# DEPLOYMENT.md — Render & Vercel

Stap-voor-stap instructies voor fase 1.4. Backend + PostgreSQL op **Render** (gratis tier), frontend op **Vercel** (gratis).

---

## Overzicht

| Component  | Platform           | Root directory | URL (voorbeeld)                          |
| ---------- | ------------------ | -------------- | ---------------------------------------- |
| Django API | Render Web Service | `backend/`     | `https://vermogenspeil-api.onrender.com` |
| PostgreSQL | Render Postgres    | —              | intern via `DATABASE_URL`                |
| React SPA  | Vercel             | `frontend/`    | `https://jouw-app.vercel.app`            |

### Render free tier — weet dit van tevoren

- **Web service:** slaapt na ~15 min zonder verkeer; eerste request duurt ~30–60 sec (cold start).
- **PostgreSQL free:** database verloopt na **90 dagen** — daarna upgrade naar betaald plan of nieuwe DB aanmaken. Voor productie later een betaald plan nemen.

---

## Methode A — Blueprint (aanbevolen, snelst)

De repo bevat `render.yaml` — één klik voor API + database.

### Stap 1 — Code op GitHub

Push alles naar `main`, inclusief `render.yaml` en `backend/Dockerfile`.

### Stap 2 — Render Blueprint

1. Ga naar [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints)
2. **New Blueprint Instance**
3. Koppel je GitHub account en kies repo `vermogenspeil`
4. Render toont de resources uit `render.yaml`:
   - `vermogenspeil-db` (PostgreSQL)
   - `vermogenspeil-api` (Docker web service)
5. Bij `CORS_ALLOWED_ORIGINS`: laat leeg of zet tijdelijk `https://placeholder.vercel.app` — vul je echte Vercel URL in na stap 4 hieronder
6. Klik **Apply**

Wacht tot beide services **Live** zijn (~5–10 min eerste build).

### Stap 3 — Health check

Open in browser (vervang met jouw Render URL):

```
https://vermogenspeil-api.onrender.com/api/v1/health/
```

Verwacht:

```json
{
  "data": { "status": "ok" },
  "error": null,
  "message": "Vermogenspeil API is running"
}
```

> **Eerste keer traag?** Free tier cold start — wacht even en refresh.

### Stap 4 — Vercel frontend

