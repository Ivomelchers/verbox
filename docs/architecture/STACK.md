# STACK.md — Tech Stack & Projectstructuur

## Beslissingen zijn definitief

De keuzes in dit bestand zijn vastgelegd. Je wisselt niet van technologie midden in het project. Als je een probleem tegenkomt met een tool, los het op binnen die tool.

---

## Stack Overzicht

| Laag | Technologie | Waarom |
|------|-------------|--------|
| Frontend | React + TypeScript | Type safety, component ecosystem |
| UI Library | Chakra UI | Accessible, consistent design system |
| Backend | Django + Django REST Framework | Ingebouwde security, ORM, admin panel |
| Database | PostgreSQL op Render | Financiële data vereist relationele DB, complexe queries |
| Backend Hosting | Render | Gratis tier voor development; Django + PostgreSQL op één platform |
| Frontend Hosting | Vercel | Gratis, snel, automatische deploys |
| Betalingen | Mollie | iDEAL support voor Nederlandse markt |
| Email | Resend of SendGrid | Transactionele emails |
| Background Tasks | Celery + Redis | Peildatum snapshots, broker sync |
| Encryptie API Keys | cryptography (Python) AES-256-GCM | Vereiste uit contract |

---

## Projectstructuur

```
vermogenspeil/
├── backend/                    # Django project
│   ├── config/                 # Django settings
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/           # Auth, users, 2FA
│   │   ├── portfolio/          # Portfolios, assets, posities
│   │   ├── integrations/       # Broker koppelingen
│   │   │   ├── bitvavo/
│   │   │   ├── degiro/
│   │   │   └── base.py        # PlatformAdapter base class
│   │   ├── tax/                # Box 3 berekeningen
│   │   ├── pricing/            # Koersdata ophalen en cachen
│   │   ├── payments/           # Mollie integratie
│   │   └── snapshots/          # Peildatum snapshots
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── manage.py
│   └── Dockerfile
├── frontend/                   # React project
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── portfolio/
│   │   │   ├── tax/
│   │   │   └── auth/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/           # API calls
│   │   ├── types/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── docs/                       # Technische documentatie
│   ├── README.md               # Documentatie-index
│   ├── product/                # REQUIREMENTS, ROADMAP
│   ├── architecture/           # STACK, DESIGN
│   ├── development/            # TRAPS, PROGRESS, DEPLOYMENT
│   ├── api/                    # API documentatie
│   └── decisions/              # Architectuur beslissingen (ADR's)
├── .github/
│   └── workflows/              # CI/CD pipelines
├── render.yaml                 # Render Blueprint (API + PostgreSQL)
├── CLAUDE.md                   # Agent context (root)
└── README.md                   # Project entry
```

---

## Backend Details

### Django Apps Verantwoordelijkheden

**accounts**
- Custom User model (nooit Django's default uitbreiden achteraf)
- 2FA via django-otp of django-two-factor-auth
- Email verificatie flow
- Wachtwoord reset
- JWT tokens via djangorestframework-simplejwt

**portfolio**
- Portfolio model (één user kan meerdere portfolios hebben)
- Asset model (aandeel, ETF, crypto, edelmetaal, spaargeld)
- Positie model (hoeveel van welk asset)
- Transactie model (aankoop, verkoop, dividend)

**integrations**
- Base PlatformAdapter klasse — elke broker erft hiervan
- BitvavoPlatformAdapter
- DEGIROPlatformAdapter
- API key encrypted opslag per user per platform
- Sync status tracking

**tax**
- Box3Calculator klasse
- ForfaitairCalculator
- TegenbewijsCalculator
- Vermogenscategorie splitsing
- Unittest coverage verplicht: minimaal 95%

**pricing**
- PriceService interface
- Cache laag (Redis of database cache)
- Fallback bij API failure

**payments**
- Mollie webhook handler
- Subscriptie status management
- Tier upgrade/downgrade logica

**snapshots**
- PeilDatumSnapshot model
- Celery task voor automatische snapshot op 1 jan 00:00 CET
- Immutable na creatie (geen update of delete mogelijk)

---

## Frontend Details

### State Management
Gebruik React Context voor auth state. Voor complexere state gebruik Zustand (lightweight, geen Redux overhead).

### API Communicatie
Axios met interceptors voor JWT refresh. Alle API calls via modules in `frontend/src/api/` (centrale client in `api/api.ts`).

### Design System
Zie [DESIGN.md](../docs/architecture/DESIGN.md). Theme in `frontend/src/theme.ts`. Gebruik shared components uit `components/common/`.

### Routing
React Router v6.

### Forms
React Hook Form + Zod voor validatie.

---

## Environment Variables

### Backend (.env)
```
DEBUG=False
SECRET_KEY=
DATABASE_URL=
REDIS_URL=
MOLLIE_API_KEY=
ENCRYPTION_KEY=          # AES-256 key voor API key encryptie
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
BITVAVO_API_URL=
PRICE_API_KEY=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
```

### Frontend (.env)
```
VITE_API_BASE_URL=
```

**Nooit** environment variables committen naar git. `.env` staat altijd in `.gitignore`.

---

## API Conventies

- REST API op `/api/v1/`
- JSON responses altijd met consistente structuur:
```json
{
  "data": {},
  "error": null,
  "message": ""
}
```
- Authenticatie via JWT Bearer token
- Alle endpoints vereisen authenticatie tenzij expliciet public
- Versioning via URL (`/api/v1/`, `/api/v2/`)

---

## Security Standaarden

- API keys worden NOOIT plaintext opgeslagen
- Encryptie: AES-256-GCM via Python `cryptography` library
- Encryption key staat in environment variable, nooit in code
- HTTPS overal, geen HTTP in productie
- CORS strict geconfigureerd
- Rate limiting op auth endpoints
- Audit log voor: login, logout, API key aanmaken/verwijderen, belastingberekening uitvoeren
