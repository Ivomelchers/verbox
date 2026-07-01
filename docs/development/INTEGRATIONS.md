# Platformkoppelingen — fixture-first (zonder account per broker)

## Wat je al hebt

Vermogenspeil gebruikt **twee paden** naar dezelfde database (`Transaction`, `Position`):

```
                    ┌─────────────────────────┐
                    │  apply_sync_results()   │  ← gemeenschappelijke DB-laag
                    │  (apps/integrations/    │
                    │   services/sync.py)     │
                    └───────────▲─────────────┘
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
   CSV-upload                              API-sync (adapter)
          │                                           │
   parse_*() → import_*_for_user()          PlatformAdapter
   (DEGIRO)                                 (Bitvavo, demo)
```

- **Abstracte API-laag:** `PlatformAdapter` in `apps/integrations/base.py`
- **Gemeenschappelijke import:** `apply_sync_results()` schrijft posities + transacties
- **Fixtures:** `backend/fixtures/<platform>/`
- **Tests:** laden fixtures, geen live broker

Geen account nodig voor development/CI — alleen optioneel 1× een export opnemen om een fixture te maken.

---

## Mapstructuur (aanhouden voor elk nieuw platform)

```
backend/
  fixtures/
    degiro/
      sample-transactions.csv
      all-transaction-types.csv
    bitvavo/
      balance.json          # optioneel: opgenomen API-response
      trades.json
    <nieuw-platform>/
      ...
  apps/integrations/
    <platform>/
      parser.py             # CSV: raw → rijen
      classification.py   # CSV: omschrijving → TransactionType
      import_service.py     # CSV: rijen → database
      adapter.py            # API: live of mock
      client.py             # API: HTTP alleen hier
    testing/
      fixtures.py           # load_text_fixture("degiro", "x.csv")
    services/
      sync.py               # niet per platform dupliceren
    tests/
      test_<platform>_*.py
```

---

## Stap-voor-stap: nieuw CSV-platform (zoals DEGIRO)

### 1. Fixture(s)

Minimaal één CSV met **elk transactietype** dat het platform kan exporteren.

```bash
backend/fixtures/degiro/all-transaction-types.csv
```

Gebruik open-source samples alleen als **inspiratie** voor types; het bestand zelf moet **jullie** kolomformaat volgen.

### 2. Parser (puur, geen database)

```python
# apps/integrations/degiro/parser.py
def parse_degiro_csv(content: str) -> list[DegiroRow]: ...
```

### 3. Import service (database)

```python
# apps/integrations/degiro/import_service.py
def import_degiro_csv_for_user(user, file_content: str) -> dict:
    rows = parse_degiro_csv(file_content)
    # ... Transaction.objects.get_or_create ...
    _rebuild_positions_from_transactions(portfolio)
```

### 4. Tests (geen account)

```python
from apps.integrations.testing.fixtures import load_text_fixture
from apps.integrations.degiro.parser import parse_degiro_csv

def test_parse_all_types(self):
    content = load_text_fixture("degiro", "all-transaction-types.csv")
    rows = parse_degiro_csv(content)
    assert len(rows) == 9
```

```bash
python manage.py test apps.integrations.tests.test_degiro_csv --settings=config.settings.development
```

### 5. View + frontend upload

Al gekoppeld: `POST /integrations/connections/degiro/import/`

### 6. Lokaal proberen zonder UI

```bash
python manage.py import_degiro_fixture --email=jouw@email.com --file=fixtures/degiro/all-transaction-types.csv
```

### 7. Bitvavo API via fixtures (geen Bitvavo-account)

Sync gebruikt **`GET /account/history`** (alle types: buy, sell, deposit, withdrawal, staking, …).

```bash
python manage.py sync_bitvavo_fixture --email=jouw@email.com --settings=config.settings.development
```

Fixtures:

- `fixtures/bitvavo/balance.json` → `GET /balance`
- `fixtures/bitvavo/history-all-types.json` → `GET /account/history`

Tests:

```bash
python manage.py test apps.integrations.tests.test_bitvavo_history apps.integrations.tests.test_bitvavo_fixtures --settings=config.settings.development
```

---

## Stap-voor-stap: nieuw API-platform (zoals Bitvavo)

### 1. JSON-fixtures (eenmalig opnemen)

Iemand met een account exporteert **of** je kopieert voorbeeldresponses uit de API-docs naar:

```
backend/fixtures/bitvavo/balance.json
backend/fixtures/bitvavo/trades.json
```

Geen keys in git. Alleen response-body.

### 2. Client (alleen HTTP)

```python
# apps/integrations/bitvavo/client.py
class BitvavoClient:
    def get_balance(self): ...
    def get_trades(self, market): ...
```

### 3. Adapter (mapping naar TradeRecord / BalanceHolding)

```python
# apps/integrations/bitvavo/adapter.py
class BitvavoPlatformAdapter(PlatformAdapter):
    def fetch_balances(self): ...
    def fetch_transactions(self): ...
```

`sync()` erft van `PlatformAdapter` → roept `apply_sync_results` aan.

### 4. Tests — mock HTTP of adapter

**Optie A (nu):** mock adapter-methoden — snel, geen fixture nodig.

**Optie B (realistischer):** mock `requests` / client met JSON uit `fixtures/bitvavo/`.

```python
@patch("apps.integrations.bitvavo.client.BitvavoClient.get_balance")
def test_balance_from_fixture(self, mock_balance):
    import json
    from apps.integrations.testing.fixtures import fixtures_dir
    data = json.loads((fixtures_dir() / "bitvavo" / "balance.json").read_text())
    mock_balance.return_value = data
    ...
```

### 5. Productie

Alleen de **gebruiker** vult API-keys in. Jullie team test zonder account via fixtures + mocks.

### 6. Registreer adapter in sync

```python
# apps/integrations/services/sync.py → get_adapter()
adapters = {
    PlatformType.BITVAVO: BitvavoPlatformAdapter,
}
```

---

## Checklist nieuw platform

- [ ] `backend/fixtures/<platform>/` met minimaal 1 happy-path + edge cases
- [ ] Parser of adapter (platform-specifiek)
- [ ] Import/sync via `apply_sync_results` of dedicated import_service (CSV)
- [ ] `test_*` laadt fixtures met `load_text_fixture` / JSON
- [ ] CI draait tests zonder secrets
- [ ] Management command optioneel (`import_*_fixture`)
- [ ] Geen demo-knop in productie-UI

---

## Wat je níet hoeft

| Niet doen                       | Wel doen                            |
| ------------------------------- | ----------------------------------- |
| Account bij elke broker         | Fixtures + mocks                    |
| Live API in `pytest`            | JSON/CSV in `fixtures/`             |
| Ghostfolio-CSV als Bitvavo-test | Bitvavo JSON of adapter-mocks       |
| PP Java-code kopiëren           | Eigen Python-parser                 |
| Render Shell voor testdata      | `manage.py test` + fixture commands |

---

## Samenvatting in één zin

**Per platform: fixture in `backend/fixtures/` → platformcode vertaalt naar `TradeRecord`/rijen → gemeenschappelijke sync/import schrijft de DB → tests laden alleen fixtures.**

Zie ook: `test_degiro_csv.py`, `test_bitvavo.py`, `base.py`, `sync.py`.
