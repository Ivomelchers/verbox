# Test fixtures (geen echte gebruikersdata)

Statische bestanden voor parser- en API-tests. **Nooit** API-keys of echte accountexports committen.

## Structuur

| Map           | Formaat                                         | Gebruik                                         |
| ------------- | ----------------------------------------------- | ----------------------------------------------- |
| `degiro/`     | CSV (DEGIRO Transactions-export)                | `parse_degiro_csv`, `import_degiro_fixture`     |
| `bitvavo/`    | JSON (`balance.json`, `history-all-types.json`) | `GET /account/history` — `sync_bitvavo_fixture` |
| `ghostfolio/` | CSV (Ghostfolio-formaat)                        | Alleen referentie, geen productie-import        |

## Laden in tests

```python
from apps.integrations.testing.fixtures import load_text_fixture

content = load_text_fixture("degiro", "all-transaction-types.csv")
```

## Nieuw platform

1. Map aanmaken: `fixtures/<platform>/`
2. Minimaal één bestand per transactietype (of één gecombineerd bestand)
3. Test + parser/adapter toevoegen — zie `docs/development/INTEGRATIONS.md`
