# Verbox

Nederlandse fintech webapplicatie voor beleggers: volledig vermogen tracken en Box 3 belastingaangiftes voorbereiden.

> Productnaam: **Verbox**. Brand-assets: `frontend/public/brand/`.

## Projectstructuur

```
vermogenspeil/
├── backend/          # Django + Django REST Framework
├── frontend/         # React + TypeScript (Vite)
├── docs/             # Alle projectdocumentatie
│   ├── product/      # Eisen & roadmap
│   ├── architecture/ # Stack & design
│   └── development/  # Traps, voortgang, werkwijze
└── .github/          # CI/CD workflows
```

Zie [docs/architecture/STACK.md](./docs/architecture/STACK.md) voor de volledige architectuur.

## Vereisten

- Python 3.12+
- Node.js 20+
- PostgreSQL (lokaal of via Render)

## Lokale ontwikkeling

> Backend en frontend worden opgezet in fase 1.2 en 1.3. Instructies volgen zodra bootstrap klaar is.

### Backend (fase 1.2)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements/development.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend (fase 1.3)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Deployment

Zie [docs/development/DEPLOYMENT.md](./docs/development/DEPLOYMENT.md) voor Render (Django + PostgreSQL) en Vercel (React).

## Documentatie

**Start hier:** [docs/README.md](./docs/README.md)

| Categorie | Bestanden |
|-----------|-----------|
| Product | [REQUIREMENTS](./docs/product/REQUIREMENTS.md) · [ROADMAP](./docs/product/ROADMAP.md) |
| Architectuur | [STACK](./docs/architecture/STACK.md) · [DESIGN](./docs/architecture/DESIGN.md) |
| Development | [TRAPS](./docs/development/TRAPS.md) · [PROGRESS](./docs/development/PROGRESS.md) · [DEPLOYMENT](./docs/development/DEPLOYMENT.md) |

## Licentie

Proprietary — alle rechten voorbehouden.
