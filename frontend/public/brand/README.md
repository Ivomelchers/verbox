# Verbox brand assets

Bron: design van Ivo. Gebruik alleen deze bestanden voor logo’s in de app (geen eigen varianten).

## Structuur

| Pad | Gebruik |
|-----|---------|
| `favicon.svg` | Browsertab (`index.html`) |
| `icon-tile.svg` | App-tegel, PWA, vierkant icoon |
| `mark/` | Alleen het V-teken (smal, sidebar-compact) |
| `wordmark/` | Alleen het woord “Verbox” |
| `logo/horizontal.svg` | **Standaard** — sidebar & publieke header (licht) |
| `logo/horizontal-reversed.svg` | Donkere achtergronden |
| `logo/stacked.svg` | Login, onboarding, marketing (smal formaat) |
| `tagline/` | “grip op je vermogen en box 3” (los van logo) |

`*-reversed` = lichte lijnen/tekst voor donkere UI.

## In code

```tsx
import { brandPaths, logoSrc } from "../brand/paths";

<img src={logoSrc("horizontal")} alt="Verbox" height={32} />
```

## Niet wijzigen

- Kleuren en verhoudingen in de SVG’s intact laten.
- Geen raster-export nodig voor de webapp; SVG schaalt scherp.
