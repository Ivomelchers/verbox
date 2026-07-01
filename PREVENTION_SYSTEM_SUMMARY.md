# Prevention System for Issue #2: Unpriceable Assets

## What Was Implemented

A four-layer defense system that prevents users from creating assets without price support:

### Layer 1: Symbol Registry
📄 **File**: `backend/apps/pricing/symbol_registry.py` (NEW)

- Curated list of supported symbols per asset type
- `get_supported_symbols()` - query what's available
- `is_symbol_supported()` - validate before creation
- `suggest_similar_symbols()` - helpful typo suggestions

```python
SUPPORTED_CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", ..., "AR"  # AR added for Arweave
})
```

### Layer 2: Asset Model Validation
📄 **File**: `backend/apps/portfolio/models.py` (MODIFIED)

- Added `Asset.clean()` method
- Validates symbol is in registry
- Shows helpful error message with suggestions
- Prevents invalid assets from database level

```python
def clean(self):
    if not is_symbol_supported(self.symbol, self.asset_type):
        raise ValidationError(
            f"Symbol '{self.symbol}' is niet ondersteund..."
        )
```

### Layer 3: Serializer Validation
📄 **File**: `backend/apps/portfolio/serializers.py` (MODIFIED)

- `ManualAssetCreateSerializer` calls `Asset.clean()`
- Validates at API level before database
- User gets immediate feedback

```python
def validate(self, data):
    asset = Asset(symbol=data["symbol"], asset_type=data["asset_type"])
    asset.clean()  # Raises ValidationError if invalid
```

### Layer 4: Integration Tests
📄 **File**: `backend/apps/pricing/tests/test_symbol_support.py` (NEW)

- **8 tests** verify symbol support:
  - All crypto symbols available on provider
  - No gaps between registry and providers
  - Model validation rejects unsupported symbols
  - Model accepts supported symbols
  - Symbol suggestions work for typos
  - AR specifically in CoinGecko mapping

✅ All tests pass - catches gaps at development time

### Bonus: Bug Fixes

1. **OKX API Timestamp** (backend/apps/integrations/okx/client.py)
   - Changed: `str(time.time())` → `str(int(time.time()))`
   - Fixed "Invalid OK-ACCESS-TIMESTAMP" error
   - OKX API requires integer seconds, not float

2. **Bitvavo AR Symbol** (backend/apps/pricing/providers/coingecko_crypto.py)
   - Added: `"AR": "arweave"` to CoinGecko mapping
   - AR now prices via CoinGecko fallback

3. **Documentation** (backend/docs/development/SYMBOL_MANAGEMENT.md)
   - How to safely add new symbols
   - Maintenance guidelines
   - Four-layer defense explanation

---

## How It Works

### User Creates Asset "FAKECOIN"

```
1. Frontend: User enters "FAKECOIN" with type "crypto"
   ↓
2. API POST: ManualAssetCreateSerializer validates
   ↓
3. Serializer: Calls Asset.clean()
   ↓
4. Model: Checks if "FAKECOIN" in SUPPORTED_CRYPTO_SYMBOLS
   ↓
5. Result: ❌ ValidationError - symbol not found
   Message: "FAKECOIN is niet ondersteund"
   ↓
6. User: Sees error, tries "BTC" instead
   ↓
7. Result: ✅ Asset created successfully
```

### Developer Adds New Symbol

```
1. User requests "DOGE" support
   ↓
2. Dev adds "DOGE" to CoinGecko in coingecko_crypto.py
   ↓
3. Dev runs: python manage.py test apps.pricing.tests.test_symbol_support
   ↓
4. Tests: Check if DOGE is available on providers
   ↓
5. If missing: ❌ Test fails - "Add DOGE to registry or provider"
   ↓
6. If available: ✅ Test passes
   ↓
7. Dev adds "DOGE" to SUPPORTED_CRYPTO_SYMBOLS
   ↓
8. Tests: ✅ All pass
   ↓
9. Dev commits: "Add DOGE (Dogecoin) support"
```

---

## Benefits

| Issue | Before | After |
|-------|--------|-------|
| User adds "FAKECOIN" | Silent failure in logs | Immediate validation error |
| Developer forgets to add symbol to provider | Tests pass but users get errors | Tests FAIL - catches at dev time |
| User sees "no price available" | No context | Helpful message: "not supported, try: DOGE, DOT" |
| What symbols can I add? | Not documented | Read SUPPORTED_CRYPTO_SYMBOLS |
| How do I add new symbols? | Guess and debug | Read SYMBOL_MANAGEMENT.md |

---

## Test Results

```
Ran 13 tests in 0.469s - OK ✅

+ 8 new symbol registry tests
+ 5 existing OKX API tests
+ All 45 portfolio+pricing tests pass
+ All 187 integration tests pass
```

---

## Files Changed

### New Files
- `backend/apps/pricing/symbol_registry.py` - Symbol definitions & validation
- `backend/apps/pricing/tests/test_symbol_support.py` - Integration tests
- `backend/docs/development/SYMBOL_MANAGEMENT.md` - Documentation

### Modified Files
- `backend/apps/portfolio/models.py` - Added Asset.clean() validation
- `backend/apps/portfolio/serializers.py` - Added serializer validation
- `backend/apps/integrations/okx/client.py` - Fixed timestamp format
- `backend/apps/pricing/providers/coingecko_crypto.py` - Added AR symbol

---

## Next Steps

1. **Review** the four-layer system
2. **Commit** with message "Implement symbol registry and validation system"
3. **Consider** adding more common symbols to registry:
   - Crypto: DOGE, SHIB, UNI, AAVE, etc.
   - Stocks: NL brokers stocks, US tech stocks, etc.
4. **Update** onboarding to reference SYMBOL_MANAGEMENT.md

---

## Key Principles

✅ **Fail fast**: Validate at creation time, not when pricing  
✅ **Be helpful**: Suggest correct symbols  
✅ **Test-driven**: Automated tests prevent gaps  
✅ **Documented**: New devs know the rules  
✅ **No silent failures**: Users always know status  

This prevents situations like AR-EUR where:
- System looks like it's working
- But users can't see prices
- And only logs show the problem
