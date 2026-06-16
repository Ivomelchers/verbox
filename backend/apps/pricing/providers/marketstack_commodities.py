"""
Edelmetalen (Box3 VermogensCategorie.EDELMETAAL) via Marketstack Commodities-API.

ONGETEST tegen echte data: het gratis Marketstack-plan blokkeert deze endpoint
volledig (`function_access_restricted` — bevestigd 16 jun 2026 met 1 live call),
dus de exacte response-vorm kon niet live geverifieerd worden. De parsing hieronder
is gebaseerd op de officiële Swagger-schema's (`CommodityResponse`,
`CommodityResponse_data`) uit de Marketstack-docs, niet op een echte response.

Verifieer opnieuw zodra het Marketstack-abonnement geüpgraded is — pas zo nodig
`_price_from_payload` / het symbol-veld aan op de werkelijke velden.
"""

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

COMMODITY_ASSET_TYPES = frozenset({AssetType.METAL})

# Marketstack commodity-symbolen voor edelmetalen (ISO 4217-edelmetaalcodes).
# Portfolio-symbolen als "GOLD"/"SILVER" worden hierop gemapt; onbekende symbolen
# gaan ongewijzigd door (voor als de gebruiker al de Marketstack-code invoert).
METAL_COMMODITY_SYMBOLS: dict[str, str] = {
    "GOLD": "XAU",
    "SILVER": "XAG",
    "PLATINUM": "XPT",
    "PALLADIUM": "XPD",
}


def _price_from_payload(entry: dict) -> Decimal | None:
    for key in ("price", "close", "value", "rate"):
        raw = entry.get(key)
        if raw is None:
            continue
        try:
            price = Decimal(str(raw))
        except (InvalidOperation, TypeError):
            continue
        if price > 0:
            return price
    return None


class MarketstackCommodityProvider:
    """Edelmetalen via Marketstack Commodities-API (vereist betaald plan)."""

    asset_types = COMMODITY_ASSET_TYPES

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.MARKETSTACK_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.MARKETSTACK_API_KEY
        self.timeout = timeout

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        if not symbols:
            return {}

        if not self.api_key:
            raise PriceFetchError("MARKETSTACK_API_KEY ontbreekt")

        symbol_map = {
            symbol.upper(): METAL_COMMODITY_SYMBOLS.get(symbol.upper(), symbol.upper())
            for symbol in symbols
        }
        commodity_symbols = list(dict.fromkeys(symbol_map.values()))

        url = f"{self.base_url}/commodities"
        try:
            response = requests.get(
                url,
                params={
                    "access_key": self.api_key,
                    "symbols": ",".join(commodity_symbols),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Marketstack commodities mislukt: %s", exc)
            raise PriceFetchError("Marketstack commodities niet beschikbaar") from exc

        if isinstance(payload, dict) and payload.get("error"):
            logger.warning("Marketstack commodities foutmelding: %s", payload.get("error"))
            raise PriceFetchError(f"Marketstack: {payload.get('error')}")

        entries_by_symbol: dict[str, dict] = {}
        data = payload.get("data") if isinstance(payload, dict) else None
        for entry in data or []:
            if not isinstance(entry, dict):
                continue
            entry_symbol = (entry.get("symbol") or entry.get("name") or "").upper()
            if entry_symbol:
                entries_by_symbol[entry_symbol] = entry

        # Eén FX-call voor alle benodigde valuta in deze batch (zelfde patroon als
        # MarketstackEquitiesProvider) i.p.v. één call per commodity.
        from apps.pricing.services.exchange_rates import get_eur_rates

        needed_currencies = {
            (entry.get("currency") or entry.get("price_currency") or "USD").upper()
            for entry in entries_by_symbol.values()
        }
        rates = (
            get_eur_rates(list(needed_currencies))
            if needed_currencies - {"EUR"}
            else {"EUR": Decimal("1")}
        )

        quotes: dict[str, LivePriceQuote] = {}
        for portfolio_symbol, commodity_symbol in symbol_map.items():
            entry = entries_by_symbol.get(commodity_symbol)
            if entry is None:
                continue

            price = _price_from_payload(entry)
            if price is None:
                continue

            currency = (entry.get("currency") or entry.get("price_currency") or "USD").upper()
            rate = rates.get(currency)
            if rate is None or rate <= 0:
                logger.debug(
                    "FX-conversie mislukt voor commodity %s (%s) — koers overgeslagen",
                    commodity_symbol,
                    currency,
                )
                continue

            price_eur = price if currency == "EUR" else price / rate
            quotes[portfolio_symbol] = LivePriceQuote(
                symbol=portfolio_symbol,
                price_eur=price_eur,
                source="marketstack",
            )

        return quotes
