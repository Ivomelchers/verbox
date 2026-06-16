"""Wisselkoersen via exchangeratesapi.io — converteert vreemde valuta naar EUR."""

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_LATEST_CACHE_TTL_SECONDS = 60 * 60
_HISTORICAL_CACHE_TTL_SECONDS = 24 * 60 * 60
_MISSING = "missing"


def _cache_key(currency: str, on_date: date | None) -> str:
    suffix = on_date.isoformat() if on_date else "latest"
    return f"fxrate:eur:{currency}:{suffix}"


def get_eur_rates(currencies: list[str], on_date: date | None = None) -> dict[str, Decimal]:
    """
    Hoeveel elke valuta in `currencies` is 1 EUR waard — in ÉÉN API-call voor alle
    nog niet-gecachete valuta (voorkomt N losse requests + rate-limit 429's bij
    meerdere vreemde valuta in dezelfde refresh-cyclus).
    """
    wanted = {c.upper().strip() for c in currencies if c and c.strip()}
    result: dict[str, Decimal] = {}
    to_fetch: list[str] = []

    for currency in wanted:
        if currency == "EUR":
            result[currency] = Decimal("1")
            continue
        cached = cache.get(_cache_key(currency, on_date))
        if cached is not None:
            if cached != _MISSING:
                result[currency] = Decimal(str(cached))
            continue
        to_fetch.append(currency)

    if not to_fetch:
        return result

    api_key = getattr(settings, "EXCHANGERATESAPI_API_KEY", "")
    if not api_key:
        logger.warning("EXCHANGERATESAPI_API_KEY ontbreekt — FX-conversie overgeslagen")
        return result

    base_url = getattr(
        settings, "EXCHANGERATESAPI_API_URL", "https://api.exchangeratesapi.io/v1"
    ).rstrip("/")
    path = on_date.isoformat() if on_date else "latest"
    url = f"{base_url}/{path}"
    ttl = _HISTORICAL_CACHE_TTL_SECONDS if on_date else _LATEST_CACHE_TTL_SECONDS
    symbols_param = ",".join(sorted(to_fetch))

    try:
        response = requests.get(
            url,
            params={"access_key": api_key, "symbols": symbols_param},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Exchangeratesapi ophalen mislukt voor %s (%s): %s", symbols_param, path, exc)
        for currency in to_fetch:
            cache.set(_cache_key(currency, on_date), _MISSING, timeout=min(ttl, 3600))
        return result

    if payload.get("success") is False:
        logger.warning(
            "Exchangeratesapi foutmelding voor %s (%s): %s",
            symbols_param,
            path,
            payload.get("error"),
        )
        for currency in to_fetch:
            cache.set(_cache_key(currency, on_date), _MISSING, timeout=min(ttl, 3600))
        return result

    rates = payload.get("rates") or {}
    for currency in to_fetch:
        rate_raw = rates.get(currency)
        rate: Decimal | None = None
        if rate_raw is not None:
            try:
                candidate = Decimal(str(rate_raw))
            except (InvalidOperation, TypeError):
                candidate = None
            if candidate is not None and candidate > 0:
                rate = candidate

        if rate is None:
            cache.set(_cache_key(currency, on_date), _MISSING, timeout=min(ttl, 3600))
            continue

        cache.set(_cache_key(currency, on_date), str(rate), timeout=ttl)
        result[currency] = rate

    return result


def get_eur_rate(currency: str, on_date: date | None = None) -> Decimal | None:
    """Hoeveel `currency` is 1 EUR waard. Voor meerdere valuta tegelijk: gebruik `get_eur_rates`."""
    currency = currency.upper().strip()
    return get_eur_rates([currency], on_date=on_date).get(currency)


def convert_to_eur(amount: Decimal, currency: str, on_date: date | None = None) -> Decimal | None:
    """Converteer een bedrag in `currency` naar EUR. Geeft None als de koers niet beschikbaar is."""
    currency = currency.upper().strip()
    if currency == "EUR":
        return amount

    rate = get_eur_rate(currency, on_date)
    if rate is None:
        return None
    return amount / rate
