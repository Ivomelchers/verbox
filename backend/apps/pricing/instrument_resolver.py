"""
Symbol/ISIN → Yahoo Finance ticker (platform-onafhankelijk).

Laag 1: korte tickers (aliases)
Laag 2: database InstrumentMapping
Laag 3: seed JSON (curated Euronext .AS — wint vóór OpenFIGI-fouten zoals VUAA.L)
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from apps.pricing.isin import looks_like_isin
from apps.pricing.mic_suffix import mic_from_yahoo_suffix
from apps.pricing.models import MappingSource

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "euronext_isin_tickers.json"

SYMBOL_ALIASES: dict[str, str] = {
    "IWDA": "IWDA.AS",
    "IWDA.L": "IWDA.AS",
    "ASML": "ASML.AS",
    "SHELL": "SHELL.AS",
    "INGA": "INGA.AS",
    "VWCE": "VWCE.AS",
    "VUSA": "VUSA.AS",
    "VUAA": "VUAA.AS",
    "VUAA.L": "VUAA.AS",
}


@lru_cache(maxsize=1)
def _seed_map() -> dict[str, str]:
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Seed ISIN-map niet geladen: %s", exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).upper(): str(v) for k, v in raw.items()}


def _db_mapping(isin: str):
    from apps.pricing.models import InstrumentMapping

    return InstrumentMapping.objects.filter(isin=isin.upper()).first()


def _effective_ticker_for_isin(isin: str) -> str | None:
    """DB-ticker, tenzij seed een betere Euronext-ticker heeft dan OpenFIGI."""
    upper = isin.upper()
    row = _db_mapping(upper)
    seed = _seed_map().get(upper)
    if not row:
        return seed
    if seed and row.source == MappingSource.OPENFIGI and row.yahoo_ticker != seed:
        return seed
    return row.yahoo_ticker


def resolve_yahoo_ticker(symbol: str) -> str:
    upper = symbol.upper().strip()
    if upper in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[upper]
    if looks_like_isin(upper):
        ticker = _effective_ticker_for_isin(upper)
        return ticker if ticker else upper
    return upper


def _yahoo_ticker_to_marketstack(ticker: str, mic: str = "") -> str:
    """Marketstack gebruikt <SYMBOL>.<MIC> (bv. ASML.XAMS) i.p.v. Yahoo's afkorting (ASML.AS)."""
    base = ticker.upper().strip()
    if mic:
        return f"{base.split('.')[0]}.{mic.upper()}"
    if "." in base:
        symbol_part, suffix = base.split(".", 1)
        resolved_mic = mic_from_yahoo_suffix(f".{suffix}")
        if resolved_mic:
            return f"{symbol_part}.{resolved_mic}"
        return base
    return base


def resolve_marketstack_ticker(symbol: str) -> str:
    upper = symbol.upper().strip()
    if looks_like_isin(upper):
        ticker = _effective_ticker_for_isin(upper)
        if not ticker:
            return upper
        row = _db_mapping(upper)
        mic = row.mic if row else ""
        return _yahoo_ticker_to_marketstack(ticker, mic)
    if upper in SYMBOL_ALIASES:
        return _yahoo_ticker_to_marketstack(SYMBOL_ALIASES[upper])
    return upper


def list_unmapped_isins(symbols: list[str]) -> list[str]:
    from apps.pricing.services.instrument_service import list_unmapped_isins as _list

    return _list(symbols)
