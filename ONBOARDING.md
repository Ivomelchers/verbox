# Developer Onboarding Guide — MijnVermogen / Vermogenspeil

**Last updated:** July 1, 2026  
**Project phase:** Phase 9 — MVP Testing & Acceptance

---

## 1. What is this project?

**MijnVermogen** (product name) / **Vermogenspeil** (repository name) is a Dutch SaaS platform for investors. It does two things:

1. **Portfolio tracking** — connect all your investment accounts (brokers, crypto exchanges, precious metals) in one place and see your total wealth, returns, and allocation.
2. **Box 3 tax preparation** — calculate how much Dutch Box 3 wealth tax you owe, and optionally prove that your *actual* return was lower than the government's flat-rate estimate (the "tegenbewijsregeling"), potentially saving money.

The platform handles real financial data for real users. Tax calculation errors have direct legal consequences. Take this seriously.

**Two subscription tiers:**
- **Free** — portfolio tracking, platform connections, transaction overview
- **Premium** (€49.99/year) — everything free + Box 3 tax calculation, PDF tax reports, deeper portfolio analytics

**Client/stakeholders:** Ivo (product owner), Frank (frank.jimenez@cloudnation.nl)

---

---

## 3. Where to find things

### Key documentation

| File | What it contains |
|------|-----------------|
| `CLAUDE.md` | Agent instructions — read this first in every session |
| `docs/product/REQUIREMENTS.md` | Contract requirements, acceptance criteria per milestone |
| `docs/product/FSD.md` | Full functional specification (25 chapters, ~3000 lines) — the source of truth for what the product should do |
| `docs/product/ROADMAP.md` | Development phases and per-phase checklists |
| `docs/development/PROGRESS.md` | **Most important for day-to-day work.** Current status, session log, gap analysis vs FSD |
| `docs/architecture/STACK.md` | Tech stack decisions and project structure |
| `docs/architecture/DESIGN.md` | Design system |
| `docs/development/TRAPS.md` | Common mistakes — read this before every commit |

### Visual references (repo root)
- `MijnVermogen-Gratis-v4.html` — Free tier UI mockup
- `MijnVermogen-Premium-v4.html` — Premium tier UI mockup

These HTML files are the visual target. When in doubt about how something should look, open these.

### Code structure

```
vermogenspeil/
├── backend/                    # Django (Python)
│   ├── config/                 # Settings (base / development / production)
│   ├── apps/
│   │   ├── accounts/           # Users, Auth0, registration, 2FA
│   │   ├── portfolio/          # Portfolios, assets, positions, transactions
│   │   ├── integrations/       # Broker connectors (Bitvavo, DEGIRO, Saxo, demo)
│   │   │   ├── bitvavo/
│   │   │   ├── degiro/
│   │   │   ├── saxo/
│   │   │   ├── csv/            # Generic CSV import framework
│   │   │   └── base.py         # PlatformAdapter base class
│   │   ├── tax/                # Box 3 calculations (forfaitair + tegenbewijsregeling)
│   │   ├── pricing/            # Market data fetching and caching
│   │   │   └── providers/      # Marketstack (equities), Bitvavo (crypto), etc.
│   │   ├── payments/           # Mollie — NOT YET IMPLEMENTED
│   │   └── snapshots/          # January 1st portfolio snapshots (immutable)
│   ├── fixtures/               # Test CSV files (DEGIRO samples)
│   └── requirements/           # base.txt / development.txt / production.txt
│
├── frontend/                   # React + TypeScript (Vite)
│   └── src/
│       ├── components/         # Reusable UI components
│       ├── pages/              # One file per route/screen
│       ├── hooks/              # Custom React hooks
│       ├── api/                # All API calls (central Axios client in api/api.ts)
│       ├── types/              # TypeScript types
│       └── theme.ts            # Chakra UI theme (colors, fonts, etc.)
│
├── docs/                       # All documentation
└── render.yaml                 # Infrastructure as code (Render deployment)
```

---

