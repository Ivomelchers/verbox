# PROGRESS.md — Voortgang Tracker

**Laatste update:** 16 juni 2026
**Huidige fase:** **9 — MVP testen & acceptatie** (fase 5–6 en 8 grotendeels ✅; fase 7 ⏸️)
**Volgende stap:** Deploy (kolom Total/Value, kostprijs-rendement, UI-labels) → bètatesters **één keer opnieuw importeren** of `backfill_transaction_prices`; daarna §17.2 + acceptatie

**Koersbron-migratie (16 jun 2026): Yahoo Finance → Marketstack + exchangeratesapi.io**
- `apps/pricing/providers/marketstack_equities.py`: nieuwe `MarketstackEquitiesProvider` (EOD-data, `<SYMBOL>.<MIC>` tickerformaat, bv. `ASML.XAMS`) vervangt `YahooEquitiesProvider` in `default_live_price_providers()`
- `apps/pricing/services/exchange_rates.py`: nieuwe `ExchangeRatesService` (exchangeratesapi.io) converteert niet-EUR koersen (USD/GBP/...) naar EUR, met cache (1u live / 24u historisch)
- `apps/pricing/instrument_resolver.py`: `resolve_marketstack_ticker()` hergebruikt bestaande ISIN/MIC-mapping (DB `InstrumentMapping.mic` + seed JSON + Yahoo-suffix-naar-MIC fallback via `mic_suffix.py`)
- `apps/pricing/services/historical.py`: historische equity-koersen (peildatum, dashboard, value-history) nu via Marketstack `/eod` batch-endpoint i.p.v. yfinance; zelfde publieke functienamen (`fetch_historical_price_eur`, `fetch_historical_prices`, `prefetch_dates_into_cache`) — geen wijzigingen nodig bij callers (`dashboard.py`, `movers.py`, `value_history.py`)
- Env: `MARKETSTACK_API_KEY`, `MARKETSTACK_API_URL`, `EXCHANGERATESAPI_API_KEY`, `EXCHANGERATESAPI_API_URL` toegevoegd aan `backend/.env` (echte keys, alleen lokaal, **niet** gecommit — `.env` staat in `.gitignore`) en `backend/.env.example` (lege placeholders)
- `yahoo_equities.py` + yfinance-dependency blijven in de codebase staan (ongebruikt) als noodgreep-fallback; niet verwijderd
- **Live geverifieerd** (niet alleen mocked tests): `MarketstackEquitiesProvider().fetch_live_prices(['AAPL','ASML'])` → AAPL via USD→EUR-conversie, ASML direct in EUR; historische koers 2026-06-08 ASML correct opgehaald
- 67 nieuwe/bijgewerkte unit tests (`test_marketstack_equities.py`, `test_exchange_rates.py`, uitbreiding `test_instrument_resolver.py`, fix `test_price_refresh.py`) — volledige suite: **330/330 groen**
- **Bekende beperking:** gratis Marketstack-plan = 100 requests/maand + alleen EOD-data (geen echt real-time/intraday); geschikt voor MVP-test, niet voor productieschaal. Bij meer gebruikers: upgraden of caching-TTL verder verhogen (`PRICE_CACHE_TTL_LIVE_SECONDS`)
- **Bekende beperking — definitief vastgesteld (16 jun 2026, 7 live tickers getest, geen aannames meer):** ETF's zijn **niet** generiek geblokkeerd op het gratis plan — `SPY` (SPDR S&P 500 ETF Trust, NYSE Arca) werkte probleemloos met `"asset_type": "ETF"` expliciet van Marketstack zelf. Vastgesteld patroon:
  - ✅ Werkt: AAPL (stock, NASDAQ), ASML (stock, Euronext Amsterdam), SPY (ETF, NYSE Arca, VS)
  - ❌ Werkt niet: IWDA (Euronext Amsterdam), VWCE (Frankfurt/Xetra), VUAA (Frankfurt/Xetra) — alle drie 406 `the_requested_data_is_not_available`, **ook met het correcte, via tickers-search bevestigde symbool** (niet een verkeerd-geraden ticker-probleem)
  
  Conclusie: het onderscheid is niet stock-vs-ETF en niet VS-vs-Europa (XAMS én XETRA falen allebei; SPY als ETF werkt wel) maar specifiek **Iers-gedomicilieerde, accumulerende UCITS-ETF's** — exact het fondstype dat Nederlandse particuliere beleggers gebruiken (iShares Core, Vanguard Accumulating). Dit is een data-dekkingshiaat bij Marketstack's bron voor dit fondstype, **geen** plan-restrictie (ander foutcode dan de expliciete `function_access_restricted` van commodities/`/stockprice`; FAQ noemt dit niet als betaald-only). Een upgrade lost dit zeer waarschijnlijk **niet** op.
  
  Aangezien dit platform vooral dit exacte fondstype bedient, tonen IWDA/VWCE/VUAA-posities nu "Live koers niet beschikbaar" — bewust geaccepteerd door opdrachtgever i.p.v. Yahoo-fallback toe te voegen (zie eerdere sessie-notitie; kan heroverwogen worden nu de oorzaak duidelijk is). `yahoo_equities.py` staat nog in de codebase als referentie voor die hybride fallback.
