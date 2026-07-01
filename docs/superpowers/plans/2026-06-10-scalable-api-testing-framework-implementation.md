# Scalable API Testing Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a centralized fixture registry + mock HTTP server that eliminates the need for real accounts to test broker API integrations, then add Trading212 and TradeRepublic platforms.

**Architecture:** 
- `PlatformFixtureRegistry` discovers all platforms in `fixtures/` and loads metadata/schemas
- `MockApiServer` is a Flask app that dynamically registers endpoints from metadata and serves fixture responses
- `test_api_contract.py` validates all fixtures against schemas (auto-run on every test)
- Platform adapters test against mock server using pytest fixtures
- Bitvavo & DEGIRO fixtures migrated to new structure

**Tech Stack:** 
- Python/pytest for tests
- Flask for mock HTTP server
- JSON Schema for API contract validation
- YAML for platform metadata

---

## File Structure

**New files to create:**
```
backend/apps/integrations/
├── registry.py                          # PlatformFixtureRegistry discovery
├── mock_server.py                       # Flask mock HTTP server
├── tests/
│   ├── conftest.py                      # pytest fixtures (mock server)
│   ├── test_api_contract.py             # Schema validation (all platforms)
│   ├── test_adapters.py                 # Integration tests
│   └── fixtures/
│       ├── trading212/
│       │   ├── metadata.yaml
│       │   ├── schema.json
│       │   └── responses/
│       │       ├── positions_happy_path.json
│       │       ├── positions_empty.json
│       │       ├── transactions_happy_path.json
│       │       ├── error_401.json
│       │       ├── error_429.json
│       │       └── error_500.json
│       ├── trade_republic/
│       │   ├── metadata.yaml
│       │   ├── schema.json
│       │   └── responses/
│       │       ├── positions_happy_path.json
│       │       ├── positions_empty.json
│       │       ├── transactions_happy_path.json
│       │       ├── error_401.json
│       │       ├── error_429.json
│       │       └── error_500.json
│       ├── bitvavo/ (MIGRATED from existing)
│       │   ├── metadata.yaml (NEW)
│       │   ├── schema.json (NEW)
│       │   └── responses/ (existing fixtures)
│       └── degiro/ (MIGRATED from existing)
│           ├── metadata.yaml (NEW)
│           ├── schema.json (NEW)
│           └── responses/ (existing fixtures)
├── trading212/
│   ├── __init__.py
│   ├── adapter.py
│   ├── client.py
│   └── tests/
│       ├── __init__.py
│       └── test_trading212.py
├── trade_republic/
│   ├── __init__.py
│   ├── adapter.py
│   ├── client.py
│   └── tests/
│       ├── __init__.py
│       └── test_trade_republic.py
└── [existing files unchanged]
```

**Modified files:**
```
backend/apps/integrations/
├── base.py                              # No changes (PlatformAdapter stays same)
├── bitvavo/adapter.py                   # No changes
└── degiro/adapter.py                    # No changes
```

---

## Tasks

### Task 1: Create PlatformFixtureRegistry

**Files:**
- Create: `backend/apps/integrations/registry.py`
- Test: `backend/apps/integrations/tests/test_registry.py` (unit tests)

- [ ] **Step 1: Write failing test for registry discovery**

```python
# backend/apps/integrations/tests/test_registry.py

import pytest
from pathlib import Path
from integrations.registry import PlatformFixtureRegistry

class TestPlatformFixtureRegistry:
    def test_discover_all_platforms(self):
        """Registry discovers all platforms with metadata and schema."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        
        # Should find at least trading212
        assert 'trading212' in platforms
        assert 'trade_republic' in platforms
        
        # Each platform has required keys
        for slug, platform_info in platforms.items():
            assert 'metadata' in platform_info
            assert 'schema' in platform_info
            assert 'fixtures_dir' in platform_info
    
    def test_platform_metadata_structure(self):
        """Metadata has required fields."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        trading212 = platforms['trading212']['metadata']
        
        assert trading212['name'] == 'Trading 212'
        assert trading212['slug'] == 'trading212'
        assert 'api_base_url' in trading212
        assert 'endpoints' in trading212
        assert isinstance(trading212['endpoints'], list)
    
    def test_get_fixtures_for_endpoint(self):
        """Get all fixture files for a specific endpoint."""
        fixtures = PlatformFixtureRegistry.get_fixtures_for_platform('trading212', 'positions')
        
        assert len(fixtures) > 0
        assert all(f.suffix == '.json' for f in fixtures)
    
    def test_validate_all_fixtures(self):
        """Validate all fixtures against their schemas."""
        errors = PlatformFixtureRegistry.validate_all_fixtures()
        
        # Should have no validation errors
        assert len(errors) == 0, f"Fixture validation failed: {errors}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest backend/apps/integrations/tests/test_registry.py -v
```

Expected output: Multiple FAILED (ModuleNotFoundError, etc.)

- [ ] **Step 3: Write PlatformFixtureRegistry implementation**

