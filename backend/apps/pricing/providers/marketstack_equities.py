import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.utils import timezone

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.instrument_resolver import resolve_marketstack_ticker
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

EQUITY_ASSET_TYPES = frozenset(
    {
        AssetType.STOCK,
        AssetType.ETF,
        AssetType.FUND,
    }
)


def _bar_price(bar: dict) -> Decimal | None:
    raw = bar.get("close")
    if raw is None:
        raw = bar.get("adj_close")
    if raw is None:
        return None
    try:
        price = Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return None
    return price if price > 0 else None


class MarketstackEquitiesProvider:
    """Aandelen/ETF via Marketstack EOD-data (vervangt Yahoo Finance)."""

    asset_types = EQUITY_ASSET_TYPES

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.MARKETSTACK_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.MARKETSTACK_API_KEY
        self.timeout = timeout

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        if not symbols:
            return {}

        # Lazy import: voorkomt circulaire import (services -> price_service -> providers).
        from apps.pricing.services.exchange_rates import get_eur_rates

        if not self.api_key:
            raise PriceFetchError("MARKETSTACK_API_KEY ontbreekt")

        ticker_map = {symbol.upper(): resolve_marketstack_ticker(symbol) for symbol in symbols}
        marketstack_symbols = list(dict.fromkeys(ticker_map.values()))

        # /eod/latest geeft op het gratis plan voor sommige tickers (bv. ETF's)
        # "the_requested_data_is_not_available" terug, ook als de ticker zelf geldig is.
        # De reguliere /eod met een datumbereik werkt wel — pak de meest recente bruikbare bar.
        today = timezone.now().date()
        date_from = today - timedelta(days=10)

        url = f"{self.base_url}/eod"
        try:
            response = requests.get(
                url,
                params={
                    "access_key": self.api_key,
                    "symbols": ",".join(marketstack_symbols),
                    "date_from": date_from.isoformat(),
                    "date_to": today.isoformat(),
                    "limit": 1000,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Marketstack EOD mislukt: %s", exc)
            raise PriceFetchError("Marketstack niet beschikbaar") from exc

        if isinstance(payload, dict) and payload.get("error"):
            logger.warning("Marketstack foutmelding: %s", payload.get("error"))
            raise PriceFetchError(f"Marketstack: {payload.get('error')}")

        bars_by_symbol: dict[str, dict] = {}
        for bar in payload.get("data", []) if isinstance(payload, dict) else []:
            ms_symbol = bar.get("symbol")
            if not ms_symbol or _bar_price(bar) is None:
                continue
            existing = bars_by_symbol.get(ms_symbol)
            if existing is None or bar.get("date", "") > existing.get("date", ""):
                bars_by_symbol[ms_symbol] = bar

        # Batch alle benodigde valuta in ÉÉN exchangeratesapi-call (i.p.v. één call per
        # vreemde valuta), zodat meerdere niet-EUR koersen in dezelfde cyclus niet
        # per ongeluk de per-seconde rate-limit raken en geen quota verspillen.
        needed_currencies = {
            (bar.get("price_currency") or "EUR").upper() for bar in bars_by_symbol.values()
        }
        rates = (
            get_eur_rates(list(needed_currencies))
            if needed_currencies - {"EUR"}
            else {"EUR": Decimal("1")}
        )

        quotes: dict[str, LivePriceQuote] = {}
        for portfolio_symbol, ms_symbol in ticker_map.items():
            bar = bars_by_symbol.get(ms_symbol)
            if bar is None:
                continue

            price = _bar_price(bar)
            if price is None:
                continue

            currency = (bar.get("price_currency") or "EUR").upper()
            rate = rates.get(currency)
            if rate is None or rate <= 0:
                logger.debug(
                    "FX-conversie mislukt voor %s (%s) — koers overgeslagen", ms_symbol, currency
                )
                continue

            price_eur = price if currency == "EUR" else price / rate
            quotes[portfolio_symbol] = LivePriceQuote(
                symbol=portfolio_symbol,
                price_eur=price_eur,
                source="marketstack",
            )

        return quotes