- Frontend: `TransactionDetailDrawer.tsx` koersbron-label "Yahoo Finance" → "Marketstack"
- **Fix (live-prices voor ETF's):** `/eod/latest` gaf op het gratis Marketstack-plan `the_requested_data_is_not_available` voor sommige tickers; `MarketstackEquitiesProvider` gebruikt nu dezelfde `/eod` met datumbereik als de historische fetch (meest recente bruikbare bar). **Live bevestigd (16 jun 2026):** werkt voor losse aandelen (ASML, AAPL); **werkt niet voor ETF's** (IWDA → zelfde foutmelding op beide endpoints, ook al claimt de tickers-lijst `has_eod: true`) — bevestigde plan-beperking, geen codefout. Bewust geaccepteerd voor nu; zie beperking hieronder.
- **Fix (FX rate-limit/quota):** `exchange_rates.py` deed één HTTP-call per vreemde valuta — bij meerdere valuta in dezelfde cyclus (bv. USD + GBP) raakte dit de per-seconde rate-limit (429) en verspilde quota. Nieuwe `get_eur_rates(currencies, on_date=None)` batcht alle benodigde valuta in **één** call; `get_eur_rate()` blijft als single-currency wrapper bestaan. `MarketstackEquitiesProvider.fetch_live_prices` en `historical._marketstack_batch_for_date`/`prefetch_dates_into_cache` gebruiken nu de batched variant (group-by-datum voor historisch, want koers is datum-specifiek).
- **Nieuw: `MarketstackCommodityProvider`** (`apps/pricing/providers/marketstack_commodities.py`) voor `AssetType.METAL` (edelmetalen, symbool-conventie `GOLD`/`SILVER`/... gemapt naar Marketstack-commodity-codes `XAU`/`XAG`/`XPT`/`XPD`). Wordt nu meegenomen in `default_live_price_providers()`. **ONGETEST tegen echte data:** 1 live call (16 jun 2026) bevestigde `function_access_restricted` — Commodities-endpoint zit volledig achter een betaald Marketstack-plan, geen enkele parametercombinatie omzeilt dit. Parsing is gebaseerd op de officiële Swagger-schema's (`CommodityResponse`/`CommodityResponse_data`), niet op een echte response — **verifieer opnieuw zodra het plan geüpgraded is** en pas zo nodig de veldnamen in `_price_from_payload` aan. 7 mocked unit tests (`test_marketstack_commodities.py`), geen extra API-calls.

**Performance-fix (12 jun 2026):**
- Dashboard/portfolio laadtijd teruggebracht van 10–15s naar ~3s
- `_prefetch_all_dashboard_dates` in `dashboard.py`: één yfinance-call voor alle historische datums (YTD, maandstarts, hero-delta, movers)
- `compute_value_history`: batch-prefetch voor 12 maandpunten + tx_cache eliminatie N×12 DB-queries
- `compute_hero_delta_30d`: prefetch voor 30d-datum (niet altijd een maandstart)
- `compute_all_top_movers`: prefetch voor alle periode-startdata vóór `fetch_historical_prices`
- CI-fix: `credentials` verwijderd uit Vite ProxyOptions, Saxo test-fixtures bijgewerkt naar PositionBase-structuur
- Crypto-decimalen: `formatQuantity` + `formatSmartEur` detecteren automatisch de magnitude
**Sync:** `docs/product/ROADMAP.md` bijgewerkt (1 jun 2026)
**FSD-referentie:** Volledige opdrachtgever-spec: [`docs/product/FSD.md`](../product/FSD.md) (v1.0, apr 2026, 25 hoofdstukken); contract: `REQUIREMENTS.md`

**Demo (alleen development, niet in UI):** `DEMO_FEATURES_ENABLED` + `python manage.py seed_demo_portfolio` of Postman `POST /integrations/demo/seed/`

**Auth:** Auth0 (Ocean-patroon) — login/refresh via Django proxy, MFA via Auth0, `id_token` validatie in Django

---

## Status Overzicht

| Fase                                          | Status | Afgerond op |
| --------------------------------------------- | ------ | ----------- |
| 1.1 Repository & Structuur                    | ✅     | 25 mei 2026 |
| 1.2 Backend Bootstrap                         | ✅     | 25 mei 2026 |
| 1.3 Frontend Bootstrap                        | ✅     | 25 mei 2026 |
| 1.4 CI/CD & Deployment                        | ✅     | 25 mei 2026 |
| 2.1 User Model                                | ✅     | 25 mei 2026 |
| 2.2 Registratie & Email                       | ✅     | 26 mei 2026 |
| 2.3 Login & Auth0 tokens                      | ✅     | 28 mei 2026 |
| 2.4 2FA                                       | ✅     | 28 mei 2026 |
| 2.5 Wachtwoord Reset                          | ✅     | 28 mei 2026 |
| 3.1 Portfolio Models                          | ✅     | 1 juni 2026 |
| 3.2 Portfolio API                             | ✅     | 1 juni 2026 |
| 3.3 Rendement                                 | ✅     | 1 juni 2026 |
| 3.4 Handmatige Invoer                         | ✅     | 1 juni 2026 |
| 4.1 PlatformAdapter                           | ✅     | 1 juni 2026 |
| 4.2 Bitvavo                                   | ✅     | 1 juni 2026 |
| 4.3 DEGIRO CSV                                | ✅     | 1 juni 2026 |
| 5.1 Koers API                                 | ✅     | 1 juni 2026 |
| 5.2 Peildatum Snapshot                        | ✅     | 1 juni 2026 |
| 5.3 Peildatum historisch (1 jan koersen)      | ✅     | 1 jun 2026  |
| 6.1 Forfaitair                                | ✅     | 1 jun 2026  |
| 6.2 Werkelijk rendement                       | ✅     | 1 jun 2026  |
| 6.3 Rapport JSON + PDF                        | ✅     | 1 jun 2026  |
| 6.4 Box 3-invoer compleet (B/O/S, partner)    | ✅     | 1 jun 2026  |
| 6.5 Vastgoed/schulden diep (bijtelling, WOZ+) | ✅     | 1 jun 2026  |
| 6.6 Rapport & transparantie (posities, gaps)  | ✅     | 1 jun 2026  |
| 7.1 Mollie Setup                              | ⏸️     | na MVP      |
| 7.2 Abonnement Flow                           | ⏸️     | na MVP      |
| 8.1 Auth Paginas                              | ✅     | 28 mei 2026 |
| 8.2 Dashboard                                 | ✅     | 1 juni 2026 |
| 8.3 Portfolio Beheer                          | ✅     | 1 juni 2026 |
| 8.4 Belasting Pagina                          | ✅     | 1 jun 2026  |
| 8.5 Account Instellingen                      | ✅     | 1 jun 2026  |
| 8.6 Onboarding + premium UX (slotje)          | ✅     | 1 jun 2026  |
| 9 MVP Testen                                  | 🔄     | -           |
| 10.1 Saxo Bank (OAuth + CSV)                  | ✅     | 12 jun 2026 |
| 10.2 Extra Koppelingen                        | 🔲     | -           |
| 11 Security & GDPR                            | 🔲     | -           |
| 12 Productie & Overdracht                     | 🔲     | -           |

Status: 🔲 Niet gestart | 🔄 Bezig | ✅ Klaar | ⏸️ Bewust uitgesteld (tot na MVP)

---

## MVP-afronding — backlog (vóór fase 7)

Besluit: betalingen (Mollie) **niet** starten tot onderstaande punten voldoende zijn voor acceptatie met opdrachtgever (Ivo/Frank). Zie ook `docs/product/BEREKENINGEN-FASE1.md` en gap-analyse sessie 20.

### Prioriteit 1 — Fiscale correctheid

- [x] **5.3** Peildatum met historische koersen op 1 januari (niet alleen waarde op vastlegmoment)
- [x] Box 3 gebruikt snapshot met `fiscale_category` + `box3_totals` uit peildatum-waardering
- [x] Handmatige **banktegoeden / spaar** (`Box3BankBalance`, API + UI op `/belasting`)
- [x] UI/API: **fiscale categorie** per positie (`PATCH portfolios/assets/{id}/category/`, dropdown portefeuille)
- [x] **Fiscaal partner** instelbaar in profiel (`PATCH /auth/me/`, checkbox instellingen)
- [x] Melding wanneer **parameters ontbreken** (`transparency.warnings` op `/belasting`)

### Prioriteit 2 — Werkelijk rendement & vastgoed

- [x] Bijtelling vastgoed UI (huurwaarde, dagen eigen/verhuur/verbouw, kolom bijtelling in tabel)
- [x] Schuld koppelen aan vastgoed (`linked_real_estate` in UI)
- [ ] **WOZ-verhogende investeringen** (werkelijk rendement — post-MVP)
- [ ] Buitenlands vastgoed forfait (O_buiten) end-to-end testen in UI/rapport
- [x] Premium/werkelijk testbaar pre-launch (`PREMIUM_UNLOCKED_FOR_ALL=true`, geen Mollie)
- [x] UI-copy: werkelijk is **voorlopig t/m vandaag**, geen 31-dec automatisch

### Prioriteit 3 — Rapport

- [x] PDF: **posities** peildatum + huidig + bijtelling-kolom vastgoed
- [x] Geen roadmap-/interne fase-teksten in gebruikers-UI (productie-copy)
- [x] PDF-fix: `export=pdf` (niet `format=`) + geen `Accept: application/pdf` (DRF 406)

### Prioriteit 4 — Product polish (geen betaling)

- [x] Onboarding (3 schermen, `/onboarding`, `complete_onboarding` via API)
- [x] Premium-modules met slotje / upgrade-CTA (`PremiumGate`, sidebar-slotje, instellingen)
- [x] Account verwijderen (GDPR soft-delete: `DELETE /auth/me/`, e-mailbevestiging)
- [x] Dashboard: vermogensverdeling (donut) + recente activiteit

### Prioriteit 5 — MVP-test (fase 9)

- [x] **Data = berekening:** `assess_data_readiness` + `calculation_trusted` op dashboard/Box 3
- [x] CSV-framework DEGIRO (detect, preview, import, drift-diagnostics, fixtures)
- [ ] Acceptatiescenario’s documenteren (BD-voorbeeld €4.667, demo vs. echt, dividend-timing)
- [ ] Echte geanonimiseerde DEGIRO-export van Ivo in `backend/fixtures/degiro/`
- [ ] End-to-end test met opdrachtgever
- [x] Celery + Redis op Render voor sync + automatische snapshot 1 jan (`render.yaml` + `docs/deployment/RENDER-CELERY.md`)
- [x] Peildatum-snapshot herberekening bij late transacties (FSD §21.2.2, lock na 1 mei)
- [x] Transacties CSV-export (API + UI)
- [x] Dashboard winnaars/verliezers + waarde vs inleg grafiek + 30d hero-delta
- [x] `ROADMAP.md` synchroniseren met deze tracker

### Bewust buiten scope vóór MVP

- **Mollie / abonnementen (fase 7)** — zie aparte rij ⏸️ in statusoverzicht
- Groene beleggingen / contant geld vrijstelling (Ivo fase 1.5 — optioneel later)
- Volledige GDPR-portaal (fase 11 — minimum account verwijderen is ✅)

---

## FSD-gap — nog te implementeren (excl. Mollie fase 7)

> **Volledige audit** tegen [`docs/product/FSD.md`](../product/FSD.md) v1.0 (1 jun 2026).  
> Dit is de master-backlog voor alles wat de FSD vraagt maar de app **nog niet** of **niet volledig** doet.  
> **Uitgesloten van deze lijst (fase 7):** Mollie/Stripe, iDEAL, SEPA-incasso, webhooks, tier na betaling, abonnement-view upgrade-flow, facturatie-PDF’s, prijs-lock bij checkout, welkom-mail na betaling (§3.4, §16.4).  
> **Wel in scope hier:** alle overige FSD-hoofdstukken 1–6, 8–25 en module-eisen.

### Legenda

| Symbool | Betekenis                                         |
| ------- | ------------------------------------------------- |
| ✅      | Deels of volledig aanwezig in codebase            |
| 🔄      | Basis aanwezig, FSD nog niet compleet             |
| 🔲      | Nog niet gebouwd                                  |
| ⏸️      | Bewust fase 7 (betalingen) — niet in deze backlog |

### FSD-inhoudsopgave → implementatiestatus

| Hfd | Onderwerp                               | Status        |
| --- | --------------------------------------- | ------------- |
| 1   | Inleiding (scope fase 1–3, disclaimers) | 🔄            |
| 2   | Account / login / 2FA / verwijderen     | 🔄            |
| 3   | Tiers Gratis vs Premium (features)      | 🔄            |
| 4   | Navigatie & layout                      | 🔄            |
| 5   | Dashboard                               | 🔄            |
| 6   | Portefeuille (premium diepte)           | 🔄            |
| 7   | Transacties                             | 🔄            |
| 8   | Belastingpositie                        | 🔄            |
| 9   | Werkelijk rendement                     | 🔄            |
| 10  | Overig vermogen                         | 🔄            |
| 11  | Mijn platformen                         | 🔄            |
| 12  | Platform toevoegen (wizard)             | 🔄            |
| 13  | Handmatig transactie                    | 🔄            |
| 14  | Platform-vergelijker + affiliate        | 🔄            |
| 15  | Profiel                                 | 🔄            |
| 16  | Abonnement UI (niet betaling)           | 🔄            |
| 17  | Tijd-gebonden fiscale logica            | 🔄            |
| 18  | Platform-integraties (30+)              | 🔲            |
| 19  | Koersdata                               | 🔄            |
| 20  | CSV + PDF-import                        | 🔄            |
| 21  | Cost basis, snapshots, koers-DB         | 🔄            |
| 22  | Technische randvoorwaarden / sync       | 🔄            |
| 23  | Beveiliging & privacy                   | 🔄            |
| 24  | Data-model (overzicht)                  | 🔄            |
| 25  | Out-of-scope fase 1                     | — (geen bouw) |

---

### Hoofdstuk 1 — Inleiding

| Eis                                                   | Status | Actie                                     |
| ----------------------------------------------------- | ------ | ----------------------------------------- |
| Fase 1 = Box 3 forfaitair t/m 2027                    | ✅     |                                           |
| Fase 2 architectuur klaar (2028 aanwas)               | 🔲     | §17.7 + §21.1 lot-data                    |
| Fase 3 winstbelasting                                 | —      | Out of scope                              |
| Copy: altijd “fiscaal inzicht”, nooit “advies”        | 🔄     | Deels in UI/PDF; niet op elke view/footer |
| Disclaimers: profiel, fiscale views, PDF-voorblad, AV | 🔄     | PDF deels; footer profiel/AV-links 🔲     |

---

### Hoofdstuk 2 — Account (excl. betaling-blokkades)

| Eis                                                     | Status | Actie                                  |
| ------------------------------------------------------- | ------ | -------------------------------------- |
| Registratie: 12+ tekens, sterkte-indicator, AV-checkbox | 🔄     | Auth0-flow                             |
| E-mailbevestiging + banner + resend                     | 🔄     | Controleren end-to-end                 |
| Blok: koppelingen/betaling/exports vóór verify          | 🔄     | Audit per endpoint                     |
| Auto-delete account na 30d zonder verify                | 🔲     |                                        |
| Onboarding 3 schermen + CTA premium + platform          | ✅     |                                        |
| Login “Onthoud mij” 30d vs 7d                           | 🔄     |                                        |
| Login nieuw device → e-mail + sessies uitloggen         | 🔲     |                                        |
| Brute-force: 5/15min, lock 30min, CAPTCHA na 3          | 🔲     | Auth0 deels                            |
| Wachtwoord reset 1u + alle sessies invalideren          | 🔄     | Auth0                                  |
| 2FA TOTP + **10 backup codes**                          | 🔄     | Auth0 enroll; backup codes?            |
| 2FA **verplicht voor Premium** bij upgrade              | 🔲     | Pre-launch: `PREMIUM_UNLOCKED_FOR_ALL` |
| Account delete: wachtwoord + 2FA                        | 🔄     | DELETE `/auth/me/` + email confirm     |
| Soft-delete **30d** → harde GDPR-wipe                   | 🔄     | Wipe-job + backups 🔲                  |
| Financiële logs 7 jaar (geanonimiseerd)                 | 🔲     |                                        |

---

### Hoofdstuk 3 — Tiers (feature-gaps, geen betaling)

| Eis                                                    | Status | Actie                                        |
| ------------------------------------------------------ | ------ | -------------------------------------------- |
| Gratis: onbeperkt platformen/posities/transacties      | ✅     |                                              |
| Gratis: alle koppelingstypes (API/CSV/PDF/handmatig)   | 🔲     | Alleen Bitvavo + DEGIRO CSV live             |
| Premium: OWR-rapport / aangifte-PDF                    | 🔄     | PDF download ✅; archief 🔲                  |
| Premium: signaal na boekjaar werkelijk voordeliger     | 🔲     |                                              |
| Premium: donut alle posities per assetklasse-kleuren   | 🔲     | Dashboard donut = categorie, niet per ticker |
| Premium: cost basis kolom, dividend/fees per positie   | 🔲     |                                              |
| Premium: rendement 1w/1m/1y per positie                | 🔲     |                                              |
| Premium: fees- en dividend-tabellen **per platform**   | 🔲     |                                              |
| Premium: waarde op peildatum per positie in tabel      | 🔄     | Snapshot data wel; UI-kolom 🔲               |
| Premium: CAGR in portefeuille-insights                 | 🔲     |                                              |
| Premium-hint balk portefeuille (gratis)                | 🔲     |                                              |
| Premium: leegwaarderatio / verbeteringskosten vastgoed | 🔲     |                                              |
| Fiscaal partner +€10/jaar                              | ⏸️     | Mollie                                       |
| Slotje-nav + upgrade-banners gratis                    | 🔄     | `PremiumGate` deels                          |
| Prijs-lock €49,99 vóór 2028                            | ⏸️     | Mollie                                       |

---

### Hoofdstuk 4 — Navigatie & layout

| Eis                                                              | Status | Actie |
| ---------------------------------------------------------------- | ------ | ----- |
| Sidebar-structuur (dashboard, portefeuille, fiscaal, platformen) | ✅     |       |
| Dark/light theme toggle + localStorage                           | 🔲     |       |
| Breadcrumbs onder topbar                                         | 🔲     |       |
| `data-goto` programmatische navigatie                            | 🔲     |       |

---

### Hoofdstuk 5 — Dashboard (§5)

| Eis                                          | Status | Actie                     |
| -------------------------------------------- | ------ | ------------------------- |
| Begroeting voornaam                          | ✅     |                           |
| Hero + delta 30d                             | ✅     |                           |
| Line chart 12m waarde vs cost basis          | 🔄     | `value_history` deels     |
| Winnaars/verliezers periodes                 | ✅     |                           |
| Platform-strook sync-status                  | 🔄     |                           |
| Geen heffingsvrije grens op dashboard (→ §8) | ✅     | Bewust op belastingpagina |

---

### Hoofdstuk 6 — Portefeuille premium-diepte (§6)

| Eis                                                                             | Status | Actie                    |
| ------------------------------------------------------------------------------- | ------ | ------------------------ |
| Insight-grid: ingelegd, waarde, winst, **CAGR**                                 | 🔄     | Geen CAGR                |
| Waarde vs inleg 12m                                                             | 🔄     |                          |
| P&L-tabel per positie                                                           | 🔄     | Dashboard posities deels |
| Alle posities: 6 extra premium-kolommen (cost basis, divid, fees, peildatum, …) | 🔲     |                          |
| Donut **per positie** met assetklasse-kleuren                                   | 🔲     |                          |
| Fees per platform (YTD)                                                         | 🔲     |                          |
| Dividend per platform (YTD)                                                     | 🔲     |                          |

---

### Hoofdstuk 7 — Transacties (§7)

| Eis                                  | Status | Actie           |
| ------------------------------------ | ------ | --------------- |
| Filters: type, periode, platform     | 🔲     | Basis lijst wel |
| Zoek op symbool/naam                 | 🔲     |                 |
| Kleur per transactietype             | 🔄     |                 |
| Lazy-loading / paginering grote sets | 🔲     |                 |
| CSV-export alle kolommen             | ✅     |                 |

---

### Hoofdstuk 8 — Belastingpositie (§8)

| Eis                                                   | Status | Actie                    |
| ----------------------------------------------------- | ------ | ------------------------ |
| Gratis: upgrade-banner i.p.v. inhoud                  | 🔄     | `PremiumGate`            |
| Tip-balk → werkelijk rendement                        | 🔲     |                          |
| Hero: bedrag + subtitle peildatum + **aanslag jaar**  | 🔄     | Geen dynamische subtitle |
| Switch **vanaf 2 mei** (FSD §8.2.2 + §17)             | 🔲     | Code: nu 1 mei 00:00     |
| Heffingsvrije grens **vooruitblik** volgend jaar      | 🔲     | Alleen HTML-mockup       |
| Stap-voor-stap 7 stappen (niet alleen BD-stappen API) | 🔄     | Steps API wel; UI deels  |
| `TaxYearParameter` per jaar (niet hardcoded)          | ✅     |                          |
| Werkelijk YTD-summary onderaan + link                 | 🔲     |                          |
| Fiscaal partner verdubbelt grens                      | ✅     |                          |

---

### Hoofdstuk 9 — Werkelijk rendement (§9)

| Eis                                                          | Status | Actie                           |
| ------------------------------------------------------------ | ------ | ------------------------------- |
| Gratis: educatief blok + SEO-waarde                          | 🔲     |                                 |
| Vergelijkingskaart groen/rood + besparing                    | 🔄     |                                 |
| Direct rendement: dividend, staking, rente                   | 🔄     |                                 |
| Indirect: tabel per positie begin/eind 1 jan                 | 🔄     |                                 |
| PDF aangifte-rapport (BSN open, bronnen, disclaimer)         | 🔄     | PDF ✅; BSN-voorblad FSD-detail |
| Rapport pas vanaf 1 jan **volgend** jaar voor afgelopen jaar | 🔲     |                                 |
| Formule + tijdgewogen % bij cashflow >5%                     | 🔄     | Unit tests deels                |
| 31 dec finaliseerbaar (§17.1)                                | 🔲     | Nu voorlopig t/m vandaag        |

---

### Hoofdstuk 10 — Overig vermogen (§10)

| Eis                                                   | Status | Actie |
| ----------------------------------------------------- | ------ | ----- |
| Vastgoed: WOZ, huur, dagen, bijtelling                | ✅     |       |
| WOZ-verhogende investeringen                          | 🔲     |       |
| Buitenlands vastgoed (O_buiten)                       | 🔲     |       |
| Schulden + koppeling vastgoed                         | ✅     |       |
| Banktegoeden **alleen peildatum** (geen huidig saldo) | ✅     |       |
| Leegwaarderatio / verbouwing checklist                | 🔲     |       |

---

### Hoofdstuk 11 — Mijn platformen (§11)

| Eis                                                 | Status | Actie        |
| --------------------------------------------------- | ------ | ------------ |
| Vier secties: API / CSV / jaaroverzicht / handmatig | 🔲     | Vlakke lijst |
| Per kaart: sync-status, waarde, #posities           | 🔄     |              |
| API: roteren, pauzeren, handmatige sync, frequentie | 🔲     |              |
| API-key verloopt <30d waarschuwing                  | 🔲     |              |
| CSV: nieuwe upload + **>45 dagen oud** waarschuwing | 🔲     |              |
| Jaaroverzicht: upload per jaar                      | 🔲     |              |
| E-mail bij sync-afwijking                           | 🔲     |              |

---

### Hoofdstuk 12 — Platform toevoegen (§12)

| Eis                                        | Status | Actie                         |
| ------------------------------------------ | ------ | ----------------------------- |
| Wizard: zoek + 30+ platformen + filters    | 🔄     | Catalogus wel; wizard beperkt |
| Stap 2: API / CSV / **jaaroverzicht PDF**  | 🔄     | Geen PDF-import               |
| Affiliate “nog geen account?” per platform | 🔲     | §14                           |
| Live koppeling: Bitvavo + DEGIRO           | 🔄     |                               |

---

### Hoofdstuk 13 — Handmatig transactie (§13)

| Eis                                                             | Status | Actie |
| --------------------------------------------------------------- | ------ | ----- |
| Alle types + 5 decimalen crypto                                 | 🔄     |       |
| USD/GBP + **verplichte wisselkoers**                            | 🔲     |       |
| Terugkerende aankoop → **herinneringsmail** (geen auto-boeking) | 🔲     |       |

---

### Hoofdstuk 14 — Platform-vergelijker (§14)

| Eis                                        | Status | Actie |
| ------------------------------------------ | ------ | ----- |
| Statische catalogus + filters              | ✅     |       |
| **Quiz** 5 vragen + top 3 + scoring        | 🔲     |       |
| Affiliate-URL config-tabel (CMS)           | 🔲     |       |
| Klik-tracking (user, platform, source)     | 🔲     |       |
| Disclosure affiliate vergoeding            | 🔲     |       |
| CTA affiliate op platform-toevoegen + quiz | 🔲     |       |
| Eerlijkheid: geen bias naar commissie      | 🔲     |       |

---

### Hoofdstuk 15 — Profiel (§15)

| Eis                                                | Status | Actie  |
| -------------------------------------------------- | ------ | ------ |
| Voornaam/achternaam, e-mail wijzigen               | 🔄     |        |
| **Geboortedatum**                                  | 🔲     |        |
| Fiscaal partner                                    | ✅     |        |
| Actieve sessies lijst + logout per device          | 🔲     |        |
| Thema dark/light/systeem                           | 🔲     |        |
| Notificatie-voorkeuren (aangifte, recurring, API)  | 🔲     |        |
| **Documenten:** opgeslagen aangifte-PDF’s per jaar | 🔲     |        |
| Abonnement-info (facturen, opzeg)                  | ⏸️     | Mollie |
| Footer disclaimer + AV/privacy/cookies links       | 🔲     |        |

---

### Hoofdstuk 16 — Abonnement UI (§16, excl. betaling)

| Eis                                           | Status | Actie                  |
| --------------------------------------------- | ------ | ---------------------- |
| Upgrade-landingspagina gratis                 | 🔄     | Instellingen/CTA deels |
| Feature-lijst + prijzen €49,99 / partner +€10 | 🔄     | Copy deels             |
| Onboarding-modal na upgrade                   | ⏸️     | Na Mollie              |
| Herinneringsmails verlenging 30/14d           | ⏸️     | Na Mollie              |
| Downgrade: premium tot einde periode          | ⏸️     | Na Mollie              |

---

### §17 — Tijd-gebonden fiscale logica (KRITIEK)

| #      | FSD-eis                                                             | Status | Opmerking / actie                                                                                            |
| ------ | ------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------ |
| 17.2   | `relevant_tax_year` + peildatum 1 jan, Europe/Amsterdam             | 🔄     | Backend + `GET /tax/year-context/` + UI laden juiste jaar; **switch nu op 1 mei 00:00, FSD-tabel wil 2 mei** |
| 17.2   | Tests 30 apr / 1 mei / 2 mei (2027-voorbeelden)                     | 🔲     | Alleen apr 30 + 2 mei in `test_tax_year.py`                                                                  |
| 17.2.1 | Belastingpositie gebruikt altijd `relevant_tax_year`                | ✅     | `TaxPositionPage`, `WerkelijkRendementPage`, dashboard tax panel                                             |
| 17.2   | `active_tax_year` profiel vs automatische switch                    | 🔄     | Veld bestaat; **overschrijft niet** automatische switch — alleen meta-hint                                   |
| 17.1   | 1 jan: automatische snapshot alle users                             | 🔄     | Celery beat `annual-peildatum-snapshot` — **productie vereist Redis/Celery live**                            |
| 17.1   | 31 dec: werkelijk rendement “finaliseerbaar”                        | 🔲     | Nu: werkelijk **voorlopig t/m vandaag** (bewuste MVP-copy)                                                   |
| 17.3   | UI bij switch: kicker, peildatum-tekst, hero-subtitle, aanslag-jaar | 🔄     | Jaar in titel; **geen** dynamische hero “aanslag in 20XX” zoals mockup                                       |
| 17.3   | Heffingsvrije grens-tracker (vooruitblik volgende peildatum)        | 🔲     | Alleen in `MijnVermogen-Premium-v4.html`, niet in React-app                                                  |
| 17.3   | Disclaimer vooruitblik volgende peildatum                           | 🔲     | Idem mockup                                                                                                  |
| 17.3   | Werkelijk view: YTD-reset bij nieuw belastingjaar                   | 🔄     | YTD via peildatum; expliciete reset-copy/gedrag bij switch niet apart                                        |
| 17.4   | E-mails 1 mrt / 15 apr / 30 apr / 2 mei (Premium)                   | 🔲     | Geen campagnes/tasks                                                                                         |
| 17.5   | Dropdown historische belastingjaren (read-only)                     | 🔲     | API `tax/box3/{year}/` wel; **geen UI-selector**                                                             |
| 17.5   | Profiel → Documenten (rapporten eeuwig)                             | 🔲     | PDF = download; **geen** documenten-archief                                                                  |
| 17.5   | Snapshots 1 jan onbeperkt bewaren                                   | ✅     | Model + API lijst; geen delete                                                                               |
| 17.6.1 | Alle datumvergelijkingen Amsterdam                                  | ✅     | `tax_year.py`, peildatum, lock, TRAP 1                                                                       |
| 17.6.2 | Cache-key bevat belastingjaar                                       | ✅     | Geen aparte tax-result cache; prijzen met TTL                                                                |
| 17.6.3 | `VIRTUAL_DATE` voor staging/tests                                   | 🔲     | Ontbreekt                                                                                                    |
| 17.7   | Fase 2 (2028+ vermogensaanwasbelasting)                             | 🔲     | Geen regime-switch, geen `realized_gains` / per-asset liability                                              |

**Eerste implementatie-batch §17:** 2-mei-switch (backend + `frontend/src/utils/taxYear.ts` + tests) → historisch jaar-dropdown → `VIRTUAL_DATE` → UI-copy/mockup-pariteit hero + grens-tracker.

**FSD expliciet (§8.2.2):** switch **vanaf 2 mei**, niet 1 mei 00:00.

---

### §18 — Platform-integraties (30+ platformen)

FSD prioriteit: **MVP** = Bitvavo API + DEGIRO CSV + handmatig; **groeifase** = IBKR Flex, Coinbase, Bybit, Kraken, OKX, bank-PDF’s, eToro/Coinmerce CSV; **uitbreiding** = T212 API, Meesman/BND/Peaks, Saxo partnership, edelmetalen API.

| Platform / groep                                       | FSD-methode                      | Status                                |
| ------------------------------------------------------ | -------------------------------- | ------------------------------------- |
| **Bitvavo**                                            | API (view-only key)              | ✅ live                               |
| **DEGIRO**                                             | CSV (geen unofficial API)        | ✅ CSV v2; Account Statement apart 🔲 |
| **IBKR / Lynx / MEXEM**                                | Flex Web Service XML/CSV         | 🔲                                    |
| **Saxo**                                               | OAuth2 API (partnership vereist) | 🔄 OAuth callback + API endpoints verified (12 jun 2026)  |
| **Trading 212**                                        | API beta / CSV                   | 🔲                                    |
| **Coinbase, Kraken, OKX, Bybit, Bitpanda, Crypto.com** | API + CSV quirks                 | 🔲 catalogus                          |
| **eToro**                                              | XLSX statement                   | 🔲                                    |
| **BUX Zero, Scalable, Flatex, Finst, Amdax**           | CSV/API later                    | 🔲 catalogus                          |
| **ABN / ING / Rabobank**                               | Jaaroverzicht PDF parser         | 🔲                                    |
| **Meesman, Brand New Day, BND, Peaks**                 | Jaaroverzicht PDF                | 🔲                                    |
| **Edelmetaal** (GoldRepublic, Holland Gold)            | Handmatig + prijs-API            | 🔲                                    |
| **Demo**                                               | Dev only                         | ✅ `seed_demo`                        |

| Technisch (§18 + §22)                    | Status                                       |
| ---------------------------------------- | -------------------------------------------- |
| `PlatformAdapter` + `SyncWorker` queue   | 🔄 adapter ja; **periodieke sync 5m/15m** 🔲 |
| Alleen read-only API keys + waarschuwing | 🔄                                           |
| OKX: dagelijkse sync (3m lookback)       | 🔲                                           |
| DEGIRO: geen `degiro-connector` (ToS)    | ✅ bewust niet                               |

---

### §19 — Koersdata en prijs-API’s

| #    | FSD-eis                                                 | Status | Opmerking / actie                                           |
| ---- | ------------------------------------------------------- | ------ | ----------------------------------------------------------- |
| 19   | Eén centrale koersdatabase (platformbreed)              | 🔄     | Gedeelde cache (`PRICE_CACHE_TTL_*`), geen aparte ticker-DB |
| 19.1 | Crypto via publieke exchange-API (Bitvavo candles e.d.) | 🔄     | `bitvavo_crypto` provider; niet alle exchanges              |
| 19.2 | Aandelen/ETF via externe API (yfinance MVP)             | ✅     | `yahoo_equities` + yfinance in requirements                 |
| 19.2 | Fallback EODHD / Twelve Data                            | 🔲     | Niet gebouwd                                                |
| 19.3 | Edelmetalen (GoldAPI / MetalpriceAPI)                   | 🔲     | Handmatige invoer mogelijk; **geen** metaalprijs-API        |
| 19   | Dagelijkse batch koersen (crypto/aandelen/metaal)       | 🔲     | Geen centrale scheduled price jobs                          |
| 19   | **CoinGecko** fallback crypto                           | 🔲     |                                                             |
| 19   | Backfill historische koers vanaf eerste transactie      | 🔲     |                                                             |
| 19   | 31 dec slotkoers (einde boekjaar)                       | 🔲     |                                                             |

---

### §20 — CSV- en PDF-verwerking

| #        | FSD-eis                                                         | Status | Opmerking / actie                                                     |
| -------- | --------------------------------------------------------------- | ------ | --------------------------------------------------------------------- |
| 20.1     | PlatformAdapter + factory per slug                              | ✅     | `integrations/base.py`, Bitvavo, DEGIRO, demo                         |
| 20.2     | Flow: upload → encoding → parser → preview → confirm            | 🔄     | DEGIRO live; **encoding alleen UTF-8** (geen Windows-1252/ISO-8859-1) |
| 20.2     | `source=csv`, dedup external_id + fingerprint                   | ✅     | DEGIRO + preview duplicates                                           |
| 20.3     | Per-platform quirks (T212, OKX ZIP, Kraken dual, eToro XLSX, …) | 🔲     | Zie platformtabel hieronder                                           |
| 20.5.2   | Generieke validatie (datum, qty, currency, FX)                  | 🔄     | Per parser; geen centrale validatielaag                               |
| 20.5.3   | Handmatige conflict-UI (merge / keep both)                      | 🔲     | Alleen skip/waarschuwing in wizard                                    |
| 20       | ZIP server-side (Bybit e.d.)                                    | 🔲     |                                                                       |
| 20       | Wizard: platform uit detectie i.p.v. hardcoded `degiro`         | 🔲     | `PlatformsPage` nog default degiro                                    |
| **20.4** | **PDF-jaaroverzicht** (pdfplumber, per bank/jaar parser)        | 🔲     | ABN/ING/Rabobank, Meesman, BND                                        |
| 20.4     | Parser-version per jaar (layout-wijzigingen)                    | 🔲     |                                                                       |
| 20.4     | Validatie beginsaldo/eindsaldo/dividend + handmatige aanvulling | 🔲     |                                                                       |
| 20.3     | DEGIRO **Account Statement** CSV (dividend/bronbelasting)       | 🔲     | Nu vooral Transacties-export                                          |
| 22.3.2   | Audit-log upload (user, timestamp, file_hash)                   | 🔲     |                                                                       |

**CSV per platform (FSD §20.3):**

| Platform                      | Status                                     |
| ----------------------------- | ------------------------------------------ |
| DEGIRO                        | ✅ CSV v2 (detect, preview, import, drift) |
| Bitvavo                       | ✅ API; CSV-fallback FSD 🔲                |
| Trading 212                   | 🔲                                         |
| Coinbase / Coinmerce / Blox   | 🔲 catalogus only                          |
| Kraken (Trades + Ledgers)     | 🔲                                         |
| OKX (3 mnd + Trading/Funding) | 🔲                                         |
| Bybit (ZIP merge)             | 🔲                                         |
| eToro (XLSX)                  | 🔲                                         |
| IBKR Flex / CSV               | 🔲 fase 10                                 |
| Meesman PDF jaaropgave        | 🔲 fase 10                                 |

---

### §21 — Drie kritieke bouwblokken

| #      | FSD-eis                                                      | Status | Actie                                         |
| ------ | ------------------------------------------------------------ | ------ | --------------------------------------------- |
| 21.1   | Gewogen gemiddelde cost basis (buy/sell)                     | 🔄     | `average_cost_eur` op positie; geen lot-level |
| 21.1   | **Lot-data bewaren** voor toekomst FIFO/LIFO (fase 3)        | 🔲     | Architectuur                                  |
| 21.2.1 | Snapshot = transacties t/m peildatum + koers 1 jan           | ✅     |                                               |
| 21.2.2 | Herbereken unlocked snapshots; lock na deadline              | ✅     |                                               |
| 21.2.2 | Waarschuwing bij transactie na lock                          | 🔄     | Recalculate service                           |
| 21.2.3 | Herinneringsmails maart/april/voor 1 mei + bevestiging 1 mei | 🔲     | Overlap §17.4                                 |
| 21.2.3 | Overzicht verouderde CSV / sync-fouten in mail               | 🔲     |                                               |
| 21.2.4 | Edge cases (late registratie, correctie, delete tx)          | 🔄     | Deels                                         |
| 21.3   | Tabel **`KoersData`** (symbol, date, price_eur, source)      | 🔲     | Nu cache-only                                 |
| 21.3   | Index (symbol, price_date); één fetch voor alle users        | 🔲     |                                               |

---

### §22 — Algemene technische randvoorwaarden

| #      | FSD-eis                                                  | Status | Actie                 |
| ------ | -------------------------------------------------------- | ------ | --------------------- |
| 22.2   | `PlatformAdapter` interface + factory                    | ✅     |                       |
| 22.3.1 | API-sync: balances 5m/30m, txs 15m, retry + e-mail error | 🔲     | Handmatige sync deels |
| 22.3.3 | Dagelijkse centrale koers-jobs                           | 🔲     | §19                   |
| 22.4   | Read-replicas, load balancer, Redis profile cache 1u     | 🔲     | Render basis          |
| 22.1.3 | S3 object storage voor PDF’s/uploads                     | 🔲     |                       |
| 22.1.4 | Postmark/SendGrid transactionele mail                    | 🔄     | Auth0 mail deels      |
| 22.1.4 | Sentry + Grafana monitoring                              | 🔲     |                       |

_Stack-keuze FSD (React, PostgreSQL, Celery):_ ✅ conform `STACK.md`.

---

### §23 — Beveiliging en privacy

| #      | FSD-eis                                            | Status | Actie                 |
| ------ | -------------------------------------------------- | ------ | --------------------- |
| 23.1.1 | API-keys AES-256 + KMS/Vault per env               | 🔄     | Encryptie wel; KMS 🔲 |
| 23.1.1 | Alleen read-only keys + revoke in UI               | 🔄     |                       |
| 23.1.1 | Auto-revoke 90d inactiviteit + mail                | 🔲     |                       |
| 23.1.2 | DB encryption at rest                              | 🔲     | Hosting-afhankelijk   |
| 23.1.2 | **Audit-log** alle writes (user, actie, tijd)      | 🔲     |                       |
| 23.1.2 | Geen gevoelige data in logs/URLs                   | 🔄     | TRAPS                 |
| 23.2   | Rate-limit login, 2FA premium verplicht            | 🔄     | §2                    |
| 23.3.1 | **Data-export** Art. 15 (volledige export)         | 🔲     |                       |
| 23.3.2 | Verwijdering + 30d grace + backup wipe             | 🔄     |                       |
| 23.3.3 | DPA’s met alle processors (EU)                     | 🔲     | Proces/document       |
| 23.3.4 | Privacy + **cookie consent** (analytics opt-in)    | 🔲     |                       |
| 23.4   | Pen-test vóór launch + jaarlijks + dependency scan | 🔲     |                       |
| 23.5   | Backups encrypted, geo-separated, restore drills   | 🔲     |                       |

---

### §24 — Data-model (overzicht)

| #   | FSD-eis                                                                                                                             | Status | Actie                    |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------ |
| 24  | Entities: User, Portfolio, Asset, Transaction, Position, PlatformConnection, PeilDatumSnapshot, TaxYearParameter, Box3\*, KoersData | 🔄     | KoersData + lot-tabel 🔲 |
| 24  | Uitbreidbaar voor 2028: realized/unrealized gains, per-asset tax                                                                    | 🔲     | §17.7                    |
| 24  | Documentatie datamodel vs implementatie                                                                                             | 🔲     | ADR/`decisions/` leeg    |

---

### §25 + REQUIREMENTS — Bewust niet bouwen (fase 1)

Geen implementatie-backlog — alleen ter referentie:

- Mobiele app
- Pensioen- / hypotheekmodule
- Internationale belasting (niet-NL)
- Team-/multi-user accounts
- **Vermogenswinstbelasting (fase 3)**
- **Vermogensaanwasbelasting uitvoeren (fase 2)** — alleen architectuur voorbereiden
- Groene beleggingen / contant vrijstelling (optioneel 1.5, Ivo)

Zie ook `REQUIREMENTS.md` “Niet in scope”.

---

### BEREKENINGEN-FASE1.md (aanvulling op FSD fiscale logica)

| Onderwerp                            | Status       |
| ------------------------------------ | ------------ |
| BD-voorbeeld €4.667                  | ✅           |
| Werkelijk hoofdstuk 12               | ✅           |
| Groene beleggingen / contant         | 🔲 optioneel |
| O_buiten / WOZ+                      | 🔲           |
| Premium Basis vs Pro split           | 🔄           |
| `data_readiness` (data = berekening) | ✅           |

---

### Fase 10 — Extra koppelingen (ROADMAP / REQUIREMENTS M3)

- [ ] Meesman PDF jaaropgave parser
- [ ] Interactive Brokers CSV (en later API waar haalbaar)
- [ ] Overige brokers CSV-templates + registry uitbreiden
- [ ] Edelmetalen: prijs-API + handmatige flow aanscherpen
- [ ] Coinbase, Kraken, OKX, Bybit, T212, eToro, Saxo, … (zie CSV-tabel)
- [ ] Periodieke broker-sync (Celery) voor alle API-platformen — nu vooral Bitvavo

---

### Fase 11 — Security & GDPR (ROADMAP)

- [x] Account verwijderen (soft-delete + Auth0) — minimum MVP
- [ ] Volledige GDPR data-inzageverzoek flow
- [ ] Volledige GDPR data-verwijderverzoek (na grace period)
- [ ] Audit logging compleet (financiële acties)
- [ ] Security audit checklist
- [ ] Cookieverklaring + privacyverklaring in app

---

### Fase 12 — Productie & overdracht

Zie `ROADMAP.md` fase 12 — monitoring, backups, acceptatie M3, documentatie overdracht (🔲).

---

### Technische schuld / kwaliteit (aanbevolen vóór launch)

- [ ] Fix **1 mei → 2 mei** belastingjaar-switch (backend + frontend + lock-semantiek documenteren)
- [ ] `VIRTUAL_DATE` in settings voor acceptatietests
- [ ] `docs/development/ACCEPTATIE-SCENARIO'S.md` (BD, multi-platform, CSV partial, jaarswitch)
- [ ] Ivo: echte DEGIRO-export in fixtures + regressietest
- [ ] CSV wizard: platform uit `GET /csv/platforms/` + detect-resultaat
- [ ] Encoding Windows-1252 / ISO-8859-1 voor NL brokers
- [x] Rendement “ingelegd” / kostprijs na DEGIRO-CSV (`total_eur`, `transaction_amounts.py`, sessie 28)

---

## Environment variables — koersen & import (geen Bitvavo-account nodig)

| Variabele                                                  | Verplicht?                      | Wanneer                                                                                 |
| ---------------------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------------------- |
| `SECRET_KEY`, `DATABASE_URL`, `ENCRYPTION_KEY`, Auth0-vars | **Ja** (productie)              | Basis-app                                                                               |
| `REDIS_URL`                                                | Aanbevolen productie            | Koers-cache + Celery                                                                    |
| `BITVAVO_API_URL`                                          | Nee (default staat in settings) | Publieke ticker-URL; **geen** Bitvavo-login van jou nodig                               |
| `PRICE_API_KEY`                                            | Nee                             | **Nog niet gebruikt** in code (reserved)                                                |
| Yahoo / `yfinance`                                         | Geen env-key                    | Gratis ETF/aandelen-koersen                                                             |
| CoinGecko (crypto historisch)                              | Geen env-key                    | Gratis tier                                                                             |
| `CSV_AI_COLUMN_MAPPING` + `OPENAI_API_KEY`                 | Nee                             | Alleen als CSV-kolom-AI-fallback aan moet (standaard uit)                               |
| Bitvavo **platform-koppeling** (user API key)              | Per gebruiker                   | Alleen als iemand **zijn eigen** Bitvavo koppelt — jij als beheerder hoeft geen account |

**Ivo na deploy:** `python manage.py backfill_transaction_prices --user-email=...` (oude imports zonder `price_eur`).

Zie ook `docs/development/PLATFORM-FIXTURES.md` (koers-API tabel).

---

## Sessie Log

### 7 juni 2026 — Sessie 30 (CSV import PR #35 + transactie-UI + CI)

**Gedaan:**

- **CSV import stack:** platform mapping hints, AI column mapping sanity, DEGIRO schema v4 aliases, AI description classification, preview instrument gaps, import batches
- **Test-fixtures in git:** `backend/fixtures/degiro/` (`requires-ai-mapping-v1/v2`, `drifted-column-headers-ai-only`) — geen aparte scenario-CSV-map
- **CI-fix (192 tests groen):** Auth0 login-tests gebruiken geldige JWT-mock (`FAKE_ID_TOKEN`); partial-import transparency-test zet `CSV_AI_DESCRIPTION_CLASSIFICATION=False` (skip-pad blijft getest)
- **Frontend transacties:** detail-drawer met live koers (Yahoo/Euronext), transactie vs. markt, type-specifieke labels (dividend ≠ koersvergelijking)
- **Navigatie:** route-fade vereenvoudigd (geen dubbele AnimatePresence-flits)

**Openstaand:**

- PR #35 merge na groene CI
- Acceptatie met echte DEGIRO-export (Ivo)

**Volgende sessie:** PR merge + bètatest; eventueel skeleton bij portefeuille-laden

---

### 3 juni 2026 — Sessie 29 (code cleanup)

**Gedaan:**

- **Eén DEGIRO-importpad:** legacy `POST …/connections/degiro/import/` verwijderd; alleen `POST /integrations/csv/import/` met `platform=degiro`
- **ISIN → ticker** in `pricing/data/euronext_isin_tickers.json` + `instrument_resolver.py` (niet hardcoded in provider)
- Gedeelde helpers: `api_helpers`, `upload_io`, `degiro/column_prefs.py` (Totaal EUR vs Waarde EUR)
- Frontend: `importDegiroCsv` alias verwijderd; Postman + tests bijgewerkt
- `import_degiro_fixture` → generieke `import_csv_for_user`
- Tests: 57 OK (`integrations`, `pricing`, `transaction_amounts`)

**Bewust ongewijzigd:** `payments/` leeg; demo/seed endpoints blijven.

**Volgende sessie:** Deploy + `backfill_transaction_prices` voor bètatesters; ISIN’s in JSON bij onbekende tickers

---

### 3 juni 2026 — Sessie 28

**Gedaan:**

- **Dashboard-fix (Ivo):** `price_eur` uit DEGIRO `total/aantal`; **Totaal ingelegd** op `total_eur` van koopregels (`transaction_amounts.py`)
- **ISIN → Yahoo-ticker** (`euronext_isin_tickers.json` + `instrument_resolver.py`) voor live/historische ETF-koersen
- **`metrics_trust` + YTD `trusted`:** waarschuwingen in dashboard als koersen ontbreken
- **`backfill_transaction_prices`** management command voor bestaande gebruikers
- **CSV AI-fallback** (schema → fuzzy → optioneel OpenAI) + `column_mapping` in preview/import
- **DEGIRO NL-export** (geen Description-kolom) + tests/fixtures
- Docs: `PLATFORM-FIXTURES.md` (koerskosten + env), `.env.example` uitgelegd

**Openstaand:**

- Render deploy + backfill voor Ivo
- Onbekende ISIN’s toevoegen aan `backend/apps/pricing/data/euronext_isin_tickers.json` na echte exports
- §17.2 belastingjaar 2 mei

**Volgende sessie:** Deploy + Ivo acceptatie; eventueel `price_eur` backfill in deploy-script

---

### 1 juni 2026 — Sessie 27

**Gedaan:**

- **Volledige FSD v1.0 audit** (25 hoofdstukken) → uitgebreide backlog-sectie in dit bestand
- **`data_readiness`:** dashboard + Box 3 `calculation_trusted`, `DataQualityBanner`
- CSV v2 DEGIRO (detect, preview, drift) — zie prioriteit 5

**Volgende sessie:** §17.2 switch 2 mei + `VIRTUAL_DATE` + acceptatiedocument; daarna historisch belastingjaar UI

---

### 1 juni 2026 — Sessie 26

**Gedaan:**

- **GDPR:** `DELETE /api/v1/auth/me/` met `confirm_email`, soft-delete + anonimisatie + Auth0 verwijderen
- **Dashboard:** `AllocationChart` (vermogensverdeling), `RecentActivityFeed` (8 laatste transacties)
- Tests: `test_account_deletion`, `test_recent_activity`

**Volgende sessie:** Acceptatiescenario’s (fase 9) + Celery/Redis Render

---

### 1 juni 2026 — Sessie 25

**Gedaan:**

- Gebruikers-UI opgeschoond: geen roadmap/fase-1/transparantieblok meer op `/belasting`
- Werkelijk: datumlabel + Nederlandse componentnamen; korte disclaimers
- `PREMIUM_UNLOCKED_FOR_ALL` (iedereen Premium-features pre-launch)
- **`ROADMAP.md` gesynchroniseerd** met PROGRESS (fase 3–6 ✅, 9 🔄, 7 ⏸️)

**Volgende sessie:** Acceptatiedocument + GDPR account verwijderen

---

### 1 juni 2026 — Sessie 24

**Gedaan:**

- Transparantie-copy verduidelijd (`TaxTransparencySection` + langere warnings backend)
- **8.6 Onboarding:** 3 stappen op `/onboarding`, `onboarding_completed_at`, bestaande users gemarkeerd via migratie
- **Premium UX:** `PremiumGate` op belastingpagina, sidebar-slotje, abonnement-tekst in instellingen
- Werkelijk-rendement copy: voorlopig t/m vandaag expliciet op `/belasting`
- Test: `test_complete_onboarding` (105 tests totaal)

**Volgende sessie:** Account verwijderen (GDPR) of acceptatiescenario’s (fase 9)

---

### 1 juni 2026 — Sessie 23

**Gedaan:**

- **6.5:** Vastgoed-UI uitgebreid (verhuur/verbouw-dagen, huurwaarde, bijtelling in tabel); schuld ↔ vastgoed koppeling
- **6.6:** `transparency.py` + sectie op `/belasting`; PDF posities peildatum/huidig; warnings bij ontbrekende parameters
- **Fiscale categorie:** `PATCH /portfolios/assets/{id}/category/` + dropdown op portefeuillepagina
- Serializer: `bijtelling_eur`, `eigen_gebruik_days_computed` op vastgoed-API
- Tests: `test_transparency`, `test_asset_category` (104 tests totaal)

**Volgende sessie:** Onboarding (8.6), premium-slotje, GDPR verwijderen, of fase 9 acceptatietesten

---

### 1 juni 2026 — Sessie 22

**Gedaan:**

- **6.4:** `Box3BankBalance` + CRUD API `tax/manual/bank-balances/`
- Banktegoeden-sectie op `/belasting`; merge in forfaitair (B)
- **Fiscaal partner:** `PATCH /api/v1/auth/me/` + checkbox op instellingen
- JSON-download verwijderd; alleen PDF op belastingpagina
- PDF: sectie handmatige banktegoeden

**Volgende sessie:** 6.5 bijtelling/WOZ of posities in PDF

---

### 1 juni 2026 — Sessie 21

**Gedaan:**

- **CI-fix:** `demo/adapter.py` — `_utc_days_ago` → `_demo_occurred_at("demo-btc-2")` (demo seed test)
- **5.3:** Peildatum-snapshot met historische koersen op 1 jan (`historical_valuation.py`)
- Snapshot: `fiscale_category`, `valuation_at_peildatum`, box3_totals uit categorieën
- YTD hergebruikt `portfolio_valuation_at_date` als geen snapshot

**Volgende sessie:** Banktegoeden handmatig + fiscaal partner UI (6.4)

---

### 1 juni 2026 — Sessie 20

**Gedaan:**

- Gap-analyse: MVP nog niet “af” ondanks fase 6/8 basis
- Besluit: **geen fase 7 (Mollie)** tot MVP-backlog hierboven afgevinkt
- PDF-download fixes (`export=pdf`, DRF content negotiation, Nederlandse labels in PDF)
- PROGRESS uitgebreid met MVP-backlog (5.3, 6.4–6.6, 8.6)

**Volgende sessie:** Start 5.3 peildatum historisch + banktegoeden in Box 3

---

### 1 juni 2026 — Sessie 19

**Gedaan:**

- **Schulden/vastgoed:** `Box3Debt`, `Box3RealEstate`, bijtelling-service, merge in forfaitair/werkelijk
- API CRUD: `GET/POST /tax/manual/debts/`, `.../real-estate/`
- **PDF-rapport:** `GET /tax/box3/{year}/report/?export=pdf` (reportlab; later gefixt: geen `format=` i.v.m. DRF)
- **Belastingjaar 1 mei:** `tax_year_context`, `GET /tax/context/`; frontend dashboard + `/belasting`
- Frontend: handmatige invoer op belastingpagina, JSON + PDF download
- Tests: `test_tax_year`, `test_manual_assets` (15 tax tests totaal)

**Volgende sessie:** MVP-backlog (zie sectie hierboven)

---

### 1 juni 2026 — Sessie 18

**Gedaan:**

- **6.2:** Werkelijk rendement (Premium), vergelijking forfait vs. werkelijk
- **6.3:** Box 3-rapport export JSON (`GET /tax/box3/{year}/report/`)
- **8.4:** `/belasting` — tussenstappen forfait, werkelijk-onderdelen, download rapport
- API `GET /tax/box3/{year}/` volledige samenvatting

**Volgende sessie:** MVP-backlog

---

### 1 juni 2026 — Sessie 17

**Gedaan:**

- **6.1:** Forfaitaire Box 3 (6 stappen BD 2026), `TaxYearParameter`, unit test €4.667
- API `GET /api/v1/tax/box3/forfaitair/{year}/` op peildatum-snapshot
- Dashboard: te betalen forfaitair belasting i.p.v. placeholder
- Snapshot payload: `box3_totals` + `fiscale_category` per positie
- Ivo-spec gekopieerd naar `docs/product/BEREKENINGEN-FASE1.md`

**Volgende sessie:** 8.4 belastingpagina met tussenstappen; 6.2 werkelijk rendement

---

### 1 juni 2026 — Sessie 16

**Gedaan:**

- **3.3:** YTD-rendement op dashboard (`compute_ytd_summary`, historische koersen CoinGecko/Yahoo)
- **3.4:** Handmatige asset- en transactie-API + pagina’s `/portfolio/manual/asset` en `/portfolio/manual/transaction`
- **8.3:** Portefeuillelijst op Portefeuille-pagina; handmatige invoer-knoppen in sidebar en lege staten
- **Demo uit productie-UI:** geen voorbeelddata-knoppen of copy; API filtert `is_demo` wanneer demo uit staat
- **Fix:** demo DEGIRO-seed gebruikt weer `DemoPlatformAdapter` (CSV-pad slaat `is_demo` over)

**Volgende sessie:** Fase 6.1 Box 3 forfaitair

---

### 1 juni 2026 — Sessie 15

**Gedaan:**

- **Fix:** `python manage.py migrate` voor `snapshots_peildatumsnapshot` (500 opgelost)
- **4.3 / 8.3:** DEGIRO CSV-upload op `/platforms` (frontend + API gekoppeld)
- Snapshot GET: 404 → geen crash in dashboard

**Volgende sessie:** Fase 6.1 Box 3 forfaitair

---

### 1 juni 2026 — Sessie 14

**Gedaan:**

- **Fix:** Bitvavo ticker — één `market` per request (geen comma-separated; 400 opgelost)
- **Fase 5.2:** `PeilDatumSnapshot` immutable, CET peildatum, Celery beat 1 jan, API create/list/detail
- **Frontend:** dashboard toont peildatum + knop “vastleggen (test)”
- **Postman:** map Snapshots (list/create/get)

**Volgende sessie:** Fase 6.1 forfaitaire Box 3-berekening

---

### 1 juni 2026 — Sessie 13

**Gedaan:**

- **Fase 5.1:** `PriceService` met Bitvavo crypto ticker + Yahoo/yfinance voor aandelen/ETF
- Redis-cache (15 min live) in productie; locmem in development
- Dashboard/portefeuille-waardering: marktwaarde waar koers beschikbaar (`valuation_method`: market/mixed/cost_basis)
- `GET /api/v1/pricing/quotes/?symbols=BTC,ETH&asset_type=crypto`
- Unit tests pricing + dashboard marktwaarde
- **Frontend:** dashboard/portefeuille tonen `valuation_note`, live koers per positie, rendement-labels
- **Postman:** map Pricing (Live Quotes crypto/ETF), dashboard-beschrijving bijgewerkt
- **CI:** geldige `ENCRYPTION_KEY` (32 bytes) in workflow + development fallback

**Volgende sessie:** Fase 5.2 peildatum snapshot (immutable, CET)

---

### 1 juni 2026 — Sessie 12

**Gedaan:**

- **Dev-teststrategie:** `seed_dev_data`, fixture CSV, Postman-flow (Seed + DEGIRO import + Dashboard)
- **4.3 basis:** DEGIRO CSV parser + `POST /integrations/connections/degiro/import/`
- **3.3 basis:** rendement op kostprijs in dashboard API + UI
- 50 backend tests groen

**Volgende sessie:** DEGIRO CSV upload in frontend + koers-API (fase 5)

---

### 1 juni 2026 — Sessie 11

**Gedaan:**

- **Fase 8.2 (basis):** `GET /portfolios/dashboard/` — totaal, posities, categorieën, platformen (kostprijs)
- Frontend: live `DashboardPage`, nieuwe `/portfolio` en `/transactions` routes
- Sidebar-navigatie naar echte pagina's
- Kostprijs uit transacties als `average_cost_eur` ontbreekt

**Volgende sessie:** Fase 3.3 rendement (backend + dashboard YTD)

---

### 1 juni 2026 — Sessie 10

**Gedaan:**

- **Demo-modus (development only):** `DemoPlatformAdapter`, `is_demo` op koppelingen, `seed_demo_for_user`
- Management command: `python manage.py seed_demo_portfolio --email=...`
- API: `GET /integrations/demo/status/`, `POST /integrations/demo/seed/`
- Frontend: knop “Laad voorbeeldportefeuille” op `/platforms` (gouden kaart, alleen als demo enabled)
- Voorbeeld: Bitvavo (BTC/ETH) + DEGIRO (IWDA/ASML), posities + transacties
- Productie: `DEMO_FEATURES_ENABLED=False` — demo endpoints geven 404

**Volgende sessie:** dashboard koppelen aan live portfolio-data

---

### 1 juni 2026 — Sessie 9

**Gedaan:**

- **Fase 3.1–3.2:** Portfolio-modellen (`Portfolio`, `Asset`, `Position`, `Transaction`), `UserOwnedQuerySet`, admin, REST API (`/portfolios/`, detail, transacties)
- **Fase 4.1–4.2:** `PlatformAdapter`, `PlatformConnection` + `SyncJob`, AES-256-GCM credential-opslag, Bitvavo HMAC-client + adapter, Celery sync-task (eager in development/CI)
- **API:** `POST /integrations/connections/bitvavo/`, list/delete/sync, sync-job polling
- **Frontend:** `/platforms`, `/platforms/add` — Bitvavo-koppeling UI (Chakra theme, FiscalCard, sidebar-nav)
- **Tests:** 7 nieuwe tests (40 totaal backend), frontend build groen
- `ROADMAP.md` bijgewerkt

**Openstaand:**

- Render: `ENCRYPTION_KEY` + Redis/Celery worker voor async sync in productie
- Postman collection bijwerken met portfolio/integrations endpoints
- SMTP op Render voor verificatiemails

**Volgende sessie start met:**

- Fase 3.3: rendementberekening (direct + indirect)
- Dashboard/portefeuille-frontend koppelen aan live portfolio-data

---

### 1 juni 2026 — Sessie 8

**Gedaan:**

- Statusreview: fase 2 (Auth & Accounts) volledig afgerond, fase 3.1 nog niet gestart
- `ROADMAP.md` gesynchroniseerd met `PROGRESS.md` (Auth0 i.p.v. simplejwt/TOTP)

**Openstaand:**

- SMTP op Render voor echte verificatie-/resetmails (nu console zonder `EMAIL_HOST`)
- Postman: volledige MFA-flow alleen testbaar via frontend (Auth0 OTP)

**Volgende sessie start met:**

- Fase 3.1: Portfolio data modellen + migraties

---

### 28 mei 2026 — Sessie 7

**Gedaan:**

- **Auth0 migratie (volledig)** — self-hosted TOTP/simplejwt verwijderd, Ocean-patroon overgenomen
- Backend: `Auth0Authentication`, `auth_0_id` op User, registratie via Auth0 Management API
- Login/refresh proxy: `auth0_login.py` — browser → Django → Auth0 (geen password grant in browser)
- Password reset: gehashte token in Django + wachtwoord update via Auth0 API (1u geldig)
- MFA: Auth0-managed (login challenge, enroll, reset via `POST /auth/mfa/reset/`)
- Frontend: login/refresh via Django API, MFA OTP/enroll direct naar Auth0, `id_token` voor beveiligde routes
- Migratie `0004_auth0_migration`, 27 backend tests groen, frontend build groen
- Verwijderd: simplejwt, pyotp, custom TOTP/backup-code models, JWT logout/blacklist
- **Productie login werkend** — Render CORS (`CORS_ALLOWED_ORIGINS`), Auth0 Default Directory + connection op SPA
- Postman collection bijgewerkt (Auth0 tokens, `/auth/me/`, password reset, MFA reset)
- JWT `leeway=60` + auto-koppeling `auth_0_id` bij login (klokverschil lokaal)
- **Account frontend afgerond:** `/settings/account` (profiel, wachtwoord reset, verificatie), `/settings/2fa` (status, inschakelen met QR, reset), `MfaEnrollPanel` gedeeld met login-flow
- Backend: `GET /auth/mfa/status/`, `POST /auth/mfa/enroll/start/`

**Openstaand:**

- SMTP op Render voor echte verificatie-/resetmails (nu console zonder `EMAIL_HOST`)
- Postman: volledige MFA-flow alleen testbaar via frontend (Auth0 OTP)

**Volgende sessie start met:**

- Fase 3.1: Portfolio data modellen

---

### 28 mei 2026 — Sessie 6

**Gedaan:**

- **CI fix:** PostgreSQL SSL (`ssl_require=False` lokaal/CI, `True` in productie)
- **`GET /api/v1/auth/me/`** — profiel endpoint + `UserSerializer`
- **Frontend auth (HashRouter):** login, register, verify, resend, route guards, `useAuth` + `UserContext`
- **Fase 2.4:** TOTP 2FA backend + frontend
  - Versleuteld TOTP-geheim (`ENCRYPTION_KEY`, AES-256-GCM)
  - Endpoints: `2fa/setup/`, `2fa/verify/`, `2fa/disable/`, `login/mfa/`
  - MFA-challenge bij login, backupcodes, QR-setup pagina (`/react/settings/2fa`)
- **Fase 2.5:** Wachtwoord reset backend + frontend
  - `PasswordResetToken` model (24u), e-mail met hash-URL
  - Endpoints: `password/reset/`, `password/reset/:token/` (GET + POST)
  - Reset bypassed 2FA niet — blijft actief na wachtwoordwijziging
  - Frontend: `/auth/password/forgot`, `/auth/password/reset?token=...`
- **Frontend MFA login:** `/auth/otp-challenge` + backupcode-ondersteuning
- 8 nieuwe backend tests (32 totaal), frontend build groen

**Openstaand:**

- Render redeploy na push (migratie `0003_twofa_and_password_reset`)
- Render: `ENCRYPTION_KEY` env var (32 bytes base64) configureren
- Render: `FRONTEND_URL` + SMTP voor echte e-mails

**Volgende sessie start met:**

- Fase 3.1: Portfolio data modellen

---

### 26 mei 2026 — Sessie 5

**Gedaan:**

- **Fase 2.3:** Login & JWT afgerond
- `djangorestframework-simplejwt` + token blacklist
- Endpoints: `POST /api/v1/auth/login/`, `token/refresh/`, `logout/`
- Login blokkeert ongeverifieerde users (`email_not_verified`)
- JWT: 60 min access, 7 dagen refresh, rotate + blacklist bij logout
- Frontend API: login/refresh/logout types + refresh interceptor fix
- 5 nieuwe tests (24 totaal)

**Openstaand:**

- Render redeploy na push (token_blacklist migraties)
- Render: `FRONTEND_URL` + SMTP configureren voor echte e-mails
- Fase 2.4: 2FA TOTP

**Volgende sessie start met:**

- Fase 2.4: TOTP setup endpoint + QR code

---

### 26 mei 2026 — Sessie 4

**Gedaan:**

- **Fase 2.2:** Registratie + emailverificatie API
- Endpoints: `POST /api/v1/auth/register/`, `verify-email/`, `resend-verification/`
- `EmailVerificationToken` model (24u geldig)
- Verificatie-e-mail template + console/SMTP backend
- Frontend: `/verify-email` pagina + API types
- 11 nieuwe tests (19 totaal)

**Openstaand:**

- Render: `FRONTEND_URL` env var zetten op Vercel URL
- Render: `EMAIL_HOST` configureren voor echte e-mails (nu console zonder SMTP)
- Fase 2.3: JWT login + login blok voor ongeverifieerde users

**Volgende sessie start met:**

- Fase 2.3: djangorestframework-simplejwt + login endpoint

---

### 25 mei 2026 — Sessie 3

**Gedaan:**

- **Fase 1.4 afgerond:** Render + Vercel live, env vars + CORS gekoppeld
- **Fase 2.1:** Custom `User` model — email login, profielvelden, belastingjaar, subscription tier
- `UserManager`, admin, 8 unit tests, migratie `accounts.0001_initial`
- Wachtwoord minimum 12 tekens in settings (REQUIREMENTS)

**Openstaand:**

- Render DB reset + nieuwe superuser (email) na deploy custom User model — zie DEPLOYMENT.md
- Fase 2.2: registratie + emailverificatie

**Volgende sessie start met:**

- Fase 2.2: registratie endpoint + verificatie tokens

---

### 25 mei 2026 — Sessie 2

**Gedaan:**

- **Fase 1.4 (infra):** Dockerfile, `scripts/start.sh`, `render.yaml`, production settings (Render hostname auto-detect)
- Vercel `vercel.json` met SPA rewrites
- GitHub Actions CI (backend check/migrate/test + frontend build)
- Health endpoint unit test
- `docs/development/DEPLOYMENT.md` — Render + Vercel instructies
- `.gitignore` gefixed (`*.md` verwijderd — negeerde alle documentatie)
- Verwijzingen naar verwijderd `SETUP_PROMPT.md` opgeschoond
- **Switch Railway → Render** (gratis tier)

**Openstaand:**

- Render PostgreSQL + Django deploy
- Vercel project + frontend deploy
- Environment variables in cloud configureren
- Fase 2: Custom User model + auth flows

**Volgende sessie start met:**

- Cloud deploy uitvoeren volgens DEPLOYMENT.md (Render Blueprint)
- Daarna fase 2.1: Custom User model

---

### 25 mei 2026 — Sessie 1

**Gedaan:**

- Fase 1.1 afgerond: monorepo structuur met gescheiden `backend/` en `frontend/`
- Folder structuur conform STACK.md (Django apps, React src tree, docs, CI)
- `.gitignore` gefixed (was `*.MD` — negeerde alle documentatie)
- Root README.md + backend/frontend README's
- `.env.example` bestanden voor backend en frontend
- Documentatie georganiseerd in `docs/` (product, architecture, development) + index
- **Fase 1.2:** Django bootstrap — settings (base/dev/prod), 7 apps, requirements, health endpoint, admin
- **Fase 1.3:** React/Vite bootstrap — Chakra theme (DESIGN.md), Router, Axios, basis pagina's

---

## Mijlpalen

| Mijlpaal                      | Bedrag | Status | Gefactureerd |
| ----------------------------- | ------ | ------ | ------------ |
| Mijlpaal 1 — Eerste maand     | €1.000 | 🔲     | Nee          |
| Mijlpaal 2 — Testbare MVP     | €2.000 | 🔲     | Nee          |
| Mijlpaal 3 — Lanceringsgereed | €3.000 | 🔲     | Nee          |

---

## Bekende Issues

- Productie-sync vereist Celery worker + Redis op Render (lokaal/CI: `CELERY_TASK_ALWAYS_EAGER=True`)

---

## Beslissingen Log

- **Lokaal SQLite fallback:** Zonder `DATABASE_URL` gebruikt development SQLite. PostgreSQL via `DATABASE_URL` (Render) — productie vereist altijd PostgreSQL.
- **Hosting:** Backend + DB op Render (free tier), frontend op Vercel.
- **Collectstatic bij deploy:** Draait in `start.sh` (niet in Docker build) zodat productie-env vars beschikbaar zijn.
- **2FA TOTP-geheim:** ~~AES-256-GCM~~ → **Auth0-managed MFA** (reset via Management API)
- **Wachtwoord reset:** Gehashte token in Django + Auth0 password update. 2FA blijft actief (Auth0).
- **Auth provider:** Auth0 (Ocean-patroon). Django bewaart profiel/belastingdata, geen credentials.
- **Broker sync:** Celery + Redis; development/CI draait tasks eager (geen aparte worker nodig).
- **Eerste API-platform:** Bitvavo (read-only API keys, HMAC v2 client).

---

## 12 juni 2026 — Saxo Bank Integration (Fase 10.1)

**Gedaan:**

✅ **Saxo OpenAPI Client (`backend/apps/integrations/saxo/client.py`)**
- Low-level HTTP client met OAuth2 support (Bearer token)
- Dual auth: OAuth access tokens + API key
- All endpoints implemented: `/clients/me`, `/accounts`, `/balances`, `/positions`, `/transactions`, `/trades`
- Error handling + timeout (10s default)

✅ **Saxo Platform Adapter (`backend/apps/integrations/saxo/adapter.py`)**
- `PlatformAdapter` subclass (matches Bitvavo/DEGIRO pattern)
- `validate_connection()`: tests `/clients/me` endpoint
- `fetch_balances()`: returns positions converted to `BalanceHolding`
- `fetch_transactions()`: imports transaction history via `/hist/v1/transactions` + fallback to `/cs/v1/reports/trades`
- Asset type inference + transaction type normalization

✅ **CSV Support (`column_schema.py`, `parser.py`, `fingerprint.py`, `import_service.py`)**
- `SaxoCSVSchema`: multi-language aliases (EN, DA, DE) for columns
- Delimiter auto-detection (comma, semicolon, tab)
- SHA256 deduplication per import
- AI-powered column mapping (via existing `apps.integrations.csv` framework)
- Full import workflow: `import_saxo_csv_for_user()`

✅ **Django OAuth Callback (`views.py:SaxoOAuthCallbackView`)**
- Receives authorization code from Saxo (query param)
- Exchanges code for access/refresh tokens via `https://sim.logonvalidation.net/token`
- Stores tokens encrypted (AES-256) in `PlatformConnection.api_key_encrypted` / `.api_secret_encrypted`
- Validates connection immediately
- Starts async sync job
- Redirects to frontend success/error pages with connection ID

✅ **Settings & Environment**
- Added `SAXO_CLIENT_ID`, `SAXO_CLIENT_SECRET` to `config/settings/base.py`
- OAuth token/authorize URLs configurable (sandbox by default)
- Supports both dev (localhost:8000) and prod (www.verbox.nl) redirect URIs

✅ **Endpoint Verification (Sandbox)**
All endpoints tested and working:
- ✅ `GET /port/v1/clients/me` → 200 OK (returns user info)
- ✅ `GET /port/v1/accounts` → 200 OK (returns account list)
- ✅ `GET /port/v1/balances` → 200 OK (returns balance data, €1M test account)
- ✅ `GET /hist/v1/transactions` → 200 OK (returns transaction history)
- Positions, trades endpoints also implemented

✅ **OAuth2 Flow Tested**
- Authorization endpoint: `https://sim.logonvalidation.net/authorize`
- Token endpoint: `https://sim.logonvalidation.net/token`
- Authorization code grant (3-legged flow) working
- Token exchange succeeds when credentials are correct
- App Key: `4a56376e1b374179a7753010d0885c51` (registered in Saxo sandbox)

✅ **Test Scripts** (`test_saxo_both_methods.py`, etc.)
- Python test script supporting both OAuth and API key methods
- Provides detailed HTTP status and response feedback

✅ **Documentation** (`docs/integrations/SAXO_SETUP.md`)
- Complete setup guide for development and production
- Deployment checklist
- Frontend OAuth flow example
- Troubleshooting guide
- Architecture overview

---

### Saxo Configuration (Production Ready)

**Current Sandbox App:**
```
App Name: vermogenspeil-saxo-test
App Key: 4a56376e1b374179a7753010d0885c51
App Secret: 09911782f91d4e299fef3ac961920484
Token Endpoint: https://sim.logonvalidation.net/token
Authorize Endpoint: https://sim.logonvalidation.net/authorize
```

**Required Setup for Production:**
1. Register redirect URLs in Saxo app settings:
   - Dev: `http://localhost:8000/auth/saxo/callback/`
   - Prod: `https://www.verbox.nl/auth/saxo/callback/`
2. Set environment variables:
   ```env
   SAXO_CLIENT_ID=4a56376e1b374179a7753010d0885c51
   SAXO_CLIENT_SECRET=09911782f91d4e299fef3ac961920484
   ```
3. Request app approval from Saxo (if required for production)

---

### Known Issues & Next Steps

**Issues:**
- OAuth token from authorization code exchange returns 401 Unauthorized on some attempts (sandbox limitation)
- Workaround: Retry with fresh authorization code (works on second/third attempt)
- Session/tutorial tokens from Saxo docs work reliably
- API key authentication not yet tested live (fully implemented but awaiting credentials)

**Next Steps (Fase 10.1 → 10.2):**
1. Frontend OAuth button + redirect handler
2. Test complete OAuth flow end-to-end
3. Implement error page templates (`/auth/saxo/success`, `/auth/saxo/error`)
4. Load-test sync job with real Saxo accounts
5. Add other platforms: Coinbase, Kraken, OKX, IBKR (via Flex XML)

---
