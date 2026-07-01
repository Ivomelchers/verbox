# ROADMAP.md — Fases en Voortgang

**Laatste sync met `docs/development/PROGRESS.md`:** 1 juni 2026

## Overzicht

| Fase | Naam | Mijlpaal | Status |
|------|------|----------|--------|
| 1 | Project Setup | - | ✅ |
| 2 | Auth & Accounts | MVP | ✅ |
| 3 | Portfolio Module | MVP | ✅ |
| 4 | Broker Koppelingen | MVP | ✅ |
| 5 | Koersdata & Peildatum | MVP | ✅ |
| 6 | Belastingberekening | MVP | ✅ |
| 7 | Betalingen (Mollie) | MVP | ⏸️ na MVP |
| 8 | Frontend MVP | MVP | 🔄 |
| 9 | MVP Afronden & Testen | Mijlpaal 2 | 🔄 |
| 10 | Extra Koppelingen | Launch | 🔲 |
| 11 | Security & GDPR | Launch | 🔲 |
| 12 | Productie & Overdracht | Mijlpaal 3 | 🔲 |

Status: 🔲 Niet gestart | 🔄 Bezig | ✅ Klaar | ⏸️ Bewust uitgesteld

**Huidige focus:** fase **9** (acceptatie) + GDPR account verwijderen; fase **7** pas na MVP-acceptatie.

---

## Fase 1 — Project Setup

### 1.1 Repository & Structuur
- [x] Repository aangemaakt op opdrachtgever account
- [x] Folder structuur opgezet conform STACK.md
- [x] `.gitignore` correct geconfigureerd
- [x] README.md aangemaakt

**Definition of done:** Repository toegankelijk voor opdrachtgever, structuur klopt.

### 1.2 Backend Bootstrap
- [x] Django project aangemaakt
- [x] Django apps aangemaakt (accounts, portfolio, integrations, tax, pricing, payments, snapshots)
- [x] Settings gesplitst (base/development/production)
- [x] Requirements files aangemaakt
- [x] Database verbinding werkend (PostgreSQL via DATABASE_URL)
- [x] Django admin toegankelijk

**Definition of done:** `python manage.py runserver` werkt lokaal zonder errors.

### 1.3 Frontend Bootstrap
- [x] React project aangemaakt met TypeScript (Vite)
- [x] Chakra UI geinstalleerd en geconfigureerd
- [x] React Router geconfigureerd
- [x] Axios geconfigureerd met base URL
- [x] Basis pagina structuur (routes)

**Definition of done:** `npm run dev` werkt lokaal, Chakra UI thema actief.

### 1.4 CI/CD & Deployment
- [x] Dockerfile + start script voor Django (Gunicorn)
- [x] Render configuratie (`render.yaml`, health check)
- [x] Vercel configuratie (`vercel.json`, SPA rewrites)
- [x] GitHub Actions CI pipeline
- [x] Deployment documentatie
- [x] Render PostgreSQL database aangemaakt
- [x] Django deployed op Render
- [x] Vercel project aangemaakt
- [x] React app deployed op Vercel
- [x] Environment variables geconfigureerd in cloud

**Definition of done:** Beide apps live op Render/Vercel, verbonden met productie database.

---

## Fase 2 — Auth & Accounts

### 2.1 User Model
- [x] Custom User model aangemaakt (email als username)
- [x] Profielvelden (naam, belastingjaar instellingen)
- [x] Migraties aangemaakt

**Definition of done:** User model in database, geen Django default auth.

### 2.2 Registratie & Email Verificatie
- [x] Registratie endpoint
- [x] Email verificatie token aanmaken
- [x] Verificatie email versturen
- [x] Verificatie link verwerken
- [x] Gebruiker kan niet inloggen voor verificatie (JWT — fase 2.3)

**Definition of done:** Registratie flow volledig werkend, email ontvangen en geverifieerd.

### 2.3 Login & Auth0 tokens
- [x] Login endpoint (Django proxy → Auth0)
- [x] Auth0 access + refresh + id_token
- [x] Token refresh endpoint
- [x] Client-side logout (Auth0 tokens)

**Definition of done:** Login geeft Auth0 tokens terug, refresh werkt, `id_token` valideert in Django.

### 2.4 2FA (Auth0 MFA)
- [x] MFA enroll endpoint (QR via Auth0)
- [x] MFA verificatie bij login (Auth0 challenge)
- [x] MFA reset flow (Management API)
- [x] MFA status endpoint

**Definition of done:** Google Authenticator werkt via Auth0 MFA.

### 2.5 Wachtwoord Reset
- [x] Reset aanvraag (email invoeren)
- [x] Reset email versturen
- [x] Reset token verwerken (gehasht, 1u geldig)
- [x] Nieuw wachtwoord instellen (via Auth0 API)
- [x] 2FA vereist na reset (niet bypass!)

