# Symbol Management & Price Provider Integration

## Overview

This document explains how to safely add new asset symbols to Vermogenspeil without causing "unpriceable asset" errors.

## The Problem We Prevent

Before this system, users could add assets like "AR" (Arweave) to their portfolio, but:
- Bitvavo didn't list "AR-EUR" as a market
- CoinGecko didn't have "AR" in the mapping
- The system would fail silently with log warnings
- Users couldn't see prices for their assets

## The Solution: Three Layers of Defense

### Layer 1: Symbol Registry (`apps/pricing/symbol_registry.py`)

Curated list of symbols that CAN be priced:

```python
SUPPORTED_CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", ..., "AR"  # Only add if Layer 2 supports it
})
```

**Key rule:** If you add a symbol here, it MUST be available on at least one price provider.

### Layer 2: Provider Mappings

Each provider maintains its own symbol list:

- **Bitvavo** (`apps/integrations/bitvavo/`): Market pairs like `BTC-EUR`, `AR-EUR`
- **CoinGecko** (`apps/pricing/providers/coingecko_crypto.py`): Coin IDs like `"BTC": "bitcoin"`, `"AR": "arweave"`
- **Yahoo Finance** (`apps/pricing/providers/yahoo_equities.py`): Stock tickers like `AAPL`, `MSFT`

### Layer 3: Model Validation (`apps/portfolio/models.py`)

Asset model validates symbols at creation time:

```python
asset = Asset(symbol="FAKECOIN", asset_type=AssetType.CRYPTO)
asset.clean()  # Raises ValidationError if not in registry
```

### Layer 4: Integration Tests (`apps/pricing/tests/test_symbol_support.py`)

Tests verify:
1. ✅ All symbols in registry are available on providers
2. ✅ No gaps in provider support
3. ✅ Model validation rejects unsupported symbols

**These tests FAIL if you break the rules.**

---

## How to Add a New Symbol

### Step 1: Add to Provider

**For crypto** (example: add `SOL`):

1. **Bitvavo**: Manually verify `SOL-EUR` is tradeable at https://bitvavo.com
2. **CoinGecko**: Add to `coingecko_crypto.py`:
   ```python
   COINGECKO_COIN_IDS: dict[str, str] = {
       ...
       "SOL": "solana",  # Add this line
   }
   ```

**For stocks/ETFs**:
- Add to `yahoo_equities.py` if Yahoo Finance has it

### Step 2: Add to Registry

Add to `symbol_registry.py`:

```python
SUPPORTED_CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", ...,
    "SOL",  # Add this
})
```

### Step 3: Run Tests

```bash
python manage.py test apps.pricing.tests.test_symbol_support
```

**These tests must pass.** If they fail, go back to Step 1.

### Step 4: Done

Symbol is now:
- ✅ In the registry
- ✅ Available on a provider
- ✅ Validated by tests
- ✅ Protected by model validation

---

## What Happens When User Creates Asset

1. **Frontend**: User enters symbol "SOL"
2. **API**: `ManualAssetCreateSerializer` validates via `Asset.clean()`
3. **Model**: Checks if "SOL" is in `SUPPORTED_CRYPTO_SYMBOLS`
4. **If not found**:
   - Shows error: `"'SOL' is niet ondersteund. Bedoelde u: SOL?"`
   - Suggests similar symbols if available
   - Asset is NOT created
5. **If found**: Asset is created successfully

---

## Troubleshooting

### "Symbol X is in registry but test fails"

Means the provider doesn't actually have it. Either:
1. Remove from registry, or
2. Add to provider mapping

**Do not ignore test failures.**

### "User can't add a valid symbol"

Check:
1. Is it in `SUPPORTED_*_SYMBOLS`?
2. Is it on a provider?
3. Did you update the registry?

### "Provider added new symbols but tests pass"

Good! The safety layer is working. But consider:
- Should we add these to the registry?
- Do we want to offer them to users?

---

## Maintenance Cadence

- **Monthly**: Check if providers added symbols we should support
- **Quarterly**: Review test coverage of providers
- **On request**: Add symbols when users request them

---

## Example: Adding AR (Arweave)

### What was done:

1. ✅ CoinGecko already had `"AR": "arweave"`
2. ✅ Added `"AR"` to `SUPPORTED_CRYPTO_SYMBOLS`
3. ✅ Tests pass
4. ✅ Users can now create AR assets

### What would have failed:

If CoinGecko didn't have `"arweave"`:
- Add `"AR": "arweave"` to `COINGECKO_COIN_IDS`
- Tests pass
- Then add to registry

---

## Key Principles

1. **Registry is source of truth**: What's here is what users can have
2. **Providers are workers**: They do the actual pricing
3. **Tests are guards**: They prevent gaps between registry and providers
4. **Model is bouncer**: It stops invalid assets at the gate

**Never:** Add to registry without provider support
**Never:** Ignore test failures
**Always:** Run tests after changes
