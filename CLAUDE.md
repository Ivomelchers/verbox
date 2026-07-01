# CLAUDE.md — Agent Context

## Verplicht bij elke sessie

Lees deze bestanden VOLLEDIG voordat je ook maar één regel code schrijft:

1. `CLAUDE.md` (dit bestand)
2. `docs/product/REQUIREMENTS.md` — contract-eisen en mijlpalen
3. `docs/product/FSD.md` — volledig functioneel platformoverzicht (opdrachtgever)
4. `docs/architecture/STACK.md` — tech stack en waarom
5. `docs/development/TRAPS.md` — fouten die je NIET mag maken
6. `docs/product/ROADMAP.md` — fases en definitie of done
7. `docs/development/PROGRESS.md` — huidige status

Volledige documentatie-index: [docs/README.md](./docs/README.md)

Daarna: **vat samen wat je hebt gelezen en vraag om bevestiging voordat je begint.**

Zeg letterlijk: "Ik heb alle context gelezen. We zijn nu in [fase X.X]. Ik ga [dit] doen. Akkoord?"

---

## Over dit project

**Vermogenspeil** is een Nederlandse fintech webapplicatie voor beleggers. Het stelt gebruikers in staat hun volledige vermogen te tracken en Box 3 belastingaangiftes voor te bereiden.

Dit is een productie-klaar platform dat echte financiële data van echte gebruikers verwerkt. Fouten in belastingberekeningen hebben directe gevolgen voor gebruikers. Elke berekening moet correct, herhaalbaar en verifieerbaar zijn.

---

## Kernprincipes

**Nooit shortcuts nemen.** Als iets complex is, bouw het dan correct. Schrijf geen `# TODO: implement later` en ga door.

**Belastinglogica is kritisch.** Box 3 berekeningen moeten exact kloppen met de Nederlandse belastingwetgeving. Twijfel je? Stop en vraag.

**Security first.** Dit platform slaat API keys op van brokers. AES-256 encryptie is niet optioneel.

**Test alles.** Elke module krijgt unit tests. Geen uitzonderingen.

**GDPR.** Gebruikersdata moet verwijderbaar zijn. Bouw dit vanaf het begin in, niet als afterthought.

---

## Wat je NIET doet

- Geen hardcoded secrets of API keys in code
- Geen mock data in productie
- Geen `print()` statements als logging
- Geen bare `except:` zonder specifieke exception handling
- Geen synchrone calls naar externe APIs in request handlers
- Geen belastingberekeningen zonder unit tests
- Geen deployment zonder environment variables in Render/Vercel

---

## Sessie einde ritual

Aan het einde van elke sessie:
1. Update `docs/development/PROGRESS.md` met wat er gedaan is
2. Lijst openstaande TODO's
3. Beschrijf de exacte volgende stap voor de volgende sessie
4. Commit alle wijzigingen met een duidelijke commit message

---

## Als je vastloopt

Stop. Schrijf niet door. Vraag specifiek wat je nodig hebt. Beschrijf het probleem in één zin.
