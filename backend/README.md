# Backend

Django + Django REST Framework API voor Vermogenspeil.

## Structuur

```
backend/
├── config/              # Django project settings
│   └── settings/        # base, development, production
├── apps/
│   ├── accounts/        # Auth, users, 2FA
│   ├── portfolio/       # Portfolios, assets, posities
│   ├── integrations/    # Broker koppelingen (Bitvavo, DEGIRO)
│   ├── tax/             # Box 3 berekeningen
│   ├── pricing/         # Koersdata
│   ├── payments/        # Mollie integratie
│   └── snapshots/       # Peildatum snapshots
├── requirements/
├── manage.py
└── Dockerfile
```

Zie [STACK.md](../docs/architecture/STACK.md) voor details.

## Lokale ontwikkeling

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements/development.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

- Admin: http://127.0.0.1:8000/admin/
- Health check: http://127.0.0.1:8000/api/v1/health/

Zonder `DATABASE_URL` in `.env` wordt SQLite gebruikt. Voor PostgreSQL (Railway): zet `DATABASE_URL` in `.env`.
