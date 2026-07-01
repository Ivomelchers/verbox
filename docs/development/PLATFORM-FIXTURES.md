# Platform CSV-fixtures en vertrouwde import

## Doel

Nieuwe brokers toevoegen **zonder eigen account**, met tests die garanderen dat:

1. Het bestand bij het juiste platform hoort (header-fingerprint).
2. Herkende transacties worden geïmporteerd.
3. Niet-herkende regels **zichtbaar** blijven in het importrapport (geen stille drops).

## Mapstructuur

```
backend/fixtures/<platform>/
  sample-transactions.csv       # happy path
  all-transaction-types.csv     # elk TransactionType
  partial-with-unknown-row.csv  # transparantie-test
  real-anonymized-*.csv         # optioneel: echte bètatester-export

backend/apps/integrations/<platform>/
  fingerprint.py                # header-score
  parser.py                     # → CsvParseResult
  classification.py
  import_service.py

backend/apps/integrations/csv/
  registry.py                   # registreer nieuwe parser hier
  detection.py
  import_service.py
```

## Open-source samples (Portfolio Performance / Ghostfolio)

1. Zoek extractor + testbestand in `datatransfer/` (PP) of Ghostfolio fixtures.
2. **Logica nabouwen in Python** — geen Java-code kopiëren (GPL).
3. Voeg fixtures toe en unit tests.
4. Voeg vóór productie minstens **één echte export** toe (geanonimiseerd).

PP DEGIRO-samples zijn vaak `.txt` (PDF-extract); voor CSV gebruik onze fixtures of een echte Transactions-export.

## Nieuwe platform toevoegen

1. `fingerprint.py` — `REQUIRED` + `SIGNATURE` headers, `score >= 0.85`.
2. `parser.py` — retourneer `CsvParseResult(rows=..., skipped=[...])`.
3. `import_service.py` — accepteer `parse_result` optioneel.
4. Registreer in `csv/registry.py` (`_build_registry`).
5. Tests: detectie, alle types, partial unknown, API `csv/import/`.

## API

| Endpoint                           | Doel                             |
| ---------------------------------- | -------------------------------- |
| `GET /integrations/csv/platforms/` | Lijst CSV-platformen             |
| `POST /integrations/csv/detect/`   | Herken platform uit headers      |
| `POST /integrations/csv/preview/`  | Dry-run + nieuw/dubbel/problemen |
| `POST /integrations/csv/import/`   | `file` + optioneel `platform`    |

Importresponse bevat o.a. `trust_summary`, `has_import_gaps`, `skipped_rows`, `unknown_descriptions`.

## Kolomschema & drift

- Per platform: `column_schema.py` met canonical velden + aliases (bron van waarheid).
- **Normale pad:** parser + aliases; geen AI, geen kosten.
- **Fallback:** als parse/detectie faalt → `resolve_column_mapping` (fuzzy ≥0,88, daarna optioneel OpenAI op **alleen** headers + 3 voorbeeldrijen).
- Preview/import bevat `column_mapping`: `source` (`schema` | `fuzzy` | `ai`), `maintenance_snippets` (tekst om aliases in `column_schema.py` toe te voegen).
- Env: `CSV_AI_COLUMN_MAPPING=true` + `OPENAI_API_KEY` (productie alleen als fallback gewenst).
- Fixture `fixtures/degiro/drifted-column-headers.csv` + `test_column_resolution.py` (gemockte AI).
- Preview toont `column_schema.schema_warnings` en `suggested_aliases` (fuzzy-suggesties, niet auto bij lage confidence).
- Elke preview/import schrijft `CsvImportDiagnostic` (alleen headers + onbekende omschrijvingen).
- Onderhoud: `python manage.py report_csv_drift --days=30`
- Django admin: Integrations → CSV-import diagnostiek

## Koers-API (gratis stack — standaard in code)

| Asset                           | Provider (volgorde)                               | Key nodig?                                  |
| ------------------------------- | ------------------------------------------------- | ------------------------------------------- |
| **Crypto live**                 | Bitvavo publiek ticker → CoinGecko `simple/price` | Optioneel `COINGECKO_API_KEY` (gratis Demo) |
| **ETF / aandelen / fonds live** | Yahoo (`yfinance`, o.a. `.AS` tickers)            | Nee                                         |
| **Crypto historisch** (1 jan)   | CoinGecko history                                 | Optioneel Demo-key                          |
| **ETF historisch**              | Yahoo history                                     | Nee                                         |

- **Cache live:** 5 min (`PRICE_CACHE_TTL_LIVE_SECONDS`, default 300)
- **Achtergrond:** Celery `refresh_live_prices` elke 5 min + `python manage.py refresh_live_prices`
- Lokaal zonder Celery beat: handmatig `refresh_live_prices` of dashboard triggert cache-miss

**ISIN → Yahoo** (alle CSV-platformen): `InstrumentMapping` + seed JSON + OpenFIGI. Zie `docs/architecture/PRICING-AND-INSTRUMENTS.md`.

Na import: `python manage.py backfill_transaction_prices --user-email=...`

**Verwacht na `all-transaction-types.csv` (6 stuks IWDA, live ~€123,88):** kostprijs portefeuille **€532,50**, historische aankopen **€710**, waarde **~€743**, onrealiseerde winst **~€211** (niet €708/€35 — dat was Value-kolom + oude rendement-formule).

## Acceptatie

- [ ] Fixture-dekking alle transactietypes
- [ ] Eén echte export per platform
- [ ] Bètatester: totalen vs broker-app
- [ ] Geen import zonder rapport bij gedeeltelijke gaps
