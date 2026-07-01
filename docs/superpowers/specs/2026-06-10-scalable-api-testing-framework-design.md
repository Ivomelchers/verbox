# Scalable API Testing Framework Design

**Date:** 2026-06-10  
**Scope:** Centralized fixture registry + mock HTTP server for testing all broker APIs without creating accounts  
**Applies to:** Vermogenspeil platform integrations (Bitvavo, DEGIRO, Trading212, TradeRepublic, and 30+ future platforms)

---

## Executive Summary

Replace scattered mock adapters with a **centralized fixture registry + mock HTTP server** that:
- Eliminates need to create accounts for any broker (test data from docs + optional sandbox recording)
- Scales to 30+ platforms with minimal setup per new platform (~90 minutes)
- Validates all API responses against JSON schemas automatically
- Provides three test layers: schema validation → adapter parsing → integration
- Maintains backward compatibility with existing Bitvavo & DEGIRO code

---

## Problem Statement

Currently:
- ❌ No standardized way to test APIs without creating accounts
- ❌ Each platform has scattered fixtures and mock logic
- ❌ Hard to add new platforms (no clear pattern)
- ❌ No validation that fixtures match API contracts
- ❌ Manual testing required to verify adapters parse correctly

Goal: Build a system where you can add a new broker integration in ~90 minutes using only API documentation, without creating an account.

---

## Architecture

### Overview

Three-layer system:

```
┌─────────────────────────────────────────┐
│  Platform Adapter Tests                 │
│  (test_trading212.py, test_bitvavo.py)  │
├─────────────────────────────────────────┤
│  Mock HTTP Server                       │
│  (Serves fixtures as real API responses)│
├─────────────────────────────────────────┤
│  Fixture Registry                       │
│  (Discovers all platforms & fixtures)   │
├─────────────────────────────────────────┤
│  Fixture Files (Git-committed)          │
│  (metadata.yaml, schema.json, responses)│
└─────────────────────────────────────────┘
```

### Component Responsibilities

**Fixture Registry (`registry.py`)**
- Discovers all platforms in `fixtures/` directory
- Loads metadata.yaml and schema.json for each platform
- Provides API to retrieve fixtures by platform/endpoint
- Auto-validates that all fixtures are valid JSON

**Mock HTTP Server (`mock_server.py`)**
- Flask-based HTTP server simulating all platform APIs
- Dynamically registers endpoints from platform metadata
- Serves fixture responses with realistic HTTP behavior (status codes, headers, latency)
- Can run standalone (`python mock_server.py`) or as pytest fixture
- Supports query params to select specific fixtures (`?fixture=empty`, `?fixture=error_401`)

**Platform Fixtures (`fixtures/{platform}/`)**
- `metadata.yaml` — platform name, API docs URL, endpoints, auth type
- `schema.json` — JSON schema validating all endpoint responses
- `responses/` — fixture files for happy path, edge cases, and error scenarios

**Platform Adapters** (unchanged from current code)
- Inherit from `PlatformAdapter` base class
- HTTP client code in `client.py` (low-level API communication)
- Parsing logic in `adapter.py` (converts API responses to internal models)
- Tests in `tests/` directory (validate against fixtures)

---

## Fixture Organization

### Directory Structure

```
backend/apps/integrations/
├── registry.py
├── mock_server.py
├── tests/
│   ├── test_api_contract.py          # Schema validation (all platforms)
│   ├── test_adapters.py               # Integration tests with mock server
│   └── fixtures/                      # Test data for all platforms
│       ├── bitvavo/
│       │   ├── metadata.yaml
│       │   ├── schema.json
│       │   └── responses/
│       │       ├── positions_happy_path.json
│       │       ├── positions_empty.json
│       │       ├── error_401.json
│       │       └── ...
│       ├── degiro/
│       │   └── ...
│       ├── trading212/
│       │   └── ...
│       └── trade_republic/
│           └── ...
├── trading212/
│   ├── __init__.py
│   ├── adapter.py
│   ├── client.py
│   └── tests/
│       └── test_trading212.py
├── trade_republic/
│   ├── __init__.py
│   ├── adapter.py
│   ├── client.py
│   └── tests/
│       └── test_trade_republic.py
└── [existing platforms...]
```

### Metadata Schema (metadata.yaml)

