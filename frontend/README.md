# Frontend

React + TypeScript (Vite) frontend voor Vermogenspeil.

## Structuur

```
frontend/
├── src/
│   ├── components/      # common, auth, portfolio, tax
│   ├── api/             # Axios client + endpoint modules (auth, health, …)
│   ├── theme.ts         # Chakra theme — kleuren, styling, component variants
│   ├── components/common/  # Kicker, MoneyText, FiscalCard, layouts
│   ├── pages/
│   ├── routes/
│   ├── hooks/
│   ├── types/
│   └── utils/
└── public/
```

Zie [DESIGN.md](../docs/architecture/DESIGN.md). Alles in `frontend/src/theme.ts`.

## Lokale ontwikkeling

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

App draait op http://localhost:5173