1. [vercel.com/new](https://vercel.com/new) → import repo `vermogenspeil`
2. **Root Directory:** `frontend`
3. Environment variable:

   | Variable            | Waarde                                          |
   | ------------------- | ----------------------------------------------- |
   | `VITE_API_BASE_URL` | `https://vermogenspeil-api.onrender.com/api/v1` |

   Gebruik je **eigen** Render URL. Geen trailing slash.

4. **Deploy** → noteer je Vercel URL (bv. `https://vermogenspeil.vercel.app`)

### Stap 5 — CORS + FRONTEND_URL op Render

1. Render Dashboard → **vermogenspeil-api** → **Environment**
2. Zet `CORS_ALLOWED_ORIGINS` op je Vercel URL:
   ```
   https://vermogenspeil.vercel.app
   ```
   Exact: `https://`, geen trailing slash.
3. Zet **`FRONTEND_URL`** op dezelfde Vercel URL (voor links in verificatie-e-mails).
4. Service redeployt automatisch.

### Stap 6 — Superuser (optioneel)

Render → **vermogenspeil-api** → **Shell**:

```bash
python manage.py createsuperuser
```

Admin: `https://vermogenspeil-api.onrender.com/admin/`

---

## Methode B — Handmatig via Render Dashboard

Als je geen Blueprint wilt gebruiken.

### B1 — PostgreSQL

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **PostgreSQL**
2. Name: `vermogenspeil-db`, Plan: **Free**, Region: **Frankfurt** (EU)
3. **Create Database** → noteer **Internal Database URL**

### B2 — Django Web Service

1. **New +** → **Web Service** → koppel GitHub repo
2. Settings:

   | Veld              | Waarde              |
   | ----------------- | ------------------- |
   | Name              | `vermogenspeil-api` |
   | Region            | Frankfurt           |
   | Root Directory    | `backend`           |
   | Runtime           | **Docker**          |
   | Plan              | Free                |
   | Health Check Path | `/api/v1/health/`   |

3. **Environment Variables:**

   | Variable                 | Waarde                                                 |
   | ------------------------ | ------------------------------------------------------ |
   | `DJANGO_SETTINGS_MODULE` | `config.settings.production`                           |
   | `DEBUG`                  | `False`                                                |
   | `SECRET_KEY`             | Genereer lokaal (zie onder)                            |
   | `DATABASE_URL`           | Plak **Internal Database URL** van je Postgres service |

   SECRET_KEY genereren:

   ```powershell
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   > `ALLOWED_HOSTS` hoef je **niet** handmatig te zetten — Render vult `RENDER_EXTERNAL_HOSTNAME` automatisch in; `production.py` leest die.

4. **Create Web Service** → wacht op deploy
5. Test health endpoint (zie Methode A stap 3)
6. Vercel + CORS (zie Methode A stap 4–5)

---

## Vercel — samenvatting

| Veld                | Waarde                                          |
| ------------------- | ----------------------------------------------- |
| Root Directory      | `frontend`                                      |
| Framework           | Vite (via `vercel.json`)                        |
| `VITE_API_BASE_URL` | `https://<jouw-render-api>.onrender.com/api/v1` |

---

## CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml` — draait bij push/PR naar `main`. Geen Render/Vercel config nodig; alleen code moet groen zijn vóór deploy.

---

## Checklist fase 1.4

- [ ] Code gepusht naar GitHub (`render.yaml` included)
- [ ] Render PostgreSQL live
- [ ] Render web service live, health endpoint OK
- [ ] Vercel frontend live
- [ ] `VITE_API_BASE_URL` wijst naar Render API
- [ ] `CORS_ALLOWED_ORIGINS` bevat Vercel URL
- [ ] GitHub Actions CI groen op `main`

**Definition of done:** Beide apps live, frontend kan de productie-API bereiken via HTTPS.

---

## Troubleshooting

**Deploy faalt / service crasht**

- Render → **Logs**. Meestal: ontbrekende `SECRET_KEY`, verkeerde `DATABASE_URL`, of DB en web service in **verschillende regions**.

**502 / Application failed to respond**

- Cold start op free tier — wacht 60 sec en probeer opnieuw.
- Check logs voor migrate/collectstatic errors.

**CORS errors in browser**

- `CORS_ALLOWED_ORIGINS` moet exact de Vercel origin zijn (`https://...`, geen slash aan het eind).

**Health check faalt op Render**

- Pad moet `/api/v1/health/` zijn (met trailing slash).
- Service moet luisteren op `0.0.0.0:$PORT` — `scripts/start.sh` doet dit al via Gunicorn.

**Database connection error**

- Gebruik de **Internal** Database URL als web service en DB op Render staan.
- Zelfde region (Frankfurt) voor beide services.

**Migrate faalt na custom User model (InconsistentMigrationHistory)**

- De oude Django default `auth_user` tabel botst met het nieuwe `accounts_user` model.
- Oplossing op staging (alleen testdata): Render Postgres **Reset** of nieuwe DB, daarna opnieuw deployen (`migrate` in `start.sh`).
- Superuser opnieuw aanmaken met **e-mail** (niet username): `createsuperuser` via External Database URL lokaal.
- Lokaal: verwijder `backend/db.sqlite3` en run `python manage.py migrate` opnieuw.

**Static files / admin styling**

- `collectstatic` draait bij elke deploy in `start.sh`. WhiteNoise serveert static files.

---

## Lokale productie-test (optioneel)

```powershell
cd backend
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
$env:SECRET_KEY="local-prod-test-key-min-50-chars-long-enough"
$env:DATABASE_URL="postgres://..."
docker build -t vermogenspeil-api .
docker run -p 8000:8000 -e SECRET_KEY -e DATABASE_URL -e RENDER_EXTERNAL_HOSTNAME=localhost vermogenspeil-api
```
