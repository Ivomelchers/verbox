# Quick Reference: Adding a New Symbol

## TL;DR - Add Symbol in 4 Steps

### Step 1: Add to Provider
For **crypto**, add to `backend/apps/pricing/providers/coingecko_crypto.py`:
```python
COINGECKO_COIN_IDS: dict[str, str] = {
    ...
    "DOGE": "dogecoin",  # ← ADD HERE
}
```

### Step 2: Add to Registry
In `backend/apps/pricing/symbol_registry.py`:
```python
SUPPORTED_CRYPTO_SYMBOLS = frozenset({
    ...,
    "DOGE",  # ← ADD HERE
})
```

### Step 3: Run Tests
```bash
cd backend
python manage.py test apps.pricing.tests.test_symbol_support
```

✅ **Tests must pass**

### Step 4: Done
Users can now create DOGE assets and see prices

---

## Decision Tree

```
Do you want to add symbol X?
│
├─ Is it crypto? → Bitvavo/CoinGecko
├─ Is it stock/ETF? → Yahoo Finance
└─ Something else? → Custom provider needed

Is X available on a provider?
│
├─ No → Can't add yet. Contact provider
└─ Yes → Add to provider mapping (Step 1)

Add to registry (Step 2)
│
Test passes? 
│
├─ No → You're missing provider mapping
│       Go back to Step 1
└─ Yes → Commit and celebrate ✅
```

---

## Common Scenarios

### Scenario 1: Add DOGE (Dogecoin)
1. CoinGecko has "dogecoin" ✅
2. Add to COINGECKO_COIN_IDS: `"DOGE": "dogecoin"`
3. Add to SUPPORTED_CRYPTO_SYMBOLS: `"DOGE"`
4. Tests pass ✅

### Scenario 2: Add Tesla (TSLA stock)
1. Yahoo Finance has TSLA ✅
2. Add to YahooEquitiesProvider (if not there)
3. Add to SUPPORTED_STOCK_SYMBOLS: `"TSLA"`
4. Tests pass ✅

### Scenario 3: User wants FAKECOIN that doesn't exist
1. No provider has FAKECOIN ✗
2. Can't add to registry
3. Tell user: "FAKECOIN not available on any price provider"

---

## Validation Checklist

Before committing, ask:
- [ ] Symbol is in registry
- [ ] Symbol is on a provider (verified by test)
- [ ] All tests pass
- [ ] No typos in symbol names

If any box is unchecked, don't commit.

---

## If Tests Fail

```
Error: "Crypto symbols with no provider: DOGE"
│
├─ DOGE in registry but not on provider?
│  → Remove from SUPPORTED_CRYPTO_SYMBOLS
│
├─ DOGE on provider but not in registry?
│  → Add to SUPPORTED_CRYPTO_SYMBOLS
│
└─ DOGE not on any provider?
   → Can't add yet
```

---

## Reference Files

| Need | File |
|------|------|
| Crypto mappings | `apps/pricing/providers/coingecko_crypto.py` |
| Stock mappings | `apps/pricing/providers/yahoo_equities.py` |
| Registry | `apps/pricing/symbol_registry.py` |
| Tests | `apps/pricing/tests/test_symbol_support.py` |
| Docs | `docs/development/SYMBOL_MANAGEMENT.md` |

---

## Remember

🚫 **Never**:
- Add to registry without provider support
- Ignore test failures
- Create a provider mapping without updating registry

✅ **Always**:
- Run tests after changes
- Add provider → registry (in that order)
- Check SYMBOL_MANAGEMENT.md for details
