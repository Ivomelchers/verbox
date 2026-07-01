# DESIGN.md — Design System MijnVermogen / Vermogenspeil

> **Implementatie:** `frontend/src/theme.ts`  
> **Visuele referentie (opdrachtgever):** `MijnVermogen-Gratis-v4.html` en `MijnVermogen-Premium-v4.html` (repo root)  
> **Functionele specificatie:** [FSD.md](../product/FSD.md)
> **Componenten:** `frontend/src/components/common/`  
> **Geen aparte CSS-bestanden** — alles via `theme/index.ts`.

## Filosofie

Dit platform is een fiscaal instrument, geen lifestyle-app. Het voelt als een notarisbrief, een jaarrekening, een serieus financieel document — niet als een crypto-app of startup-product.

Elke designbeslissing ondersteunt één gevoel: **dit klopt, dit vertrouw ik, dit is voor serieus geld.**

Light mode is het visuele fundament. Dark mode is out of scope tot expliciet gevraagd.

---

## Kleurpalet

### Achtergrond & Tekst

| Design token | Chakra token | Hex | Gebruik |
|--------------|--------------|-----|---------|
| Background | `background` | `#FAFAF7` | Pagina — warm papier, geen browser-wit |
| Background Card | `backgroundCard` | `#F3F1EC` | Cards, panels, sidebar |
| Background Hover | `backgroundHover` | `#E8E5DD` | Hover rijen, nav-items, icon achtergronden |
| Paper | `paper` | `#FFFFFF` | Tekst op azure/goud buttons |
| Ink Primary | `ink.primary` | `#14213D` | Primaire tekst — diep marineblauw, nooit `#000` |
| Ink Dim | `ink.dim` | `#4A5878` | Secundaire tekst, beschrijvingen |
| Ink Faint | `ink.faint` | `#8892A6` | Labels, kickers, metadata |

### Drager — Marineblauw

| Design token | Chakra token | Hex | Gebruik |
|--------------|--------------|-----|---------|
| Azure | `azure.500` | `#1E3A5F` | CTA's, links, branding, actieve accenten |
| Azure Bright | `azure.600` | `#2C4D7A` | Hover op CTA's |
| Azure Deep | `azure.700` | `#102542` | Diepe accenten |
| Azure Dim | `azure.50`–`azure.100` | rgba | Notities, subtiele achtergronden |

### Premium Anker — Goud

| Design token | Chakra token | Hex | Gebruik |
|--------------|--------------|-----|---------|
| Gold | `gold.500` | `#B8934E` | **Alleen** premium: crown, PRO-badge, upgrade |
| Gold Bright | `gold.600` | `#CBA461` | Hover premium-elementen |

> ⚠️ Goud mag **nergens** anders verschijnen. Geen gouden CTA's buiten premium-momenten.

### Performance — Winst & Verlies

| Design token | Chakra token | Hex | Gebruik |
|--------------|--------------|-----|---------|
| Moss | `moss.500` | `#4A7A4E` | Winst, positief rendement |
| Rust | `rust.500` | `#8B3A2A` | Verlies — bewust gedempt (loss aversion) |

### Secundair

| Design token | Chakra token | Hex | Gebruik |
|--------------|--------------|-----|---------|
| Taupe | `taupe.500` | `#6B6F7A` | Meta, neutrale staten |
| Line | `line.DEFAULT` | `#D6D3CA` | Randen, tabellen |
| Line Soft | `line.soft` | `#E4E1D7` | Subtiele scheidingen |

---

## Typografie