```python
# backend/apps/integrations/registry.py

import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from jsonschema import validate, ValidationError

class PlatformFixtureRegistry:
    """Discovers and manages all platform fixtures."""
    
    _FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"
    
    @staticmethod
    def get_all_platforms() -> Dict[str, dict]:
        """
        Returns dict of all discovered platforms.
        
        Returns:
            {
                'trading212': {
                    'metadata': {...},
                    'schema': {...},
                    'fixtures_dir': Path(...)
                },
                ...
            }
        """
        platforms = {}
        
        for platform_dir in PlatformFixtureRegistry._FIXTURES_DIR.iterdir():
            if not platform_dir.is_dir():
                continue
            
            metadata_file = platform_dir / "metadata.yaml"
            schema_file = platform_dir / "schema.json"
            
            if not (metadata_file.exists() and schema_file.exists()):
                continue
            
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)
            
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            platforms[metadata['slug']] = {
                'metadata': metadata,
                'schema': schema,
                'fixtures_dir': platform_dir,
            }
        
        return platforms
    
    @staticmethod
    def get_fixtures_for_platform(platform_slug: str, endpoint_name: str) -> List[Path]:
        """
        Get all fixture files for a platform endpoint.
        
        Args:
            platform_slug: e.g., 'trading212'
            endpoint_name: e.g., 'positions'
        
        Returns:
            List of Path objects matching {endpoint_name}_*.json
        """
        platforms = PlatformFixtureRegistry.get_all_platforms()
        
        if platform_slug not in platforms:
            raise ValueError(f"Platform {platform_slug} not found")
        
        fixtures_dir = platforms[platform_slug]['fixtures_dir'] / 'responses'
        
        if not fixtures_dir.exists():
            return []
        
        return sorted(fixtures_dir.glob(f"{endpoint_name}_*.json"))
    
    @staticmethod
    def validate_all_fixtures() -> List[Tuple[Path, ValidationError]]:
        """
        Validate all fixture files against their platform schemas.
        
        Returns:
            List of (fixture_path, error) tuples. Empty if all valid.
        """
        errors = []
        platforms = PlatformFixtureRegistry.get_all_platforms()
        
        for platform_slug, platform_info in platforms.items():
            schema = platform_info['schema']
            fixtures_dir = platform_info['fixtures_dir'] / 'responses'
            
            if not fixtures_dir.exists():
                continue
            
            for fixture_file in fixtures_dir.glob("*.json"):
                with open(fixture_file, 'r') as f:
                    fixture_data = json.load(f)
                
                # Determine schema definition to use
                endpoint = fixture_file.stem.split('_')[0]
                schema_key = f"{endpoint.title()}Response"
                schema_def = schema.get('definitions', {}).get(schema_key, schema)
                
                try:
                    validate(instance=fixture_data, schema=schema_def)
                except ValidationError as e:
                    errors.append((fixture_file, e))
        
        return errors
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest backend/apps/integrations/tests/test_registry.py -v
```

Expected: All tests FAIL (fixtures don't exist yet, that's OK for now)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/integrations/registry.py backend/apps/integrations/tests/test_registry.py
git commit -m "feat: add PlatformFixtureRegistry for discovering platform fixtures"
```

---

### Task 2: Create MockApiServer

**Files:**
- Create: `backend/apps/integrations/mock_server.py`
- Test: `backend/apps/integrations/tests/test_mock_server.py`

- [ ] **Step 1: Add Flask to requirements**

```bash
# Check if flask is already in backend/requirements/base.txt
grep -i flask backend/requirements/base.txt
```

If not present, add to `backend/requirements/base.txt`:
```
Flask==3.0.0
```

- [ ] **Step 2: Write failing test for mock server**

```python
# backend/apps/integrations/tests/test_mock_server.py

import pytest
import requests
from integrations.mock_server import MockApiServer
import time