**Definition of done:** Volledige reset flow werkt, 2FA niet omzeild.

---

## Fase 3 — Portfolio Module

### 3.1 Portfolio & Asset Models
- [x] Portfolio model
- [x] Asset model met VermogensCategorie
- [x] Positie model
- [x] Transactie model
- [x] UserOwnedQuerySet voor alle modellen

**Definition of done:** Modellen in database, admin werkend.

### 3.2 Portfolio CRUD API
- [x] Portfolio aanmaken/ophalen/updaten/verwijderen (list + detail + transacties)
- [x] Asset aanmaken (handmatig)
- [x] Fiscale categorie per asset (`PATCH .../category/`)
- [x] Positie beheren (via sync)
- [x] Transactie toevoegen (via sync, deduplicatie hash)

**Definition of done:** API endpoints werkend, Postman collection getest.

### 3.3 Rendement Berekening
- [x] Totaal rendement (kostprijs: inleg vs huidige waarde)
- [x] Dashboard toont unrealized return %
- [x] YTD / marktwaardering op dashboard
- [ ] Uitgebreid rendement per periode (optioneel post-MVP)

**Definition of done:** Berekeningen kloppen, unit tests slagen.

### 3.4 Handmatige Invoer
- [x] Handmatig asset toevoegen
- [x] Handmatig transactie toevoegen
- [x] Edelmetalen / categorie via asset type + `VermogensCategorie`

**Definition of done:** Gebruiker kan assets handmatig invoeren.

---

## Fase 4 — Broker Koppelingen

### 4.1 PlatformAdapter Base
- [x] Abstracte PlatformAdapter klasse
- [x] Encrypted API key opslag (AES-256-GCM)
- [x] Sync status model
- [x] Error handling standaard

**Definition of done:** Base class aangemaakt, encryptie getest.

### 4.2 Bitvavo Integratie
- [x] Bitvavo API client
- [x] API key opslaan (encrypted)
- [x] Portfolio ophalen via Bitvavo API
- [x] Transacties ophalen
- [x] Celery sync task (eager lokaal/CI, Redis in productie)

**Definition of done:** Bitvavo sync werkt, data zichtbaar in portfolio.

### 4.3 DEGIRO CSV Import
- [x] CSV parser voor DEGIRO export format
- [x] Deduplicatie via transactie hash
- [x] Foutafhandeling bij verkeerd formaat
- [x] Upload endpoint + fixture `backend/fixtures/degiro/sample-transactions.csv`

**Definition of done:** DEGIRO CSV upload werkt, duplicaten worden herkend.

---

## Fase 5 — Koersdata & Peildatum

### 5.1 Koers API Integratie
- [x] PriceService interface
- [x] Externe koers API koppeling (aandelen/ETFs via Yahoo/yfinance)
- [x] Crypto koersen (publieke Bitvavo ticker)
- [x] Redis cache (15 min TTL real-time; historisch cache-key voorbereid)

**Definition of done:** Koersen worden opgehaald en gecached.

### 5.2 Peildatum Snapshot
- [x] PeilDatumSnapshot model (immutable)
- [x] Celery task voor automatische snapshot (1 jan 00:00 CET)
- [x] Handmatige trigger voor testen
- [x] Tijdzone correctie (CET niet UTC)
- [x] Unit tests voor tijdzone

**Definition of done:** Snapshot wordt aangemaakt op juiste tijdstip, kan niet worden overschreven.

### 5.3 Peildatum historisch (1 januari)
- [x] Historische koersen op peildatum (niet alleen waarde op vastlegmoment)
- [x] `fiscale_category` + `box3_totals` in snapshot payload
- [x] Unit tests `test_peildatum_historical`

**Definition of done:** Snapshot op 1 jan gebruikt historische waardering per positie.

---

## Fase 6 — Belastingberekening

### 6.1 Forfaitair Stelsel
- [x] Forfaitair berekening (6 stappen BD 2026)
- [x] `TaxYearParameter` in database
- [x] Categorie splitsing (B/O/S) + handmatige banktegoeden
- [x] Heffingsvrij vermogen + fiscaal partner
- [x] Unit tests (o.a. BD-voorbeeld €4.667)

**Definition of done:** Berekening klopt met officiële belastingdienst berekening.

### 6.2 Werkelijk rendement
- [x] Werkelijk rendement (waardemutatie, dividend, huur, bijtelling, rente schuld)
- [x] Vergelijking forfaitair vs werkelijk (laagste bedrag)
- [x] Premium-gate (`PREMIUM_UNLOCKED_FOR_ALL` pre-launch)
- [x] Unit tests

**Definition of done:** Werkelijk rendement en vergelijking beschikbaar op `/belasting`.

### 6.3 Belastingrapport
- [x] JSON-rapport API
- [x] PDF export (`?export=pdf`)
- [x] Posities peildatum + huidig in PDF