## 4. Tech stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React + TypeScript | Type safety, large ecosystem |
| UI components | Chakra UI | Accessible, consistent |
| Backend | Django + Django REST Framework | Built-in security, ORM, admin panel |
| Database | PostgreSQL | Financial data needs relational DB |
| Auth | **Auth0** | Handles MFA, password reset, sessions |
| Backend hosting | Render | Django + PostgreSQL on one platform |
| Frontend hosting | Vercel | Automatic deploys, fast CDN |
| Background jobs | Celery + Redis | Platform sync, automatic Jan 1 snapshots |
| Payments | Mollie (iDEAL) | Dutch market — **not yet implemented** |
| API key encryption | Python `cryptography` (AES-256-GCM) | Required by contract |
| Market data | Marketstack (equities), Bitvavo (crypto) | Yahoo Finance was replaced June 16 |

**Important Auth note:** Auth0 handles all authentication. Django does NOT store passwords. The flow is: browser → Django proxy → Auth0. Django validates the `id_token` on every request.

---

## 5. Environment variables you need

### Backend (`backend/.env`)
```
SECRET_KEY=                     # Django secret key
DATABASE_URL=                   # PostgreSQL connection string
REDIS_URL=                      # Redis (for Celery + cache)
ENCRYPTION_KEY=                 # AES-256 key (32 bytes, base64) — for API key storage
AUTH0_DOMAIN=                   # Auth0 tenant domain
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_AUDIENCE=
MARKETSTACK_API_KEY=            # For stock/ETF prices
MARKETSTACK_API_URL=
EXCHANGERATESAPI_API_KEY=       # For currency conversion (USD/GBP → EUR)
EXCHANGERATESAPI_API_URL=
MOLLIE_API_KEY=                 # NOT YET IN USE
SAXO_CLIENT_ID=                 # Saxo Bank OAuth (sandbox available)
SAXO_CLIENT_SECRET=
```

### Frontend (`frontend/.env`)
```
VITE_API_BASE_URL=              # Backend URL (e.g. http://localhost:8000)
```

**Never commit `.env` files.** They are in `.gitignore`.

---

## 6. Where we are right now (July 1, 2026)

### What is complete and working

- **Auth** — Registration, email verification, login, 2FA (via Auth0), password reset, account deletion (GDPR soft-delete)
- **Portfolio** — Dashboard with total wealth, movers, allocation chart, 12-month chart; portfolio list with positions; transaction history with CSV export
- **Platform integrations** — Bitvavo (live API sync), DEGIRO (CSV import v2 with duplicate detection), Saxo Bank (OAuth2 + CSV, sandbox tested), Demo mode (dev only)
- **Tax calculations** — Box 3 forfaitair (6-step Dutch tax formula), actual return (tegenbewijsregeling), PDF tax report, manual input for bank balances / real estate / debts
- **Onboarding** — 3-step onboarding flow for new users, premium gate UI with lock icons
- **Pricing** — Marketstack for stocks/ETFs, Bitvavo for crypto, currency conversion; Redis caching
- **Infrastructure** — Render (backend + PostgreSQL), Vercel (frontend), GitHub Actions CI, Celery + Redis for background tasks

### What is deliberately NOT done yet

- **Mollie payments (Phase 7)** — The payment flow for upgrading to Premium is not built. Currently `PREMIUM_UNLOCKED_FOR_ALL=True` in settings, meaning everyone gets Premium features for free during testing. This needs to be built before launch.
- **Phase 10: Extra platform integrations** — IBKR/Lynx, Coinbase, Kraken, OKX, Bybit, eToro, ABN/ING/Rabobank PDF, Meesman PDF, Trading 212, and 20+ more platforms are in the catalogue but not connected.
- **Phase 11: Full security & GDPR** — Audit logging, data export requests (Art. 15), cookie consent, privacy policy in-app, pen test.
- **Phase 12: Production & handover** — Final client acceptance test, monitoring (Sentry/Grafana), automated backups, domain/DNS setup, full documentation handover.

### Known limitations in what IS built

- Marketstack free tier (100 requests/month) works for MVP testing but needs an upgrade for production
- **UCITS ETFs (IWDA, VWCE, VUAA) do not get live prices** from Marketstack — this affects most Dutch investors. The old Yahoo Finance provider is still in the codebase as a fallback but intentionally disabled. This needs a decision before launch.
- Tax year switch happens at "1 May 00:00" but the FSD says it should be "2 May" — this is a known bug
- `VIRTUAL_DATE` config flag for testing the tax year switch is not yet implemented

