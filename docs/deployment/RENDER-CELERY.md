# Render — Celery, Valkey (Redis) en free tier

## Wat je zag in de Blueprint-sync

| Stap | Status | Betekenis |
|------|--------|-----------|
| `vermogenspeil-redis` (Valkey) | ✅ | Key Value / Redis werkt (25 MB free) |
| `vermogenspeil-api` (web) | ✅ | API deployed |
| `vermogenspeil-celery-worker` | ❌ | **"service type is not available for this plan"** |
| `vermogenspeil-celery-beat` | ❌ | Zelfde — **background workers zijn niet gratis op Render** |

De blueprint is **niet volledig mislukt** — alleen de twee worker-services. Redis + web zijn goed.

## Free-tier oplossing (huidige `render.yaml`)

Celery draait **in dezelfde Docker-container** als Gunicorn:

- Env op web: `RUN_CELERY_IN_WEB=true`
- `scripts/start.sh` start worker + beat met `--detach`, daarna Gunicorn
- `WEB_CONCURRENCY=1` en `CELERY_CONCURRENCY=1` (free = 0.05 CPU, 25 MB Redis)

**Beperkingen free web:**

- Service **slaapt** na inactiviteit → Celery slaapt mee tot de volgende HTTP-request de container wekt
- Eerste sync na slaapstand kan traag zijn (cold start)
- Geen aparte schaal voor workers

Voor MVP-testen is dit vaak genoeg. Voor productie: **Starter worker** (~$7/maand per service) of hoger.

## Wat jij nu moet doen

### 1. Blueprint opnieuw syncen

Push de nieuwe `render.yaml` (zonder `type: worker` services) en klik **Manual sync** in Render.

De sync zou nu **zonder worker-fouten** moeten slagen.

### 2. Environment variables op `vermogenspeil-api` controleren

Blueprint zou moeten zetten:

| Variabele | Bron |
|-----------|------|
| `REDIS_URL` | `vermogenspeil-redis` (internal URL) |
| `CELERY_BROKER_URL` | zelfde |
| `CELERY_RESULT_BACKEND` | zelfde |
| `RUN_CELERY_IN_WEB` | `true` |

Handmatig invullen (als sync ze mist):

- `CORS_ALLOWED_ORIGINS` — Vercel-URL
- `FRONTEND_URL`
- `ENCRYPTION_KEY` — zelfde waarde als lokaal `.env`
- Auth0-variabelen

**Internal Redis URL** (alleen vanaf Render-services):

`redis://red-d8eu9icp3tds73908akg:6379` — gebruik de waarde uit Dashboard → Connections → **Internal Key Value URL**, niet de external (die is geblokkeerd tenzij je IP whitelist).

### 3. Redeploy web

Na sync: **vermogenspeil-api** → Manual Deploy (of auto-deploy vanuit Git).

### 4. Logs controleren

In **vermogenspeil-api** logs bij start:

```
RUN_CELERY_IN_WEB=true — starting Celery worker + beat in background
```

### 5. Test Bitvavo-sync

In de app: Platformen → Sync. In API-logs of `/tmp/celery/worker.log` in de container zou activiteit moeten verschijnen.

## Paid tier (later): aparte workers

Als je een betaald Render-plan hebt, voeg twee services toe (niet in free blueprint):

```yaml
  - type: worker
    name: vermogenspeil-celery-worker
    runtime: docker
    plan: starter
    rootDir: backend
    dockerCommand: ./scripts/celery-worker.sh
    # ... zelfde env als web (DATABASE_URL, REDIS_URL, ENCRYPTION_KEY, Auth0)

  - type: worker
    name: vermogenspeil-celery-beat
    runtime: docker
    plan: starter
    rootDir: backend
    dockerCommand: ./scripts/celery-beat.sh
```

Zet dan op web: `RUN_CELERY_IN_WEB=false` (of verwijder de variabele).

## Lokaal

Geen wijziging nodig — `CELERY_TASK_ALWAYS_EAGER=True` in development.

## Handmatig testen

```bash
cd backend
celery -A config worker --loglevel=info
# aparte terminal:
celery -A config beat --loglevel=info
```

Peildatum-taak: `apps.snapshots.tasks.run_annual_peildatum_snapshots`