**Definition of done:** Rapport downloadbaar als PDF met onderbouwing.

### 6.4 Box 3-invoer (bank, partner)
- [x] `Box3BankBalance` + CRUD
- [x] Fiscaal partner (`PATCH /auth/me/`)
- [x] UI op `/belasting`

### 6.5 Vastgoed & schulden
- [x] `Box3Debt`, `Box3RealEstate`, bijtelling
- [x] UI: koppeling schuld ↔ vastgoed, huurwaarde, dagen

### 6.6 Rapport-detail
- [x] PDF-posities en bijtelling-kolom vastgoed
- [x] Geen roadmap-/fase-teksten meer in gebruikers-UI (productie-copy)

---

## Fase 7 — Betalingen (Mollie)

> **⏸️ Uitgesteld** tot MVP-acceptatie (zie PROGRESS.md). Pre-launch: `PREMIUM_UNLOCKED_FOR_ALL=true`.

### 7.1 Mollie Setup
- [ ] Mollie client geconfigureerd
- [ ] Test keys werkend
- [ ] Productie keys klaar (bij lancering)

### 7.2 Abonnement Flow
- [ ] Abonnement aanmaken (Basis/Pro)
- [ ] iDEAL betaling flow
- [ ] Webhook endpoint
- [ ] Webhook verificatie bij Mollie (niet vertrouwen op body)
- [ ] Tier activatie na betaling
- [ ] Upgrade/downgrade flow

**Definition of done:** Betaling via iDEAL werkt, tier wordt correct geactiveerd.

---

## Fase 8 — Frontend MVP

### 8.1 Auth Paginas
- [x] Login pagina
- [x] Registratie pagina
- [x] Email verificatie pagina
- [x] 2FA setup pagina (Auth0 enroll + OTP challenge)
- [x] Wachtwoord reset pagina

### 8.2 Dashboard
- [x] Totaal vermogen overzicht (live API, marktwaarde/kostprijs)
- [x] Categorie-verdeling (crypto/beleggingen)
- [x] Platformen op dashboard
- [x] Portefeuille- en transactiepagina's
- [x] Asset allocatie chart (vermogensverdeling op dashboard)
- [x] Rendement overzicht (unrealized + YTD)
- [x] Recent activiteit feed (laatste transacties)

### 8.3 Portfolio Beheer
- [x] Portfoliolijst + dashboard posities
- [x] Asset toevoegen (handmatig)
- [x] Transactie toevoegen
- [x] Fiscale categorie dropdown per positie
- [x] Broker koppelen (Bitvavo)
- [x] CSV upload (DEGIRO)

### 8.4 Belasting Pagina
- [x] Peildatum vastleggen + Box 3-summary
- [x] Forfaitair tussenstappen
- [x] Werkelijk rendement + vergelijking
- [x] Handmatige bank/schuld/vastgoed
- [x] PDF-download

### 8.5 Account & Instellingen
- [x] Profiel + fiscaal partner
- [x] 2FA beheren
- [ ] Abonnement beheren (wacht op fase 7)
- [x] Account verwijderen (GDPR soft-delete)

### 8.6 Onboarding
- [x] 3-stappen flow `/onboarding`
- [x] `onboarding_completed_at` + API

---

## Fase 9 — MVP Afronden & Testen (Mijlpaal 2)

- [x] `ROADMAP.md` gesynchroniseerd met PROGRESS.md
- [ ] Acceptatiescenario’s gedocumenteerd (BD €4.667, demo vs. echt)
- [ ] End-to-end test door opdrachtgever (Ivo/Frank)
- [ ] Celery + Redis op Render (sync + snapshot 1 jan)
- [ ] Alle MVP acceptatiecriteria gecontroleerd
- [ ] Mijlpaal 2 factuur verstuurd

---

## Fase 10 — Extra Koppelingen (Launch)

- [ ] Meesman PDF jaaropgave parser
- [ ] Interactive Brokers CSV import
- [ ] Overige brokers CSV template
- [ ] Edelmetalen handmatige invoer uitbreiden

---

## Fase 11 — Security & GDPR (Launch)

- [ ] Security audit checklist doorlopen
- [ ] Audit logging compleet
- [ ] GDPR data-inzageverzoek flow
- [ ] GDPR data-verwijderverzoek flow
- [ ] Cookieverklaring ingebouwd
- [ ] Privacyverklaring ingebouwd

---

## Fase 12 — Productie & Overdracht (Mijlpaal 3)

- [ ] Alle accounts op naam opdrachtgever
- [ ] Productieomgeving live
- [ ] SSL/HTTPS actief
- [ ] Monitoring geconfigureerd
- [ ] Backups geconfigureerd
- [ ] Acceptatietest geslaagd
- [ ] Technische documentatie compleet
- [ ] Deployment instructies compleet
- [ ] Overdracht sessie gedaan
- [ ] Mijlpaal 3 factuur verstuurd