---

## 7. The detailed gap list (what still needs to be built)

The `docs/development/PROGRESS.md` has a full FSD gap analysis (every feature from the 25-chapter spec mapped to its current status). Here is a summary of the most important missing pieces, in rough priority order:

### Pre-launch blockers

| Feature | Where in FSD |
|---------|-------------|
| Mollie iDEAL payment flow + webhook | FSD §16, phase 7 |
| 2FA mandatory for Premium users | FSD §2.4 |
| Tax year switch: fix 1 May → 2 May | FSD §17.2 |
| `VIRTUAL_DATE` for acceptance testing | FSD §17.6.3 |

### Important but not blocking launch

| Feature | Where in FSD |
|---------|-------------|
| Premium portfolio table (cost basis, dividend, fees, Jan 1 value per position) | FSD §6.2 |
| Donut chart per individual position (not just asset class) | FSD §6.2.1 |
| "Heffingsvrije grens" forward-looking tracker on tax page | FSD §8.2.3 |
| Historical tax year dropdown | FSD §17.5 |
| PDF report archive in profile | FSD §17.5 |
| Dark/light theme toggle | FSD §4.5 |
| Breadcrumbs | FSD §4.4 |
| Platform comparator quiz (5 questions) | FSD §14.5 |
| Affiliate link tracking | FSD §14.3 |

### Nice-to-have / post-launch

| Feature | Where |
|---------|-------|
| Extra broker integrations (30+ platforms) | FSD §18, phase 10 |
| Full GDPR data export portal | FSD §23.3, phase 11 |
| Monitoring + backups + pen test | FSD §23.4, phase 12 |
| Phase 2: Vermogensaanwasbelasting (2028 tax reform) | FSD §17.7 |

---

## 8. Critical things you must understand

These are the traps that caused bugs or near-misses already. See `docs/development/TRAPS.md` for full detail.

### Tax year switch date
The "relevant tax year" on the tax page switches automatically. Before May 2 of year Y+1, show tax year Y. After May 2, show year Y+1. **The current code uses May 1 (wrong) — it should be May 2.**

### January 1 timezone
The portfolio snapshot for Box 3 must be taken at exactly **January 1, 00:00:00 CET (Europe/Amsterdam)**, not UTC. UTC would be December 31 at 23:00. Always use `pytz.timezone('Europe/Amsterdam')`, never naive datetimes.

### Snapshot immutability
The January 1 portfolio snapshot is the legal basis for the tax calculation. It can be recalculated if a user adds historical transactions **before** May 1 of the following year. After May 1, it is locked and must never change. Never delete snapshots.

### API key encryption
Broker API keys (Bitvavo, Saxo, etc.) are stored encrypted with AES-256-GCM. The encryption key comes from the `ENCRYPTION_KEY` environment variable. If this key is lost, all stored API keys are permanently inaccessible.

### Box 3 categories
Dutch Box 3 has three asset categories with different tax rates: bank deposits, investments/other assets, and debts. These must never be mixed in calculations. Each asset has an explicit `fiscale_category` field.

### DEGIRO: no unofficial API
The `degiro-connector` Python library exists but requires sharing the user's credentials (username + password) and violates DEGIRO's terms of service. **Only CSV import.** This is a deliberate decision.

### User data isolation
Every database query must filter on the logged-in user. The `UserOwnedQuerySet` base class enforces this. Never call `.objects.all()` in a view.

---

## 9. How to get the app running locally

1. **Clone the repo**
2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements/development.txt
   cp .env.example .env       # fill in the required values
   python manage.py migrate
   python manage.py runserver
   ```
3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local   # set VITE_API_BASE_URL=http://localhost:8000
   npm run dev
   ```
4. **Optional: load demo data (dev only)**
   ```bash
   python manage.py seed_demo_portfolio --email=your@email.com
   ```
   This creates a fake Bitvavo + DEGIRO portfolio so you can explore without real accounts.

5. **Run tests:**
   ```bash
   python manage.py test       # 330 tests, all should pass
   ```

### Minimum required env vars to get started
Without Bitvavo credentials or real user data, you only need:
- `SECRET_KEY`, `DATABASE_URL`, `ENCRYPTION_KEY`, Auth0 variables
- Without `MARKETSTACK_API_KEY`, stock prices will fail gracefully