### Google Fonts (`index.html`)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,500;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,500&display=swap" rel="stylesheet">
```

### Rollen

| Rol | Font | Chakra | Gebruik |
|-----|------|--------|---------|
| Display & headings | Source Serif 4 | `fonts.heading` / `<Heading>` | Pagina-titels, belasting-"antwoord", hero waarden |
| Body & UI | Inter 300–700 | `fonts.body` | Tekst, nav, forms, buttons |
| Kickers | Inter uppercase | `<Kicker>` component | Sectielabels, breadcrumbs |
| Tabular cijfers | Inter + tnum | `<MoneyText variant="tabular\|delta">` | Kolommen, deltas, tabelbedragen |
| Display cijfers | Source Serif 4 | `<MoneyText variant="display">` | Grote net worth / belastingbedrag |

**Nooit** monospace coding fonts. Tabular-nums binnen Inter voor financiële kolommen.

---

## Afmetingen & Effecten

| Eigenschap | Waarde | Chakra |
|------------|--------|--------|
| Border radius | **4px** (cards, buttons, nav) | `radii.base` / `borderRadius="base"` |
| Kleine radius | 2px | `radii.sm` |
| Avatar / dot | `full` | `borderRadius="full"` |
| Shadow max | Subtiel | `shadows.sm` of `shadows.md` — nooit groter |
| Transitions | **150ms ease** | hardcoded in `theme.ts` |
| Papier-texture | `.app-shell::before/::after` | Global styles in theme — **niet dupliceren** |

---

## Layouts

Twee layouts — **nooit mixen op één pagina**.

| Layout | Bestand | Routes | Kenmerken |
|--------|---------|--------|-----------|
| **PublicLayout** | `PublicLayout.tsx` | `/`, `/login`, `/register` | Geen sidebar, header met logo + auth links |
| **AppLayout** | `AppLayout.tsx` | `/dashboard`, toekomstige app-routes | Sidebar 240px, topbar, peildatum-chip |

Sidebar-nav: `Button variant="ghostNav"`. Actief item: `backgroundHover` + azure lijn links.

Brand: **Mijn** + *Vermogen* (italic, `azure.500`) via `<BrandMark />`.

---

## Chakra Theme

Enige bron: **`frontend/src/theme.ts`** — kleuren, global styles, component variants. Geen aparte CSS-bestanden.

Import:

```typescript
import theme from "./theme";
```

### Button variants

| Variant | Gebruik |
|---------|---------|
| `fiscal` | Primaire CTA (azure) |
| `fiscalOutline` | Secundaire actie |
| `premium` | **Alleen** premium upgrade — goud |
| `ghostNav` | Sidebar navigatie |

### Badge variants

| Variant | Gebruik |
|---------|---------|
| `premium` | PRO-badge — goud |

---

## Verplichte Shared Components

**Gebruik deze componenten.** Geen inline styling dupliceren.

| Component | Bestand | Wanneer |
|-----------|---------|---------|
| `Kicker` | `Kicker.tsx` | Uppercase sectielabels, breadcrumbs |
| `MoneyText` | `MoneyText.tsx` | Alle geldbedragen en rendement |
| `FiscalCard` | `FiscalCard.tsx` | Panels, insight cards, auth cards |
| `BrandMark` | `BrandMark.tsx` | Logo overal |
| `PublicLayout` | `PublicLayout.tsx` | Publieke pagina's |
| `AppLayout` | `AppLayout.tsx` | Ingelogde app |
| `Sidebar` | `Sidebar.tsx` | Alleen via AppLayout |

### Voorbeelden

```tsx
// Kicker
<Kicker>Belastingjaar 2026 · Forfaitair stelsel</Kicker>

// Groot bedrag (hero / belasting-antwoord)
<MoneyText variant="display">€174</MoneyText>

// Tabel / delta
<MoneyText variant="tabular" tone="positive">+ € 2.341,80</MoneyText>
<MoneyText variant="delta" tone="negative">− € 184,20</MoneyText>

// Card
<FiscalCard p={6}>{children}</FiscalCard>

// CTA
<Button variant="fiscal">Account aanmaken</Button>
<Button variant="fiscalOutline">Inloggen</Button>

// Premium (alleen premium-momenten)
<Badge variant="premium">PRO</Badge>
<Button variant="premium">Upgrade</Button>
```

### Heading

Gebruik `<Heading>` zonder handmatige `fontFamily` — theme zet Source Serif 4 automatisch.

---

## Gratis vs Premium visueel

| Element | Gratis | Premium |
|---------|--------|---------|
| Crown icon (nav) | `azure.500` | `gold.500` |
| PRO badge | — | `Badge variant="premium"` |
| Premium CTA | — | `Button variant="premium"` |

---

## Wat je NIET doet

- Geen pure zwart (`#000000`) — gebruik `ink.primary`
- Geen felle kleuren, decoratieve gradients op componenten, glow-effecten
- Geen goud buiten premium-momenten
- Geen monospace fonts voor cijfers
- Geen border radius groter dan **4px** (behalve `full` voor avatars)
- Geen shadows groter dan `shadows.md`
- Geen animaties behalve **150ms ease** hover transitions
- Geen `global.css` — styling alleen via Chakra theme
- Geen hardcoded hex in components — altijd theme tokens
- Geen nieuwe UI bouwen zonder shared components te hergebruiken

---

## Nieuwe features checklist

Bij elke nieuwe pagina of component:

1. [ ] Juiste layout (`PublicLayout` vs `AppLayout`)
2. [ ] `Kicker`, `MoneyText`, `FiscalCard` gebruikt waar van toepassing
3. [ ] Button variant `fiscal` / `fiscalOutline` (niet default Chakra)
4. [ ] Kleuren via theme tokens (`ink.*`, `azure.*`, `moss.500`, etc.)
5. [ ] Goud alleen als het een premium-moment is
6. [ ] Geen hex literals in JSX
