# REQUIREMENTS.md — Functionele Eisen Vermogenspeil / MijnVermogen

## Documenthiërarchie

| Document | Rol |
|----------|-----|
| **Dit bestand** | Contract-eisen, mijlpalen, acceptatiecriteria |
| [FSD.md](./FSD.md) | Volledig functioneel platformoverzicht (opdrachtgever, v1.0) |
| [ROADMAP.md](./ROADMAP.md) | Ontwikkel-fases en definition of done |
| [DESIGN.md](../architecture/DESIGN.md) | Design system (implementatie: `frontend/src/theme.ts`) |

**Visuele referenties (repo root):**
- `MijnVermogen-Gratis-v4.html` — gratis tier UI/UX
- `MijnVermogen-Premium-v4.html` — premium tier UI/UX

**Productnaam:** opdrachtgever gebruikt **MijnVermogen**; repository/technisch **Vermogenspeil**. Zelfde product.

---

## Doel van het platform

MijnVermogen is een Nederlands SaaS-platform waar beleggers al hun investeringen centraal bijhouden — aandelen, ETF's, crypto, edelmetalen — verspreid over brokers, exchanges en banken. Data via API, CSV, PDF-jaaroverzicht en handmatige invoer.

**Premium** voegt doorlopend fiscaal inzicht toe: Box 3 forfaitair + tegenbewijsregeling (werkelijk rendement).

### Juridische positionering (FSD 1.4)

- Platform biedt **fiscaal inzicht**, geen fiscaal advies
- Geen aangifte-besluiten namens gebruiker
- UI-copy: altijd "fiscaal inzicht", nooit "fiscaal advies"
- Disclaimers in: profiel, fiscale views, export-PDF, algemene voorwaarden

### Belasting-scope

| Fase | Inhoud | Status |
|------|--------|--------|
| Fase 1 (nu) | Box 3 forfaitair t/m belastingjaar 2027 | In scope |
| Fase 2 (2028+) | Vermogensaanwasbelasting | Architectuur voorbereiden, niet bouwen |
| Fase 3 (toekomst) | Vermogenswinstbelasting | Out of scope |

---

## Platformmodules (FSD)

Volledige specificatie per module: [FSD.md](./FSD.md).

| # | Module | Tier |
|---|--------|------|
| 1 | Dashboard | Gratis + Premium |
| 2 | Portefeuille | Gratis (basis) / Premium (uitgebreid) |
| 3 | Transacties | Gratis + Premium |
| 4 | Belastingpositie | Premium |
| 5 | Werkelijk rendement (tegenbewijs) | Premium |
| 6 | Overig vermogen (vastgoed, schulden, bank) | Premium |
| 7 | Mijn platformen | Gratis + Premium |
| 8 | Platform toevoegen | Gratis + Premium |
| 9 | Transactie handmatig toevoegen | Gratis + Premium |
| 10 | Platform-vergelijker | Gratis |
| 11 | Profiel & accountbeheer | Gratis + Premium |
| 12 | Abonnement & upgrade | Gratis + Premium |

**Layouts:** publieke pagina's (home, login, register) gescheiden van app-shell met sidebar (dashboard en app-modules). Zie DESIGN.md.

---

## Gebruikerstiers

### Mapping contract ↔ FSD

| Contract (ROADMAP) | FSD | Prijs (FSD) |
|--------------------|-----|-------------|
| Gratis tier | Gratis | €0 |
| Premium Basis | Premium (fiscaal + portfolio+) | €49,99/jaar |
| Premium Pro | Premium + PDF export / analytics | Zelfde premium-laag, extra features |

> FSD beschrijft **twee** tiers (Gratis/Premium). Contract/ROADMAP splitst premium in Basis/Pro voor feature gating en facturatie. Implementatie: één premium-flag + feature flags voor Pro.

### Gratis tier (FSD samenvatting)

- Onbeperkt platformen, posities, transacties
- Dashboard: totaal vermogen, rendement, allocatie
- Portefeuille: holdings, basis rendement
- Platform-koppelingen (Bitvavo API, DEGIRO CSV, handmatig)
- Platform-vergelijker
- Premium-modules zichtbaar met slotje/crown — leiden naar upgrade

### Premium tier (FSD samenvatting)

- Alles van Gratis
- Box 3 forfaitair + tegenbewijsregeling (OWR-rapport)
- Belastingpositie doorlopend actueel
- Uitgebreide portefeuille-analytics (cost basis, dividend, fees, peildatum-waarden)
- Overig vermogen: vastgoed, schulden, banktegoeden peildatum
- Fiscaal partner (+€10/jaar in FSD)
- 2FA verplicht
- PDF belastingrapport (Pro)

---

## Auth & account (FSD hoofdstuk 2 — MVP)

- Registratie: email, wachtwoord (min. 12 tekens), voornaam, AV-checkbox
- Emailverificatie (token 24u); banner tot bevestigd; blokkade op koppelingen/betaling/exports
- Login: email + wachtwoord; "Onthoud mij" (30d vs 7d sessie)
- 2FA TOTP: optioneel gratis, **verplicht premium**; backup codes
- Wachtwoord reset: token 1u; alle sessies invalideren; geen 2FA bypass
- Brute-force: max 5 pogingen/15min; lock 30min; CAPTCHA na 3 fails
- Account verwijderen: soft-delete 30d, daarna GDPR-wipe
- Onboarding na eerste login: 3 schermen + CTA premium + platform koppelen

Details: [FSD.md §2](./FSD.md)

