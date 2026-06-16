import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.portfolio.models import AssetType
from apps.pricing.instrument_resolver import resolve_marketstack_ticker
from apps.pricing.providers.marketstack_equities import EQUITY_ASSET_TYPES, _bar_price
from apps.pricing.services.cache_keys import historical_price_cache_key
from apps.pricing.services.exchange_rates import convert_to_eur

logger = logging.getLogger(__name__)

AMSTERDAM = ZoneInfo("Europe/Amsterdam")

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

_CACHE_MISS = {"missing": True}


def _cache_is_miss(symbol: str, asset_type: str, on_date: date) -> bool:
    cached = cache.get(historical_price_cache_key(symbol, asset_type, on_date.isoformat()))
    return isinstance(cached, dict) and cached.get("missing") is True


def _cache_get(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    cached = cache.get(historical_price_cache_key(symbol, asset_type, on_date.isoformat()))
    if not cached or cached.get("missing"):
        return None
    return Decimal(str(cached["price_eur"]))


def _cache_set(symbol: str, asset_type: str, on_date: date, price: Decimal, source: str) -> None:
    from django.conf import settings

    ttl = getattr(settings, "PRICE_CACHE_TTL_HISTORICAL_SECONDS", 86400)
    cache.set(
        historical_price_cache_key(symbol, asset_type, on_date.isoformat()),
        {"price_eur": str(price), "source": source},
        timeout=ttl,
    )


def _cache_set_miss(symbol: str, asset_type: str, on_date: date) -> None:
    from django.conf import settings

    ttl = min(getattr(settings, "PRICE_CACHE_TTL_HISTORICAL_SECONDS", 86400), 3600)
    cache.set(
        historical_price_cache_key(symbol, asset_type, on_date.isoformat()),
        _CACHE_MISS,
        timeout=ttl,
    )


def fetch_historical_price_eur(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    """Historische EUR-koers op een kalenderdag (Europe/Amsterdam)."""
    symbol = symbol.upper().strip()
    today = timezone.now().date()
    if on_date > today:
        return None

    cached = _cache_get(symbol, asset_type, on_date)
    if cached is not None:
        return cached
    if _cache_is_miss(symbol, asset_type, on_date):
        return None

    price: Decimal | None = None
    source = ""

    if asset_type == AssetType.CRYPTO:
        price, source = _fetch_coingecko_history(symbol, on_date)
    elif asset_type in EQUITY_ASSET_TYPES:
        price, source = _fetch_marketstack_history(symbol, on_date)

    if price and price > 0:
        _cache_set(symbol, asset_type, on_date, price, source)
        return price

    _cache_set_miss(symbol, asset_type, on_date)
    return None


def _fetch_coingecko_history(symbol: str, on_date: date) -> tuple[Decimal | None, str]:
    coin_id = COINGECKO_IDS.get(symbol)
    if not coin_id:
        return None, ""

    date_str = on_date.strftime("%d-%m-%Y")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
    headers: dict[str, str] = {}

    key = getattr(settings, "COINGECKO_API_KEY", "") or ""
    if key:
        headers["x-cg-demo-api-key"] = key

    try:
        response = requests.get(
            url,
            params={"date": date_str, "localization": "false"},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        price_eur = payload.get("market_data", {}).get("current_price", {}).get("eur")
        if price_eur is None:
            return None, ""
        return Decimal(str(price_eur)), "coingecko"
    except Exception as exc:
        logger.debug("CoinGecko history %s %s: %s", symbol, on_date, exc)
        return None, ""


def _fetch_marketstack_bars(ms_symbols: list[str], date_from: date, date_to: date) -> list[dict]:
    """Eén Marketstack EOD-call voor meerdere symbolen over een datumbereik."""
    if not ms_symbols:
        return []

    api_key = getattr(settings, "MARKETSTACK_API_KEY", "")
    if not api_key:
        logger.debug("MARKETSTACK_API_KEY ontbreekt — historische koers overgeslagen")
        return []

    base_url = getattr(settings, "MARKETSTACK_API_URL", "https://api.marketstack.com/v2").rstrip("/")

    try:
        response = requests.get(
            f"{base_url}/eod",
            params={
                "access_key": api_key,
                "symbols": ",".join(ms_symbols),
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "limit": 1000,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.debug("Marketstack EOD-history mislukt (%s..%s): %s", date_from, date_to, exc)
        return []

    if isinstance(payload, dict) and payload.get("error"):
        logger.debug("Marketstack foutmelding: %s", payload.get("error"))
        return []

    return payload.get("data", []) if isinstance(payload, dict) else []


def _bar_price_eur(bar: dict, on_date: date) -> Decimal | None:
    price = _bar_price(bar)
    if price is None:
        return None
    currency = (bar.get("price_currency") or "EUR").upper()
    if currency == "EUR":
        return price
    return convert_to_eur(price, currency, on_date)


def _fetch_marketstack_history(symbol: str, on_date: date) -> tuple[Decimal | None, str]:
    ms_symbol = resolve_marketstack_ticker(symbol)
    bars = _fetch_marketstack_bars([ms_symbol], date_from=on_date - timedelta(days=7), date_to=on_date)
    if not bars:
        return None, ""

    matching = [b for b in bars if b.get("date", "")[:10] == on_date.isoformat()]
    bar = matching[0] if matching else max(bars, key=lambda b: b.get("date", ""))
    price = _bar_price_eur(bar, on_date)
    if price and price > 0:
        return price, "marketstack"
    return None, ""


def _marketstack_batch_for_date(symbols: list[str], on_date: date) -> dict[str, Decimal]:
    """Eén Marketstack-call voor meerdere symbolen op dezelfde datum."""
    if not symbols:
        return {}

    from apps.pricing.services.exchange_rates import get_eur_rates

    ticker_map = {symbol.upper(): resolve_marketstack_ticker(symbol) for symbol in symbols}
    ms_symbols = list(dict.fromkeys(ticker_map.values()))

    bars = _fetch_marketstack_bars(ms_symbols, date_from=on_date, date_to=on_date)
    bars_by_symbol = {bar.get("symbol"): bar for bar in bars if bar.get("date", "")[:10] == on_date.isoformat()}

    # Eén FX-call voor alle vreemde valuta op deze datum (i.p.v. één call per symbool).
    needed_currencies = {
        (bar.get("price_currency") or "EUR").upper() for bar in bars_by_symbol.values()
    }
    rates = (
        get_eur_rates(list(needed_currencies), on_date=on_date)
        if needed_currencies - {"EUR"}
        else {"EUR": Decimal("1")}
    )

    result: dict[str, Decimal] = {}
    for portfolio_symbol, ms_symbol in ticker_map.items():
        bar = bars_by_symbol.get(ms_symbol)
        if bar is None:
            continue
        price = _bar_price(bar)
        if price is None:
            continue
        currency = (bar.get("price_currency") or "EUR").upper()
        rate = rates.get(currency)
        if rate and rate > 0:
            result[portfolio_symbol] = price if currency == "EUR" else price / rate
    return result


def prefetch_dates_into_cache(
    items: list[tuple[str, str]],
    dates: list[date],
) -> None:
    """
    Download het volledige datumbereik voor alle equity-symbolen in ÉÉN Marketstack-call en
    vul de koers-cache voor elke gevraagde datum.

    Vervangt N losse per-datum fetches (elk 2-3 s) door één download.
    """
    today = timezone.now().date()
    target_dates = sorted({d for d in dates if d < today})
    if not target_dates or not items:
        return

    equity_items = [
        (sym.upper().strip(), at)
        for sym, at in items
        if at in EQUITY_ASSET_TYPES
    ]
    if not equity_items:
        return

    uncached_dates = [
        d for d in target_dates
        if any(
            _cache_get(sym, at, d) is None and not _cache_is_miss(sym, at, d)
            for sym, at in equity_items
        )
    ]
    if not uncached_dates:
        return

    symbols = list({sym for sym, _ in equity_items})
    ticker_map = {sym: resolve_marketstack_ticker(sym) for sym in symbols}
    ms_symbols = list(dict.fromkeys(ticker_map.values()))

    fetch_start = min(uncached_dates) - timedelta(days=7)
    fetch_end = max(uncached_dates)

    bars = _fetch_marketstack_bars(ms_symbols, date_from=fetch_start, date_to=fetch_end)
    if not bars:
        for sym, at in equity_items:
            for on_date in uncached_dates:
                if _cache_get(sym, at, on_date) is None and not _cache_is_miss(sym, at, on_date):
                    _cache_set_miss(sym, at, on_date)
        return

    bars_by_symbol_date: dict[tuple[str, date], dict] = {}
    for bar in bars:
        bar_date_str = (bar.get("date") or "")[:10]
        try:
            bar_date = date.fromisoformat(bar_date_str)
        except ValueError:
            continue
        bars_by_symbol_date[(bar.get("symbol"), bar_date)] = bar

    from apps.pricing.services.exchange_rates import get_eur_rates

    # Eén FX-call per datum (koers is datum-specifiek) i.p.v. één call per (symbool, datum).
    currencies_by_date: dict[date, set[str]] = defaultdict(set)
    for sym, at in equity_items:
        ms_sym = ticker_map[sym]
        for on_date in uncached_dates:
            if _cache_get(sym, at, on_date) is not None or _cache_is_miss(sym, at, on_date):
                continue
            bar = bars_by_symbol_date.get((ms_sym, on_date))
            if not bar or _bar_price(bar) is None:
                continue
            currencies_by_date[on_date].add((bar.get("price_currency") or "EUR").upper())

    rates_by_date: dict[date, dict[str, Decimal]] = {}
    for on_date, currencies in currencies_by_date.items():
        rates_by_date[on_date] = (
            get_eur_rates(list(currencies), on_date=on_date)
            if currencies - {"EUR"}
            else {"EUR": Decimal("1")}
        )

    for sym, at in equity_items:
        ms_sym = ticker_map[sym]
        for on_date in uncached_dates:
            if _cache_get(sym, at, on_date) is not None or _cache_is_miss(sym, at, on_date):
                continue
            bar = bars_by_symbol_date.get((ms_sym, on_date))
            price = None
            if bar:
                raw_price = _bar_price(bar)
                if raw_price is not None:
                    currency = (bar.get("price_currency") or "EUR").upper()
                    rate = rates_by_date.get(on_date, {}).get(currency)
                    if rate and rate > 0:
                        price = raw_price if currency == "EUR" else raw_price / rate
            if price and price > 0:
                _cache_set(sym, at, on_date, price, "marketstack")
            else:
                _cache_set_miss(sym, at, on_date)


def fetch_historical_prices(
    items: list[tuple[str, str, date]],
) -> dict[tuple[str, date], Decimal]:
    """Batch helper: (symbol, asset_type, date) -> price. Equity per datum gebundeld."""
    result: dict[tuple[str, date], Decimal] = {}
    today = timezone.now().date()

    equity_by_date: dict[date, list[str]] = defaultdict(list)
    equity_asset_type: dict[tuple[str, date], str] = {}
    other_items: list[tuple[str, str, date]] = []

    seen_equity: set[tuple[str, date]] = set()
    for symbol, asset_type, on_date in items:
        if on_date > today:
            continue
        symbol = symbol.upper().strip()
        key = (symbol, on_date)
        cached = _cache_get(symbol, asset_type, on_date)
        if cached is not None:
            result[key] = cached
            continue
        if _cache_is_miss(symbol, asset_type, on_date):
            continue

        if asset_type in EQUITY_ASSET_TYPES:
            if key not in seen_equity:
                seen_equity.add(key)
                equity_by_date[on_date].append(symbol)
                equity_asset_type[key] = asset_type
        else:
            other_items.append((symbol, asset_type, on_date))

    for on_date, symbols in equity_by_date.items():
        batch_prices = _marketstack_batch_for_date(symbols, on_date)
        for symbol in symbols:
            asset_type = equity_asset_type[(symbol, on_date)]
            price = batch_prices.get(symbol)
            if price and price > 0:
                _cache_set(symbol, asset_type, on_date, price, "marketstack")
                result[(symbol, on_date)] = price
            else:
                _cache_set_miss(symbol, asset_type, on_date)

    for symbol, asset_type, on_date in other_items:
        price = fetch_historical_price_eur(symbol, asset_type, on_date)
        if price:
            result[(symbol.upper(), on_date)] = price

    return result