```yaml
name: "Trading 212"
slug: "trading212"
api_base_url: "https://api.trading212.com/api"
sandbox_url: "https://sandbox.trading212.com/api"  # null if not available
docs_url: "https://trading212.github.io/api-docs"
auth_type: "bearer_token"  # Options: bearer_token, api_key, oauth2, hmac
endpoints:
  - name: "positions"
    method: "GET"
    path: "/accounts/{account_id}/portfolio/positions"
  - name: "transactions"
    method: "GET"
    path: "/accounts/{account_id}/history/transactions"
  - name: "balance"
    method: "GET"
    path: "/accounts/{account_id}/balance"
```

### API Response Schema (schema.json)

JSON Schema validating all endpoint responses. Example:

```json
{
  "definitions": {
    "Position": {
      "type": "object",
      "required": ["instrumentId", "quantity", "currentPrice", "currentValue"],
      "properties": {
        "instrumentId": { "type": "string" },
        "quantity": { "type": "number", "minimum": 0 },
        "currentPrice": { "type": "number", "minimum": 0 },
        "currentValue": { "type": "number" }
      }
    },
    "PositionsResponse": {
      "type": "object",
      "required": ["positions"],
      "properties": {
        "positions": {
          "type": "array",
          "items": { "$ref": "#/definitions/Position" }
        }
      }
    }
  }
}
```

### Fixture Files (responses/*.json)

Each endpoint gets multiple fixtures representing scenarios:

- `{endpoint}_happy_path.json` — Normal operation (e.g., portfolio with 5 positions)
- `{endpoint}_empty.json` — Empty state (e.g., no positions)
- `{endpoint}_single_{asset_type}.json` — Single position (e.g., single BTC)
- `{endpoint}_mixed_assets.json` — Multiple asset types
- `{endpoint}_with_dividends.json` — Includes dividend events
- `error_401.json` — Unauthorized (invalid API key)
- `error_429.json` — Rate limited
- `error_500.json` — Server error
- `error_timeout.json` — Connection timeout (empty response, status 0)

**Example fixture** (`positions_happy_path.json`):
```json
{
  "positions": [
    {
      "instrumentId": "AAPL",
      "quantity": 10,
      "currentPrice": 150.25,
      "currentValue": 1502.50
    },
    {
      "instrumentId": "BTC",
      "quantity": 0.5,
      "currentPrice": 45000,
      "currentValue": 22500
    }
  ]
}
```

---

## Testing Strategy

### Layer 1: Schema Validation (Automatic)

**File:** `backend/apps/integrations/tests/test_api_contract.py`

```python
import pytest, json
from jsonschema import validate, ValidationError
from integrations.registry import PlatformFixtureRegistry

class TestApiContract:
    """Validates all fixtures against their platform schemas."""
    
    @pytest.mark.parametrize("platform_slug", 
        list(PlatformFixtureRegistry.get_all_platforms().keys()))
    def test_all_fixtures_valid(self, platform_slug):
        """Every fixture must validate against its platform's schema."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        platform = platforms[platform_slug]
        schema = platform['schema']
        fixtures_dir = platform['fixtures_dir'] / 'responses'
        
        for fixture_file in fixtures_dir.glob("*.json"):
            with open(fixture_file) as f:
                fixture_data = json.load(f)
            
            endpoint = fixture_file.stem.split('_')[0]
            schema_def = schema['definitions'].get(f"{endpoint.title()}Response", schema)
            
            try:
                validate(instance=fixture_data, schema=schema_def)
            except ValidationError as e:
                pytest.fail(f"{fixture_file.name} failed schema validation: {e.message}")
```

**Result:** Schema validation runs on every test suite run. Catches stale/invalid fixtures early.

### Layer 2: Adapter Parsing Tests

**File:** `backend/apps/integrations/{platform}/tests/test_{platform}.py`

Tests that adapters correctly parse fixture data:

