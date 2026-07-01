# Documentatie — Vermogenspeil

Overzicht van alle projectdocumentatie. Start hier als je iets zoekt.

## Snel zoeken

| Ik wil… | Ga naar |
|---------|---------|
| Weten **wat** we bouwen | [product/REQUIREMENTS.md](./product/REQUIREMENTS.md) + [product/FSD.md](./product/FSD.md) |
| Zien **waar** we staan en wat de volgende fase is | [product/ROADMAP.md](./product/ROADMAP.md) + [development/PROGRESS.md](./development/PROGRESS.md) |
| Tech stack, mappenstructuur en API-conventies | [architecture/STACK.md](./architecture/STACK.md) |
| UI-kleuren, typografie, componenten, layouts | [architecture/DESIGN.md](./architecture/DESIGN.md) — implementatie in `frontend/src/theme.ts` |
| Fouten vermijden (belasting, security, sync) | [development/TRAPS.md](./development/TRAPS.md) |
| Een AI-sessie starten | [../CLAUDE.md](../CLAUDE.md) |
| Deployen (Render + Vercel) | [development/DEPLOYMENT.md](./development/DEPLOYMENT.md) |
| API testen (Postman) | [api/Vermogenspeil.postman_collection.json](./api/Vermogenspeil.postman_collection.json) |
| Architectuurbeslissingen vastleggen | [decisions/](./decisions/) |

---

## Mappen

### `product/` — Wat & wanneer

Business-eisen, mijlpalen en fasering.

| Bestand | Inhoud |
|---------|--------|
| [REQUIREMENTS.md](./product/REQUIREMENTS.md) | Contract-eisen, mijlpalen, modules-overzicht |
| [FSD.md](./product/FSD.md) | Volledig functioneel platformoverzicht (opdrachtgever v1.0) |
| [ROADMAP.md](./product/ROADMAP.md) | 12 fases, checklists, definition of done |

### `architecture/` — Hoe het gebouwd is

Technische keuzes en visueel design.

| Bestand | Inhoud |
|---------|--------|
| [STACK.md](./architecture/STACK.md) | Tech stack, projectstructuur, env vars, security |
| [DESIGN.md](./architecture/DESIGN.md) | Design system: kleuren, typografie, componenten |

### `development/` — Dagelijks werk

Werkwijze, valkuilen en voortgang.

| Bestand | Inhoud |
|---------|--------|
| [TRAPS.md](./development/TRAPS.md) | 11 kritieke valkuilen + commit-checklist |
| [PROGRESS.md](./development/PROGRESS.md) | Sessielog, huidige fase, openstaande taken |
| [DEPLOYMENT.md](./development/DEPLOYMENT.md) | Render + Vercel deploy-instructies |

### `api/` — API-referentie

Endpoint-documentatie per module. Wordt gevuld vanaf fase 1.2.

### `decisions/` — ADR's

Architecture Decision Records: waarom een keuze is gemaakt.

---

## Root-bestanden

| Bestand | Waarom in root |
|---------|----------------|
| [../README.md](../README.md) | Projectentry voor GitHub en nieuwe developers |
| [../CLAUDE.md](../CLAUDE.md) | Agent-context (Cursor/Claude leest dit automatisch) |
| [../MijnVermogen-Gratis-v4.html](../MijnVermogen-Gratis-v4.html) | Visuele UI-referentie gratis tier |
| [../MijnVermogen-Premium-v4.html](../MijnVermogen-Premium-v4.html) | Visuele UI-referentie premium tier |
