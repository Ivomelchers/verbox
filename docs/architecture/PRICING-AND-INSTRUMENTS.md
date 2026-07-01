# Koersen en instrumenten (ISIN)

## Probleem

CSV-imports slaan **ISIN** op als symbool (correct). Yahoo Finance verwacht **tickers** (`IWDA.AS`). Zonder vertaling: geen live koers → dashboard/YTD onbetrouwbaar.

Dit geldt voor **elke broker** (DEGIRO, later Saxo, …), niet alleen één platform.

## Flow

```
CSV-import → transacties (ISIN in portfolio)
       ↓
InstrumentMapping (DB) + seed JSON + OpenFIGI (nieuwe ISIN)
       ↓
resolve_yahoo_ticker → Yahoo / Bitvavo / CoinGecko
```

## Wat is OpenFIGI?

Gratis lookup: **ISIN → ticker + beurs**. Geen prijzen, geen user-data. Eén call per nieuwe ISIN, daarna cache in `InstrumentMapping` voor alle gebruikers.

Uitzetten: `OPENFIGI_ENABLED=false` → alleen seed JSON + handmatig in Django admin.

**Let op:** OpenFIGI kan een **verkeerde beurs** kiezen (bv. `VUAA.L` i.p.v. `VUAA.AS` voor DEGIRO). ISIN's in `euronext_isin_tickers.json` winnen bij koersen; `sync_instrument_seed` zet de DB ook goed.

## Commando's

- `python manage.py migrate` — tabel + seed
- `python manage.py resolve_instruments` — ontbrekende ISIN's
- `python manage.py report_unmapped_isins --email=...`

## Na import

Import-API bevat `instrument_resolve` (resolved/failed). Bij failures: admin of `resolve_instruments`.