```python
import pytest
from {platform}.adapter import {Platform}PlatformAdapter

class Test{Platform}Adapter:
    
    @pytest.fixture
    def adapter(self, monkeypatch):
        """Adapter pointing to mock server."""
        monkeypatch.setenv("{PLATFORM}_API_URL", "http://localhost:5555/mock/{platform}")
        return {Platform}PlatformAdapter(api_key="mock_key")
    
    def test_fetch_positions_happy_path(self, adapter):
        positions = adapter.fetch_positions()
        assert len(positions) > 0
        assert all(p.quantity > 0 for p in positions)
    
    def test_fetch_positions_empty(self, adapter):
        positions = adapter.fetch_positions(fixture="empty")
        assert len(positions) == 0
    
    def test_fetch_transactions_with_dividends(self, adapter):
        txs = adapter.fetch_transactions(fixture="with_dividends")
        dividends = [t for t in txs if t.type == 'dividend']
        assert len(dividends) > 0
    
    def test_error_handling_401(self, adapter):
        with pytest.raises(UnauthorizedError):
            adapter.fetch_positions(fixture="error_401")
```

**Result:** Each platform adapter tested against all fixture scenarios.

### Layer 3: Integration Tests (With Mock Server)

**File:** `backend/apps/integrations/tests/test_adapters.py`

Optional tests that run with mock server for critical platforms:

```python
@pytest.fixture
def mock_api_server():
    """Start mock server for test duration."""
    server = MockApiServer(port=5555)
    import threading
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield server

def test_trading212_full_flow(mock_api_server):
    """End-to-end: adapter makes real HTTP calls to mock server."""
    adapter = Trading212PlatformAdapter(api_key="mock_key")
    positions = adapter.fetch_positions()
    assert len(positions) > 0
```

### Coverage Matrix

Generated from test run results:

```
Platform         | Schema Valid | Happy Path | Empty | Error | Transactions
─────────────────┼──────────────┼────────────┼───────┼───────┼──────────────
Bitvavo          | ✅           | ✅         | ✅    | ✅    | ✅
DEGIRO           | ✅           | ✅         | ⚠️    | ⚠️    | ✅
Trading 212      | 🔲           | 🔲         | 🔲    | 🔲    | 🔲
Trade Republic   | 🔲           | 🔲         | 🔲    | 🔲    | 🔲
```

---

## Adding a New Platform

### Workflow (90 minutes)

**Step 1: Create Fixture Folder** (5 min)
```bash
mkdir -p backend/apps/integrations/fixtures/{platform}/responses
```

**Step 2: Write metadata.yaml** (10 min)
- Read platform's API docs
- List all endpoints (positions, transactions, balance, etc.)
- Document auth type and base URLs

**Step 3: Write schema.json** (10 min)
- Define JSON structure for each endpoint response
- List required fields, types, constraints
- Can start minimal and expand as needed

**Step 4: Create Fixture Files** (20 min)
- Write 5-6 fixture JSONs (happy path, empty, errors, edge cases)
- Use docs examples or record from sandbox (if available)
- Validate against schema before committing

**Step 5: Create Adapter** (30 min)
- `adapter.py` — subclass `PlatformAdapter`, parse responses
- `client.py` — low-level HTTP communication
- Follow existing Bitvavo pattern

**Step 6: Write Tests** (15 min)
- Test each fixture scenario
- Validate error handling
- Test type conversion to internal models

**Step 7: Run Test Suite** (0 min)
```bash
pytest backend/apps/integrations/tests/test_api_contract.py
pytest backend/apps/integrations/{platform}/tests/
```

New platform automatically discovered by registry. ✅

---

## Migration Plan (Existing Platforms)

### Bitvavo
- Move existing fixtures from `backend/apps/integrations/tests/` to `fixtures/bitvavo/responses/`
- Create `metadata.yaml` and `schema.json`
- Adapter code unchanged
- Existing tests continue to work

### DEGIRO (CSV)
- Create `fixtures/degiro/` with `metadata.yaml` marking as CSV
- Move existing test CSV files to `responses/`
- Add `schema.json` for CSV column structure
- CSV import tests continue to work

**No breaking changes.** Just reorganizing existing fixtures.

---

## Implementation Details

### PlatformFixtureRegistry

```python
# backend/apps/integrations/registry.py

class PlatformFixtureRegistry:
    @staticmethod
    def get_all_platforms() -> Dict[str, dict]:
        """Returns {slug: {metadata, schema, fixtures_dir}}."""
        # Discover all platforms in fixtures/ directory
        # Load metadata.yaml and schema.json
        # Return as dict
    
    @staticmethod
    def get_fixtures_for_platform(slug: str, endpoint: str) -> List[Path]:
        """Returns list of fixture files for endpoint."""
        # Load all fixtures matching endpoint_*.json
        # Return file paths
    
    @staticmethod
    def validate_all_fixtures() -> List[ValidationError]:
        """Validate all fixtures against schemas."""
        # Iterate all platforms
        # Validate each fixture
        # Return errors (if any)
```