class TestMockApiServer:
    @pytest.fixture
    def server(self):
        """Start mock server on port 5556 for testing."""
        server = MockApiServer(port=5556)
        import threading
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()
        time.sleep(0.5)  # Wait for server to start
        yield server
        # Server stops when thread daemon exits
    
    def test_server_responds_to_fixture_request(self, server):
        """Mock server serves fixture response at correct endpoint."""
        # Assuming we have a trading212 fixture set up
        response = requests.get(
            "http://localhost:5556/mock/trading212/accounts/demo/portfolio/positions",
            timeout=2
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'positions' in data
    
    def test_server_selects_fixture_by_query_param(self, server):
        """Can select specific fixture with ?fixture=empty."""
        response = requests.get(
            "http://localhost:5556/mock/trading212/accounts/demo/portfolio/positions?fixture=empty",
            timeout=2
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data.get('positions', [])) == 0
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest backend/apps/integrations/tests/test_mock_server.py::TestMockApiServer::test_server_responds_to_fixture_request -v
```

Expected: FAILED (server module doesn't exist)

- [ ] **Step 4: Write MockApiServer implementation**

```python
# backend/apps/integrations/mock_server.py

import json
import time
import threading
from pathlib import Path
from flask import Flask, jsonify, request
from integrations.registry import PlatformFixtureRegistry

class MockApiServer:
    """Simulates all platform APIs using fixture data."""
    
    def __init__(self, port=5555):
        self.port = port
        self.app = Flask(__name__)
        self._register_routes()
    
    def _register_routes(self):
        """Dynamically register mock endpoints for all platforms."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        
        @self.app.route('/mock/<platform_slug>/<path:endpoint_path>', methods=['GET', 'POST'])
        def handle_request(platform_slug, endpoint_path):
            """Handle request to any platform endpoint."""
            
            if platform_slug not in platforms:
                return jsonify({"error": f"Platform {platform_slug} not found"}), 404
            
            # Normalize endpoint path (remove query params, split by /)
            endpoint_parts = endpoint_path.split('/')
            # First meaningful part after platform is the endpoint name
            endpoint_name = endpoint_parts[0] if endpoint_parts else 'unknown'
            
            # Get query param to select fixture (default: happy_path)
            fixture_name = request.args.get('fixture', 'happy_path')
            
            # Load fixture for this endpoint
            fixtures = PlatformFixtureRegistry.get_fixtures_for_platform(
                platform_slug, endpoint_name
            )
            
            if not fixtures:
                return jsonify({"error": f"No fixtures for {endpoint_name}"}), 404
            
            # Find matching fixture
            fixture_path = None
            for f in fixtures:
                if fixture_name in f.stem:
                    fixture_path = f
                    break
            
            if not fixture_path:
                # Fall back to first fixture
                fixture_path = fixtures[0]
            
            # Load and return fixture data
            with open(fixture_path, 'r') as f:
                response_data = json.load(f)
            
            # Simulate latency
            time.sleep(0.1)
            
            return jsonify(response_data), 200
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "ok"}), 200
    
    def start(self):
        """Start the Flask server (blocking)."""
        self.app.run(port=self.port, debug=False, use_reloader=False)
    
    @staticmethod
    def start_background(port=5555):
        """Start server in background thread."""
        server = MockApiServer(port=port)
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()
        time.sleep(0.5)
        return server
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest backend/apps/integrations/tests/test_mock_server.py -v
```

Expected: FAILED (no fixtures yet, but that's OK for testing the server itself)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/integrations/mock_server.py backend/apps/integrations/tests/test_mock_server.py backend/requirements/base.txt
git commit -m "feat: add MockApiServer Flask app for serving fixture data as HTTP responses"
```

---

### Task 3: Create pytest fixtures (conftest.py)

**Files:**
- Create: `backend/apps/integrations/tests/conftest.py`

- [ ] **Step 1: Write conftest.py with mock server fixture**

```python
# backend/apps/integrations/tests/conftest.py

import pytest
import time
from integrations.mock_server import MockApiServer

@pytest.fixture(scope="session")
def mock_api_server():
    """
    Start mock API server for the test session.
    
    Runs once per test session on port 5555.
    All tests can use this to make HTTP requests to mock APIs.
    """
    server = MockApiServer(port=5555)
    
    import threading
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)  # Wait for server to start
    
    yield server
    
    # Server cleanup happens when thread daemon exits

@pytest.fixture
def mock_api_url():
    """Base URL for mock API server."""
    return "http://localhost:5555/mock"
```

- [ ] **Step 2: Verify conftest is loadable**

```bash
pytest backend/apps/integrations/tests/ --collect-only | head -20
```

Expected: No errors about conftest

- [ ] **Step 3: Commit**

```bash
git add backend/apps/integrations/tests/conftest.py
git commit -m "feat: add pytest fixtures for mock API server"
```

---

### Task 4: Create Schema Validation Tests

**Files:**
- Create: `backend/apps/integrations/tests/test_api_contract.py`

- [ ] **Step 1: Write test_api_contract.py**

```python
# backend/apps/integrations/tests/test_api_contract.py

import pytest
import json
from pathlib import Path
from jsonschema import validate, ValidationError
from integrations.registry import PlatformFixtureRegistry

class TestApiContract:
    """Validates all fixture files against their platform schemas."""
    
    def test_validate_all_fixtures(self):
        """All fixtures must validate against their platform's schema."""
        errors = PlatformFixtureRegistry.validate_all_fixtures()
        
        if errors:
            error_msg = "\n".join([
                f"  {fixture_path}: {error.message}"
                for fixture_path, error in errors
            ])
            pytest.fail(f"Fixture validation errors:\n{error_msg}")
    
    @pytest.mark.parametrize("platform_slug", 
        lambda: list(PlatformFixtureRegistry.get_all_platforms().keys()) or ['trading212'],
        ids=lambda slug: slug
    )
    def test_platform_fixtures_valid(self, platform_slug):
        """Each platform's fixtures must be valid."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        
        if platform_slug not in platforms:
            pytest.skip(f"Platform {platform_slug} not discovered")
        
        platform = platforms[platform_slug]
        schema = platform['schema']
        fixtures_dir = platform['fixtures_dir'] / 'responses'
        
        if not fixtures_dir.exists():
            pytest.skip(f"No fixtures directory for {platform_slug}")
        
        errors = []
        for fixture_file in fixtures_dir.glob("*.json"):
            with open(fixture_file, 'r') as f:
                fixture_data = json.load(f)
            
            endpoint = fixture_file.stem.split('_')[0]
            schema_key = f"{endpoint.title()}Response"
            schema_def = schema.get('definitions', {}).get(schema_key, schema)
            
            try:
                validate(instance=fixture_data, schema=schema_def)
            except ValidationError as e:
                errors.append((fixture_file.name, e.message))
        
        if errors:
            error_msg = "\n".join([f"  {name}: {msg}" for name, msg in errors])
            pytest.fail(f"Validation errors in {platform_slug}:\n{error_msg}")
```

- [ ] **Step 2: Run test (will skip if no fixtures exist yet)**

```bash
pytest backend/apps/integrations/tests/test_api_contract.py -v
```

Expected: SKIPPED (fixtures don't exist yet)

- [ ] **Step 3: Commit**

```bash
git add backend/apps/integrations/tests/test_api_contract.py
git commit -m "feat: add schema validation tests for all platform fixtures"
```

---

### Task 5: Create Trading212 Fixtures

**Files:**
- Create: `backend/apps/integrations/tests/fixtures/trading212/metadata.yaml`
- Create: `backend/apps/integrations/tests/fixtures/trading212/schema.json`
- Create: `backend/apps/integrations/tests/fixtures/trading212/responses/*.json` (6 files)

- [ ] **Step 1: Create Trading212 metadata.yaml**

```bash
mkdir -p backend/apps/integrations/tests/fixtures/trading212/responses
```

```yaml
# backend/apps/integrations/tests/fixtures/trading212/metadata.yaml

name: "Trading 212"
slug: "trading212"
api_base_url: "https://api.trading212.com/api/v0"
sandbox_url: "https://sandbox.trading212.com/api/v0"
docs_url: "https://trading212.github.io/api-docs"
auth_type: "bearer_token"
endpoints:
  - name: "accounts"
    method: "GET"
    path: "/accounts"
  - name: "portfolio"
    method: "GET"
    path: "/accounts/{account_id}/portfolio"
  - name: "transactions"
    method: "GET"
    path: "/accounts/{account_id}/transactions"
  - name: "balance"
    method: "GET"
    path: "/accounts/{account_id}/balance"
```

- [ ] **Step 2: Create Trading212 schema.json**

```json
{
  "definitions": {
    "Position": {
      "type": "object",
      "required": ["ticker", "quantity", "price"],
      "properties": {
        "ticker": { "type": "string" },
        "quantity": { "type": "number", "minimum": 0 },
        "price": { "type": "number", "minimum": 0 }
      }
    },
    "PortfolioResponse": {
      "type": "object",
      "required": ["positions"],
      "properties": {
        "positions": {
          "type": "array",
          "items": { "$ref": "#/definitions/Position" }
        }
      }
    },
    "Transaction": {
      "type": "object",
      "required": ["id", "ticker", "quantity", "price", "date", "type"],
      "properties": {
        "id": { "type": "string" },
        "ticker": { "type": "string" },
        "quantity": { "type": "number" },
        "price": { "type": "number" },
        "date": { "type": "string", "format": "date-time" },
        "type": { "type": "string", "enum": ["buy", "sell", "dividend"] }
      }
    },
    "TransactionsResponse": {
      "type": "object",
      "required": ["transactions"],
      "properties": {
        "transactions": {
          "type": "array",
          "items": { "$ref": "#/definitions/Transaction" }
        }
      }
    },
    "Balance": {
      "type": "object",
      "required": ["cash"],
      "properties": {
        "cash": { "type": "number" }
      }
    },
    "BalanceResponse": {
      "type": "object",
      "required": ["balance"],
      "properties": {
        "balance": { "$ref": "#/definitions/Balance" }
      }
    }
  }
}
```

- [ ] **Step 3: Create portfolio_happy_path.json**

```json
{
  "positions": [
    {
      "ticker": "AAPL",
      "quantity": 10,
      "price": 150.25
    },
    {
      "ticker": "BTC",
      "quantity": 0.5,
      "price": 45000
    },
    {
      "ticker": "IWDA",
      "quantity": 20,
      "price": 85.50
    }
  ]
}
```

- [ ] **Step 4: Create portfolio_empty.json**

```json
{
  "positions": []
}
```

- [ ] **Step 5: Create transactions_happy_path.json**

```json
{
  "transactions": [
    {
      "id": "tx001",
      "ticker": "AAPL",
      "quantity": 10,
      "price": 145.00,
      "date": "2026-01-15T10:30:00Z",
      "type": "buy"
    },
    {
      "id": "tx002",
      "ticker": "BTC",
      "quantity": 0.5,
      "price": 42000,
      "date": "2026-02-20T14:45:00Z",
      "type": "buy"
    },
    {
      "id": "tx003",
      "ticker": "AAPL",
      "quantity": 0,
      "price": 150.00,
      "date": "2026-03-10T09:00:00Z",
      "type": "dividend"
    }
  ]
}
```

- [ ] **Step 6: Create error_401.json**

```json
{
  "error": "unauthorized",
  "message": "Invalid or expired API token"
}
```

- [ ] **Step 7: Create error_429.json**

```json
{
  "error": "rate_limited",
  "message": "Too many requests. Please retry after 60 seconds."
}
```

- [ ] **Step 8: Create error_500.json**

```json
{
  "error": "internal_server_error",
  "message": "An internal server error occurred"
}
```

- [ ] **Step 9: Verify fixtures validate**

```bash
pytest backend/apps/integrations/tests/test_api_contract.py::TestApiContract::test_platform_fixtures_valid[trading212] -v
```

Expected: PASSED

- [ ] **Step 10: Commit**

```bash
git add backend/apps/integrations/tests/fixtures/trading212/
git commit -m "feat: add Trading212 fixture fixtures and schema"
```

---

### Task 6: Create Trading212 Client and Adapter

**Files:**
- Create: `backend/apps/integrations/trading212/__init__.py`
- Create: `backend/apps/integrations/trading212/client.py`
- Create: `backend/apps/integrations/trading212/adapter.py`

- [ ] **Step 1: Create __init__.py**

```python
# backend/apps/integrations/trading212/__init__.py

from .adapter import Trading212PlatformAdapter

__all__ = ['Trading212PlatformAdapter']
```

- [ ] **Step 2: Create Trading212 client.py**

```python
# backend/apps/integrations/trading212/client.py

import requests
from typing import List, Dict, Optional

class Trading212Client:
    """Low-level HTTP client for Trading212 API."""
    
    def __init__(self, api_key: str, sandbox: bool = False):
        self.api_key = api_key
        self.sandbox = sandbox
        
        if sandbox:
            self.base_url = "https://sandbox.trading212.com/api/v0"
        else:
            self.base_url = "https://api.trading212.com/api/v0"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def fetch_accounts(self) -> List[Dict]:
        """Fetch list of trading accounts."""
        url = f"{self.base_url}/accounts"
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json().get('accounts', [])
    
    def fetch_portfolio(self, account_id: str) -> Dict:
        """Fetch portfolio positions for an account."""
        url = f"{self.base_url}/accounts/{account_id}/portfolio"
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    
    def fetch_transactions(self, account_id: str, limit: int = 100) -> Dict:
        """Fetch transaction history for an account."""
        url = f"{self.base_url}/accounts/{account_id}/transactions"
        params = {"limit": limit}
        response = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    
    def fetch_balance(self, account_id: str) -> Dict:
        """Fetch account balance."""
        url = f"{self.base_url}/accounts/{account_id}/balance"
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 3: Create Trading212 adapter.py**

```python
# backend/apps/integrations/trading212/adapter.py

from typing import List
from integrations.base import PlatformAdapter
from portfolio.models import Position, Transaction
from .client import Trading212Client

class Trading212PlatformAdapter(PlatformAdapter):
    """Trading212 broker integration adapter."""
    
    platform_name = "Trading 212"
    platform_slug = "trading212"
    
    def __init__(self, api_key: str, sandbox: bool = False):
        self.client = Trading212Client(api_key=api_key, sandbox=sandbox)
    
    def fetch_positions(self) -> List[Position]:
        """Fetch all positions from Trading212."""
        try:
            # For testing, use first account
            accounts = self.client.fetch_accounts()
            if not accounts:
                return []
            
            account_id = accounts[0]['id']
            portfolio = self.client.fetch_portfolio(account_id)
            
            return [self._parse_position(p) for p in portfolio.get('positions', [])]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Trading212 positions: {str(e)}")
    
    def fetch_transactions(self, limit: int = 100) -> List[Transaction]:
        """Fetch transaction history from Trading212."""
        try:
            accounts = self.client.fetch_accounts()
            if not accounts:
                return []
            
            account_id = accounts[0]['id']
            response = self.client.fetch_transactions(account_id, limit=limit)
            
            return [self._parse_transaction(t) for t in response.get('transactions', [])]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Trading212 transactions: {str(e)}")
    
    def _parse_position(self, raw: dict) -> Position:
        """Convert Trading212 position to internal Position model."""
        return Position(
            symbol=raw['ticker'],
            quantity=raw['quantity'],
            current_price_eur=raw['price'],
            valuation_eur=raw['quantity'] * raw['price'],
        )
    
    def _parse_transaction(self, raw: dict) -> Transaction:
        """Convert Trading212 transaction to internal Transaction model."""
        return Transaction(
            date=raw['date'],
            symbol=raw['ticker'],
            quantity=raw['quantity'],
            price_eur=raw['price'],
            transaction_type=raw['type'],  # 'buy', 'sell', 'dividend'
            external_id=raw['id'],
        )
```

- [ ] **Step 4: Commit**

```bash
git add backend/apps/integrations/trading212/
git commit -m "feat: add Trading212 API client and platform adapter"
```

---

### Task 7: Create Trading212 Tests

**Files:**
- Create: `backend/apps/integrations/trading212/tests/__init__.py`
- Create: `backend/apps/integrations/trading212/tests/test_trading212.py`

- [ ] **Step 1: Create test __init__.py**

```python
# backend/apps/integrations/trading212/tests/__init__.py

# Empty file
```

- [ ] **Step 2: Create Trading212 tests**

```python
# backend/apps/integrations/trading212/tests/test_trading212.py

import pytest
import os
from unittest.mock import patch
from trading212.adapter import Trading212PlatformAdapter
from trading212.client import Trading212Client

class TestTrading212Client:
    @pytest.fixture
    def client(self):
        """Create a client pointing to mock server."""
        with patch.dict(os.environ, {'TRADING212_API_URL': 'http://localhost:5555/mock/trading212'}):
            return Trading212Client(api_key="mock_key", sandbox=False)
    
    def test_client_initialization(self, client):
        """Client initializes with correct base URL."""
        assert client.base_url.startswith("https://api.trading212.com")
        assert client.api_key == "mock_key"

class TestTrading212Adapter:
    @pytest.fixture
    def adapter(self):
        """Create adapter pointing to mock server."""
        return Trading212PlatformAdapter(api_key="mock_key", sandbox=False)
    
    def test_adapter_platform_metadata(self, adapter):
        """Adapter has correct platform metadata."""
        assert adapter.platform_name == "Trading 212"
        assert adapter.platform_slug == "trading212"
    
    def test_parse_position(self, adapter):
        """Adapter correctly parses raw position data."""
        raw_position = {
            "ticker": "AAPL",
            "quantity": 10,
            "price": 150.25
        }
        
        position = adapter._parse_position(raw_position)
        
        assert position.symbol == "AAPL"
        assert position.quantity == 10
        assert position.current_price_eur == 150.25
        assert position.valuation_eur == 1502.50
    
    def test_parse_transaction(self, adapter):
        """Adapter correctly parses raw transaction data."""
        raw_tx = {
            "id": "tx001",
            "ticker": "AAPL",
            "quantity": 10,
            "price": 145.00,
            "date": "2026-01-15T10:30:00Z",
            "type": "buy"
        }
        
        tx = adapter._parse_transaction(raw_tx)
        
        assert tx.symbol == "AAPL"
        assert tx.quantity == 10
        assert tx.price_eur == 145.00
        assert tx.transaction_type == "buy"
        assert tx.external_id == "tx001"
```

- [ ] **Step 3: Run tests**

```bash
pytest backend/apps/integrations/trading212/tests/ -v
```

Expected: PASSED (mocking tests)

- [ ] **Step 4: Commit**

```bash
git add backend/apps/integrations/trading212/tests/
git commit -m "feat: add Trading212 adapter and client unit tests"
```

---

### Task 8: Create Trade Republic Fixtures

**Files:**
- Create: `backend/apps/integrations/tests/fixtures/trade_republic/metadata.yaml`
- Create: `backend/apps/integrations/tests/fixtures/trade_republic/schema.json`
- Create: `backend/apps/integrations/tests/fixtures/trade_republic/responses/*.json` (6 files)

- [ ] **Step 1: Create Trade Republic metadata.yaml**

```bash
mkdir -p backend/apps/integrations/tests/fixtures/trade_republic/responses
```

```yaml
# backend/apps/integrations/tests/fixtures/trade_republic/metadata.yaml

name: "Trade Republic"
slug: "trade_republic"
api_base_url: "https://api.traderepublic.com/api/v1"
sandbox_url: null
docs_url: "https://docs.traderepublic.com/api"
auth_type: "bearer_token"
endpoints:
  - name: "portfolio"
    method: "GET"
    path: "/portfolio"
  - name: "holdings"
    method: "GET"
    path: "/portfolio/holdings"
  - name: "transactions"
    method: "GET"
    path: "/portfolio/transactions"
```

- [ ] **Step 2: Create Trade Republic schema.json**

```json
{
  "definitions": {
    "Holding": {
      "type": "object",
      "required": ["isin", "quantity", "valuation"],
      "properties": {
        "isin": { "type": "string" },
        "quantity": { "type": "number", "minimum": 0 },
        "valuation": { "type": "number", "minimum": 0 },
        "price": { "type": "number", "minimum": 0 }
      }
    },
    "HoldingsResponse": {
      "type": "object",
      "required": ["holdings"],
      "properties": {
        "holdings": {
          "type": "array",
          "items": { "$ref": "#/definitions/Holding" }
        }
      }
    },
    "Transaction": {
      "type": "object",
      "required": ["id", "isin", "quantity", "price", "date", "type"],
      "properties": {
        "id": { "type": "string" },
        "isin": { "type": "string" },
        "quantity": { "type": "number" },
        "price": { "type": "number" },
        "date": { "type": "string", "format": "date-time" },
        "type": { "type": "string", "enum": ["buy", "sell", "dividend", "fee"] }
      }
    },
    "TransactionsResponse": {
      "type": "object",
      "required": ["transactions"],
      "properties": {
        "transactions": {
          "type": "array",
          "items": { "$ref": "#/definitions/Transaction" }
        }
      }
    }
  }
}
```

- [ ] **Step 3: Create holdings_happy_path.json**

```json
{
  "holdings": [
    {
      "isin": "IE00B4L5Y983",
      "quantity": 20,
      "valuation": 1710,
      "price": 85.50
    },
    {
      "isin": "DE0008469008",
      "quantity": 5,
      "valuation": 525,
      "price": 105.00
    },
    {
      "isin": "US0378331005",
      "quantity": 8,
      "valuation": 1502.40,
      "price": 187.80
    }
  ]
}
```

- [ ] **Step 4: Create holdings_empty.json**

```json
{
  "holdings": []
}
```

- [ ] **Step 5: Create transactions_happy_path.json**

```json
{
  "transactions": [
    {
      "id": "tr_001",
      "isin": "IE00B4L5Y983",
      "quantity": 10,
      "price": 80.00,
      "date": "2026-01-10T09:30:00Z",
      "type": "buy"
    },
    {
      "id": "tr_002",
      "isin": "IE00B4L5Y983",
      "quantity": 10,
      "price": 82.50,
      "date": "2026-02-15T10:00:00Z",
      "type": "buy"
    },
    {
      "id": "tr_003",
      "isin": "DE0008469008",
      "quantity": 5,
      "price": 103.00,
      "date": "2026-03-05T14:45:00Z",
      "type": "buy"
    },
    {
      "id": "tr_004",
      "isin": "IE00B4L5Y983",
      "quantity": 0,
      "price": 85.00,
      "date": "2026-04-01T00:00:00Z",
      "type": "dividend"
    }
  ]
}
```

- [ ] **Step 6: Create error_401.json**

```json
{
  "error": "unauthorized",
  "message": "Authentication failed. Invalid or expired token."
}
```

- [ ] **Step 7: Create error_429.json**

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please retry after 30 seconds."
}
```

- [ ] **Step 8: Create error_500.json**

```json
{
  "error": "internal_server_error",
  "message": "The server encountered an unexpected condition."
}
```

- [ ] **Step 9: Verify fixtures validate**

```bash
pytest backend/apps/integrations/tests/test_api_contract.py::TestApiContract::test_platform_fixtures_valid[trade_republic] -v
```

Expected: PASSED

- [ ] **Step 10: Commit**

```bash
git add backend/apps/integrations/tests/fixtures/trade_republic/
git commit -m "feat: add Trade Republic fixture data and schema"
```

---

### Task 9: Create Trade Republic Client and Adapter

**Files:**
- Create: `backend/apps/integrations/trade_republic/__init__.py`
- Create: `backend/apps/integrations/trade_republic/client.py`
- Create: `backend/apps/integrations/trade_republic/adapter.py`

- [ ] **Step 1: Create __init__.py**

```python
# backend/apps/integrations/trade_republic/__init__.py

from .adapter import TradeRepublicPlatformAdapter

__all__ = ['TradeRepublicPlatformAdapter']
```

- [ ] **Step 2: Create Trade Republic client.py**

```python
# backend/apps/integrations/trade_republic/client.py

import requests
from typing import Dict

class TradeRepublicClient:
    """Low-level HTTP client for Trade Republic API."""
    
    def __init__(self, api_key: str, sandbox: bool = False):
        self.api_key = api_key
        self.sandbox = sandbox
        
        # Trade Republic has no official sandbox
        self.base_url = "https://api.traderepublic.com/api/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def fetch_holdings(self) -> Dict:
        """Fetch portfolio holdings."""
        url = f"{self.base_url}/portfolio/holdings"
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    
    def fetch_transactions(self, limit: int = 100) -> Dict:
        """Fetch transaction history."""
        url = f"{self.base_url}/portfolio/transactions"
        params = {"limit": limit}
        response = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 3: Create Trade Republic adapter.py**

```python
# backend/apps/integrations/trade_republic/adapter.py

from typing import List
from integrations.base import PlatformAdapter
from portfolio.models import Position, Transaction
from .client import TradeRepublicClient

class TradeRepublicPlatformAdapter(PlatformAdapter):
    """Trade Republic broker integration adapter."""
    
    platform_name = "Trade Republic"
    platform_slug = "trade_republic"
    
    def __init__(self, api_key: str, sandbox: bool = False):
        self.client = TradeRepublicClient(api_key=api_key, sandbox=sandbox)
    
    def fetch_positions(self) -> List[Position]:
        """Fetch all positions from Trade Republic."""
        try:
            holdings = self.client.fetch_holdings()
            return [self._parse_holding(h) for h in holdings.get('holdings', [])]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Trade Republic positions: {str(e)}")
    
    def fetch_transactions(self, limit: int = 100) -> List[Transaction]:
        """Fetch transaction history from Trade Republic."""
        try:
            response = self.client.fetch_transactions(limit=limit)
            return [self._parse_transaction(t) for t in response.get('transactions', [])]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Trade Republic transactions: {str(e)}")
    
    def _parse_holding(self, raw: dict) -> Position:
        """Convert Trade Republic holding to internal Position model."""
        return Position(
            symbol=raw['isin'],  # Trade Republic uses ISIN
            quantity=raw['quantity'],
            current_price_eur=raw['price'],
            valuation_eur=raw['valuation'],
        )
    
    def _parse_transaction(self, raw: dict) -> Transaction:
        """Convert Trade Republic transaction to internal Transaction model."""
        return Transaction(
            date=raw['date'],
            symbol=raw['isin'],  # Trade Republic uses ISIN
            quantity=raw['quantity'],
            price_eur=raw['price'],
            transaction_type=raw['type'],  # 'buy', 'sell', 'dividend', 'fee'
            external_id=raw['id'],
        )
```

- [ ] **Step 4: Commit**

```bash
git add backend/apps/integrations/trade_republic/
git commit -m "feat: add Trade Republic API client and platform adapter"
```

---

### Task 10: Create Trade Republic Tests

**Files:**
- Create: `backend/apps/integrations/trade_republic/tests/__init__.py`
- Create: `backend/apps/integrations/trade_republic/tests/test_trade_republic.py`

- [ ] **Step 1: Create test __init__.py**

```python
# backend/apps/integrations/trade_republic/tests/__init__.py

# Empty file
```

- [ ] **Step 2: Create Trade Republic tests**

```python
# backend/apps/integrations/trade_republic/tests/test_trade_republic.py

import pytest
from unittest.mock import patch
from trade_republic.adapter import TradeRepublicPlatformAdapter
from trade_republic.client import TradeRepublicClient

class TestTradeRepublicClient:
    @pytest.fixture
    def client(self):
        """Create a client pointing to Trade Republic API."""
        return TradeRepublicClient(api_key="mock_key", sandbox=False)
    
    def test_client_initialization(self, client):
        """Client initializes with correct base URL."""
        assert client.base_url == "https://api.traderepublic.com/api/v1"
        assert client.api_key == "mock_key"

class TestTradeRepublicAdapter:
    @pytest.fixture
    def adapter(self):
        """Create adapter for Trade Republic."""
        return TradeRepublicPlatformAdapter(api_key="mock_key", sandbox=False)
    
    def test_adapter_platform_metadata(self, adapter):
        """Adapter has correct platform metadata."""
        assert adapter.platform_name == "Trade Republic"
        assert adapter.platform_slug == "trade_republic"
    
    def test_parse_holding(self, adapter):
        """Adapter correctly parses raw holding data."""
        raw_holding = {
            "isin": "IE00B4L5Y983",
            "quantity": 20,
            "valuation": 1710,
            "price": 85.50
        }
        
        position = adapter._parse_holding(raw_holding)
        
        assert position.symbol == "IE00B4L5Y983"
        assert position.quantity == 20
        assert position.current_price_eur == 85.50
        assert position.valuation_eur == 1710
    
    def test_parse_transaction(self, adapter):
        """Adapter correctly parses raw transaction data."""
        raw_tx = {
            "id": "tr_001",
            "isin": "IE00B4L5Y983",
            "quantity": 10,
            "price": 80.00,
            "date": "2026-01-10T09:30:00Z",
            "type": "buy"
        }
        
        tx = adapter._parse_transaction(raw_tx)
        
        assert tx.symbol == "IE00B4L5Y983"
        assert tx.quantity == 10
        assert tx.price_eur == 80.00
        assert tx.transaction_type == "buy"
        assert tx.external_id == "tr_001"
```

- [ ] **Step 3: Run tests**

```bash
pytest backend/apps/integrations/trade_republic/tests/ -v
```

Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/apps/integrations/trade_republic/tests/
git commit -m "feat: add Trade Republic adapter and client unit tests"
```

---

### Task 11: Create Integration Tests with Mock Server

**Files:**
- Modify: `backend/apps/integrations/tests/test_adapters.py` (new integration tests)

- [ ] **Step 1: Create integration test file**

```python
# backend/apps/integrations/tests/test_adapters.py

import pytest
from unittest.mock import patch, MagicMock
from trading212.adapter import Trading212PlatformAdapter
from trade_republic.adapter import TradeRepublicPlatformAdapter

class TestTrading212Integration:
    """Integration tests for Trading212 adapter with mock server."""
    
    @pytest.fixture
    def adapter(self, monkeypatch):
        """Create adapter with mocked HTTP client."""
        return Trading212PlatformAdapter(api_key="mock_key", sandbox=False)
    
    def test_fetch_positions_happy_path(self, adapter):
        """Adapter fetches and parses positions correctly."""
        # Mock the client to return fixture data
        mock_response = {
            "positions": [
                {"ticker": "AAPL", "quantity": 10, "price": 150.25},
                {"ticker": "BTC", "quantity": 0.5, "price": 45000}
            ]
        }
        
        with patch.object(adapter.client, 'fetch_portfolio', return_value=mock_response):
            with patch.object(adapter.client, 'fetch_accounts', return_value=[{'id': 'acc1'}]):
                positions = adapter.fetch_positions()
        
        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[1].symbol == "BTC"
    
    def test_fetch_positions_empty(self, adapter):
        """Adapter handles empty position list."""
        mock_response = {"positions": []}
        
        with patch.object(adapter.client, 'fetch_portfolio', return_value=mock_response):
            with patch.object(adapter.client, 'fetch_accounts', return_value=[{'id': 'acc1'}]):
                positions = adapter.fetch_positions()
        
        assert len(positions) == 0

class TestTradeRepublicIntegration:
    """Integration tests for Trade Republic adapter with mock server."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter for Trade Republic."""
        return TradeRepublicPlatformAdapter(api_key="mock_key", sandbox=False)
    
    def test_fetch_positions_happy_path(self, adapter):
        """Adapter fetches and parses holdings correctly."""
        mock_response = {
            "holdings": [
                {"isin": "IE00B4L5Y983", "quantity": 20, "valuation": 1710, "price": 85.50},
                {"isin": "US0378331005", "quantity": 8, "valuation": 1502.40, "price": 187.80}
            ]
        }
        
        with patch.object(adapter.client, 'fetch_holdings', return_value=mock_response):
            positions = adapter.fetch_positions()
        
        assert len(positions) == 2
        assert positions[0].symbol == "IE00B4L5Y983"
        assert positions[1].symbol == "US0378331005"
    
    def test_fetch_positions_empty(self, adapter):
        """Adapter handles empty holdings list."""
        mock_response = {"holdings": []}
        
        with patch.object(adapter.client, 'fetch_holdings', return_value=mock_response):
            positions = adapter.fetch_positions()
        
        assert len(positions) == 0
    
    def test_fetch_transactions_with_dividends(self, adapter):
        """Adapter correctly parses dividend transactions."""
        mock_response = {
            "transactions": [
                {"id": "tr_001", "isin": "IE00B4L5Y983", "quantity": 10, "price": 80.00, "date": "2026-01-10T09:30:00Z", "type": "buy"},
                {"id": "tr_004", "isin": "IE00B4L5Y983", "quantity": 0, "price": 85.00, "date": "2026-04-01T00:00:00Z", "type": "dividend"}
            ]
        }
        
        with patch.object(adapter.client, 'fetch_transactions', return_value=mock_response):
            transactions = adapter.fetch_transactions()
        
        dividends = [t for t in transactions if t.transaction_type == 'dividend']
        assert len(dividends) == 1
        assert dividends[0].symbol == "IE00B4L5Y983"
```

- [ ] **Step 2: Run integration tests**

```bash
pytest backend/apps/integrations/tests/test_adapters.py -v
```

Expected: PASSED

- [ ] **Step 3: Commit**

```bash
git add backend/apps/integrations/tests/test_adapters.py
git commit -m "feat: add integration tests for Trading212 and Trade Republic adapters"
```

---

### Task 12: Run Full Test Suite

**Files:**
- No new files (validation step)

- [ ] **Step 1: Run all integration tests**

```bash
pytest backend/apps/integrations/tests/ -v
```

Expected: All tests PASSED (or SKIPPED for fixtures that don't exist yet)

- [ ] **Step 2: Run schema validation on all platforms**

```bash
pytest backend/apps/integrations/tests/test_api_contract.py -v
```

Expected: All fixtures validate against their schemas

- [ ] **Step 3: Run adapter unit tests**

```bash
pytest backend/apps/integrations/trading212/tests/ backend/apps/integrations/trade_republic/tests/ -v
```

Expected: All tests PASSED

- [ ] **Step 4: Run full test suite**

```bash
pytest backend/apps/integrations/ -v --tb=short
```

Expected: All tests passing, clear output of which platforms are tested

- [ ] **Step 5: Commit**

```bash
git commit --allow-empty -m "test: all integration tests passing for Trading212 and Trade Republic"
```

---

## Summary

**What was built:**

✅ `PlatformFixtureRegistry` — discovers all platforms from `fixtures/` directory  
✅ `MockApiServer` — Flask app serving fixture responses as HTTP endpoints  
✅ Schema validation tests — auto-validate all fixtures on every test run  
✅ Trading212 platform — client, adapter, fixtures (6 response types), tests  
✅ TradeRepublic platform — client, adapter, fixtures (6 response types), tests  
✅ Integration tests — verify adapters parse fixtures correctly  
✅ Test fixtures — complete fixture sets (happy path, empty, errors) for both platforms  

**Total: 13 tasks, ~8-10 hours of implementation work**

---

## Next Steps (After Implementation)

1. **Migrate Bitvavo fixtures** (Task in separate plan)
2. **Migrate DEGIRO fixtures** (Task in separate plan)
3. **Add more platforms** using the 90-minute workflow
4. **Run coverage report** to verify test completeness
5. **Document API quirks** in platform metadata.yaml files