---

## Mijlpaal 1 — Eerste maand (€1.000)

Acceptatiecriteria:
- Werkende ontwikkelomgeving opgezet
- Repository structuur correct opgezet
- Opdrachtgever heeft toegang tot repository vanaf dag één
- Aantoonbare voortgang zichtbaar in git
- Wekelijkse commits

---

## Mijlpaal 2 — Testbare MVP (€2.000)

### Auth & Accounts
- Registratie met emailverificatie
- Login met 2FA (TOTP)
- Wachtwoord reset flow
- Email verificatie

### Portfolio Module (gratis tier)
- Dashboard met totaaloverzicht vermogen
- Asset allocatie weergave
- Rendement berekening (direct + indirect)
- Inleg tracking
- Handmatige invoer voor alle asset types

### Platform Koppelingen MVP
- **Bitvavo**: server-side API integratie, encrypted key storage
- **DEGIRO**: CSV upload importer met deduplicatie

### Koersdata
- Externe koers API voor aandelen en ETFs
- Publieke crypto koersen
- Peildatum berekeningen (1 januari)

### Peildatum Snapshot
- Automatische vastlegging portfoliowaarde op 1 januari 00:00 CET
- Voor alle gekoppelde accounts tegelijk
- Immutable — kan niet achteraf worden aangepast

### Belastingberekening (premium)
- Box 3 forfaitair stelsel berekening
- Tegenbewijsregeling (werkelijk rendement)
- Uitsplitsing per vermogenscategorie (banktegoeden, beleggingen, overig)
- Correcte heffingsvrij vermogen toepassing
- Resultaat exporteerbaar

### Betalingen
- Mollie integratie (iDEAL + creditcard)
- Premium abonnementsflow
- Webhook verwerking voor betalingsstatus
- Automatische tier upgrade/downgrade

### Testomgeving
- Acceptatie-omgeving voor meerdere testgebruikers tegelijk
- End-to-end testbaar door opdrachtgever

### Documentatie MVP
- Technische documentatie
- Setup handleiding

---

## Mijlpaal 3 — Lanceringsgereed (€3.000)

### Volledige Platform Koppelingen
- Bitvavo (API)
- DEGIRO (CSV)
- Meesman (PDF jaaropgave parser)
- Interactive Brokers (CSV/API)
- Overige brokers via CSV import
- Handmatige invoer edelmetalen (goud, zilver)
- Handmatige invoer spaargeld
- Handmatige invoer overig vastgoed/bezittingen

### Premium Tiers
- Basis tier: feature gating correct
- Pro tier: feature gating correct
- Upgrade/downgrade flows werken correct

### Productieomgeving
- Draait op accounts van opdrachtgever
- SSL/HTTPS
- Monitoring actief
- Geautomatiseerde backups
- Domein en DNS correct geconfigureerd

### Security
- AES-256 encrypted opslag van alle API keys
- Gescheiden key management
- Audit logging voor alle gevoelige acties
- Security vereisten uit FSD volledig nageleefd — zie [FSD.md §23](./FSD.md)

### GDPR/AVG
- Data-inzageverzoeken technisch implementeerbaar
- Data-verwijderverzoeken technisch implementeerbaar
- Cookieverklaring correct ingebouwd
- Privacyverklaring correct ingebouwd

### Email Service
- Transactionele emails (registratie, betalingen, notificaties)
- Optionele nieuwsbrief integratie

### Acceptatietest
- Geslaagde test door aangewezen testgebruikers
- Alle kernflows werken zonder blokkerende issues

### Overdracht
- Volledige toegangsoverdracht repositories, hosting, domeinen, API keys
- Technische documentatie compleet
- Deployment instructies compleet
- Onderhoudshandleiding compleet
- Operationele runbook compleet

---

## Belastinglogica — Kritische Details

Zie ook [FSD.md §17](./FSD.md) en [TRAPS.md](../development/TRAPS.md).

### Box 3 Forfaitair Stelsel
- Peildatum: 1 januari 00:00:00 **CET**
- Heffingsvrij vermogen: jaarlijks te controleren (2025: €57.000 per persoon)
- Drie vermogenscategorieën met eigen forfaitaire rendementen:
  1. Banktegoeden
  2. Beleggingen en overige bezittingen
  3. Schulden
- Berekening: (grondslag sparen en beleggen) × forfaitair rendement × belastingtarief (36%)

### Tegenbewijsregeling (Werkelijk Rendement)
- Gebruiker mag werkelijk rendement bewijzen als dat lager is dan forfaitair
- Werkelijk rendement = directe opbrengsten + indirecte opbrengsten (waardestijging)
- Ongerealiseerde verliezen mogen worden meegenomen
- Complexe berekening — unit tests verplicht voor elk scenario

### Peildatum Snapshot Vereisten
- Exact 1 januari 00:00:00 CET (niet UTC)
- Alle gekoppelde accounts tegelijk
- Immutable na vastlegging
- Basis voor belastingberekening — mag nooit worden overschreven

---

## Niet in scope (bouwen alleen op verzoek)

- Mobiele app
- Pensioenmodule
- Hypotheekmodule
- Internationale belastingwetgeving
- Meerdere gebruikers per account (team features)
- Vermogensaanwasbelasting (2028+) — alleen architectuur voorbereiden
- Vermogenswinstbelasting — toekomst

Volledige FSD out-of-scope lijst: [FSD.md](./FSD.md) (hoofdstuk 25 indien aanwezig in bron-document).