### MockApiServer

```python
# backend/apps/integrations/mock_server.py

class MockApiServer:
    def __init__(self, port=5555):
        self.app = Flask(__name__)
        self._register_routes()
    
    def _register_routes(self):
        # For each platform in registry:
        #   For each endpoint in metadata:
        #     Register Flask route @app.route(...)
        #     Handler loads fixture, returns JSON response
    
    def start(self):
        self.app.run(port=self.port)

@pytest.fixture
def mock_api_server():
    """Pytest fixture to start mock server for test."""
    server = MockApiServer(port=5555)
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield server
```

### Adapter Client Pattern

```python
# backend/apps/integrations/{platform}/client.py
class {Platform}Client:
    """Low-level HTTP client (no business logic)."""
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.{platform}.com"
    
    def fetch_positions(self) -> dict:
        """Raw API response (dict)."""
        response = requests.get(
            f"{self.base_url}/positions",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

# backend/apps/integrations/{platform}/adapter.py
class {Platform}PlatformAdapter(PlatformAdapter):
    """Business logic (converts API responses to internal models)."""
    def __init__(self, api_key: str, sandbox: bool = False):
        self.client = {Platform}Client(api_key, sandbox)
    
    def fetch_positions(self) -> List[Position]:
        raw = self.client.fetch_positions()
        return [self._parse_position(p) for p in raw['positions']]
    
    def _parse_position(self, raw) -> Position:
        return Position(...)
```

---

## Success Criteria

✅ Can add new platform (Trading212, TradeRepublic) in ~90 minutes  
✅ No account creation required (fixtures from docs)  
✅ All fixtures automatically validated against schemas  
✅ Tests cover happy path + empty + error scenarios  
✅ Mock server simulates realistic API behavior  
✅ Backward compatible with existing Bitvavo & DEGIRO code  
✅ Scales to 30+ platforms without friction  
✅ Team can understand and extend system in 30 minutes  

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Fixtures become stale (API changes) | Schema validation catches breaking changes; docs reviewed quarterly |
| Mock server complexity | Start simple (Flask), expand only if needed |
| Fixture maintenance burden | Standard fixture structure reduces cognitive load; registry auto-discovers |
| Platform-specific quirks | Each platform documents quirks in metadata.yaml |

---

## Timeline

- **Phase 1:** Build registry + mock server + schema validation (2-3 days)
- **Phase 2:** Migrate Bitvavo fixtures (1 day)
- **Phase 3:** Migrate DEGIRO fixtures (1 day)
- **Phase 4:** Add Trading212 (1-2 days)
- **Phase 5:** Add TradeRepublic (1-2 days)
- **Total:** ~1-2 weeks to full implementation

---

## Questions Answered

**Q: What if a platform doesn't have a sandbox?**  
A: Write fixtures from API documentation. Validate against schema before use.

**Q: What if an API requires complex authentication?**  
A: Document in metadata.yaml; mock server handles auth simulation (mocks it out).

**Q: How do we ensure fixtures stay up-to-date?**  
A: Schema validation catches drift. Reviews of metadata.yaml + schema.json quarterly.

**Q: Can we record real API responses if we get a sandbox?**  
A: Yes. Record into cassettes (VCR-style), then commit to fixtures/ directory.

**Q: How do we test error scenarios without errors?**  
A: Fixtures. Create `error_401.json`, `error_500.json`, etc. Mock server returns them on request.

---

## Appendix: Example Fixtures

### Happy Path (positions_happy_path.json)
```json
{
  "positions": [
    {"instrumentId": "AAPL", "quantity": 10, "currentPrice": 150.25, "currentValue": 1502.50},
    {"instrumentId": "BTC", "quantity": 0.5, "currentPrice": 45000, "currentValue": 22500}
  ]
}
```

### Empty (positions_empty.json)
```json
{
  "positions": []
}
```

### Error (error_401.json)
```json
{
  "error": "unauthorized",
  "message": "Invalid API key"
}
```