---

## 10. How the API works

- Base URL: `/api/v1/`
- Auth: JWT Bearer token (from Auth0 via Django proxy)
- All responses use this shape:
  ```json
  { "data": {}, "error": null, "message": "" }
  ```
- All endpoints require authentication unless explicitly public

Key endpoint groups:
| Path prefix | What it does |
|-------------|-------------|
| `/api/v1/auth/` | Login, register, 2FA, password reset, profile |
| `/api/v1/portfolios/` | Portfolio CRUD, assets, positions, transactions |
| `/api/v1/portfolios/dashboard/` | Dashboard aggregated data |
| `/api/v1/integrations/` | Platform connections (Bitvavo, CSV upload, Saxo) |
| `/api/v1/tax/` | Box 3 calculations, snapshots, PDF report |
| `/api/v1/pricing/` | Live and historical market prices |
| `/api/v1/tax/context/` | Current relevant tax year |

---

## 11. Key architectural decisions (already made, don't change)

These decisions are final unless you have a very good reason and explicit client approval:

- **Auth0 for authentication** — Django does not store passwords. Swapping this out would require rebuilding the entire auth layer.
- **No DEGIRO API** — Only CSV. See TRAPS.md for why.
- **Marketstack for stocks** — Yahoo Finance was removed June 16, 2026 due to reliability. Yahoo code still exists in `yahoo_equities.py` as an emergency fallback.
- **Mollie for payments** — iDEAL is required for the Dutch market. No Stripe alternative.
- **Tax parameters in database** — Forfaitaire tax rates (percentages, thresholds) are stored in `TaxYearParameter` database records, never hardcoded. This allows updating rates after a new Dutch budget without a code release.
- **Render (backend) + Vercel (frontend)** — Two separate hosting platforms. Do not merge them.
- **Celery for background tasks** — Any call to an external API must go through Celery, never in a Django view directly.

---

## 12. What to work on next

Based on the current state (July 2026), the logical next steps are:

1. **Fix the May 2 tax year switch** — small backend + frontend fix, needed for correctness
2. **Add `VIRTUAL_DATE` setting** — needed to properly test the tax year switch
3. **End-to-end acceptance test** — get Ivo to import a real DEGIRO export and verify the tax calculation
4. **Build Mollie payment flow** — Phase 7, currently blocked by MVP acceptance. Without this, Premium cannot be sold.
5. **Premium portfolio table** — The FSD-specified premium features (cost basis column, dividend/fees per position, Jan 1 value) are not yet in the UI.
6. **Platform integrations** — IBKR, Coinbase, Kraken are next in priority after MVP acceptance.

---

## 13. Glossary (Dutch tax terms you will encounter)

| Term | Meaning |
|------|---------|
| Box 3 | Dutch wealth tax on savings and investments |
| Peildatum | Reference date = January 1, 00:00 CET. The value of your portfolio on this date is used for tax calculation. |
| Heffingsvrij vermogen | Tax-free threshold (€57,000 per person in 2025). Wealth below this is not taxed. |
| Forfaitair rendement | The government's assumed flat-rate return on your assets. You are taxed on this even if your actual return was lower. |
| Tegenbewijsregeling | The legal right to prove your *actual* return was lower than the forfait, and pay tax on the actual return instead. This is the "werkelijk rendement" feature in Premium. |
| OWR-rapport | "Opgaaf Werkelijk Rendement" — the official report format for submitting actual return to the tax authority. |
| Werkelijk rendement | Actual return = (end value − start value − net deposits) + dividends + staking + interest − fees |
| Fiscaal partner | Tax partner (usually spouse). Having one doubles the tax-free threshold and allows income/asset splitting. |

---

## 14. Who to talk to if you're stuck

- Product questions, business decisions, client wishes → **Ivo** (product owner)
- Technical questions about this repo → check `docs/development/PROGRESS.md` session log first (30+ sessions documented)
- If something in the FSD is unclear → `docs/product/FSD.md` is the authoritative spec, not the code

**The rule from CLAUDE.md:** If you are stuck, stop. Do not keep writing. Ask specifically what you need.

---

*This document is a living handoff guide. Update it when the project state changes significantly.*
