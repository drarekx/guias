# Tomo del Cristal — Guías de Final Fantasy

Una **colección de guías modernas, rápidas y visualmente memorables** de Final Fantasy, construida con Astro 5 + Tailwind v4. Cada guía es un "tomo" del mismo arco visual pero con su propia paleta cromática. El contenido se adapta de [Eliteguias](https://www.eliteguias.com).

## 🎮 Guías disponibles

| Juego | Año | Paleta | Capítulos |
|---|---|---|---|
| **Final Fantasy IX** | 2000 | Cristal violeta + Tantalus gold | 74 |
| **Final Fantasy VII** | 1997 | Mako green + Ember | 28 |
| **Final Fantasy VIII** | 1999 | Lionheart blue + Rose | 66 |
| **Final Fantasy X** | 2001 | Spira teal + Yuna pink | 52 |
| **Final Fantasy VI** | 1994 | Maduin ember + Crimson | 54 |

## ✨ Features

- **🔍 Búsqueda global cross-game** con `⌘K` o `/`, ranking por relevancia y resaltado.
- **🌗 Dark/Light mode** (dark por defecto, light = pergamino).
- **📑 Sidebar TOC** por juego con secciones colapsables, items activos y progreso.
- **✅ Marcador de progreso** por juego, persistido en `localStorage`.
- **➡️ Anterior/Siguiente** + migas de pan (Juego › CD/Sección › Capítulo).
- **🖼️ Lightbox** para todas las imágenes.
- **📱 Responsive** con bottom-bar en móvil.
- **🚀 100% estático** + sitemap automático.

## 🛠️ Stack

- **[Astro 5](https://astro.build)** + `getStaticPaths` dinámico
- **[Tailwind CSS v4](https://tailwindcss.com)** con `@theme` y variables por juego
- **TypeScript** estricto
- **Python 3** (BeautifulSoup) para el parser de eliteguias
- **Google Fonts**: Cinzel (display), Spectral (body), Manrope (UI), JetBrains Mono (datos)

## 🚀 Quick start

```bash
# 1) Instalar dependencias
npm install

# 2a) Descargar TODAS las guías (5 juegos, ~30 min, ~45 MB de imágenes)
python3 scripts/download.py --game all

# 2b) O descarga solo un juego
python3 scripts/download.py --game ff7

# 3) Dev server
npm run dev   # → http://127.0.0.1:4321

# 4) Build de producción
npm run build
```

## 📂 Estructura

```
ff9/
├── scripts/
│   ├── download.py            # Descargador + parser (game-agnostic)
│   ├── screenshot.mjs         # Verificador visual con Playwright
│   └── screenshot-themes.mjs  # Screenshots cross-game
├── data/
│   ├── games.json             # Registry: juegos, paletas, secciones
│   └── games/
│       ├── ff9/{guide.json, structure.json, raw/}
│       ├── ff7/...
│       ├── ff8/...
│       ├── ff10/...
│       └── ff6/...
├── public/
│   ├── favicon.svg
│   └── img/
│       ├── ff9/  (~310 imágenes)
│       ├── ff7/  (~170 imágenes)
│       ├── ff8/  (~300 imágenes)
│       ├── ff10/ (~190 imágenes)
│       └── ff6/  (~655 imágenes)
├── src/
│   ├── components/
│   │   ├── BackToTop.astro
│   │   ├── Breadcrumbs.astro
│   │   ├── ContentBlocks.astro
│   │   ├── Crystal.astro
│   │   ├── Lightbox.astro
│   │   ├── Logo.astro
│   │   ├── PageNav.astro
│   │   ├── ProgressToggle.astro
│   │   ├── ProgressTracker.astro
│   │   ├── Search.astro
│   │   ├── Sidebar.astro
│   │   └── ThemeToggle.astro
│   ├── layouts/
│   │   └── GuideLayout.astro
│   ├── lib/
│   │   ├── games.ts           # Registry + temas
│   │   ├── guide.ts           # Data loaders por juego
│   │   └── search.ts          # Índice cross-game
│   ├── pages/
│   │   ├── 404.astro
│   │   ├── index.astro        # Games index (list de todos)
│   │   └── [game]/
│   │       ├── index.astro    # Home de cada juego
│   │       └── guia/
│   │           └── [slug].astro
│   └── styles/
│       └── global.css         # Tailwind v4 + tema
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

## 🎨 Sistema de temas

Cada juego tiene su **paleta** definida en `data/games.json`:

```json
"theme": {
  "primary":   { "name": "crystal", "hex": "#9b7aff", "ink": "#2d1f5e" },
  "accent":    { "name": "gold",    "hex": "#e8b75d", "ink": "#5a3a0e" },
  "rose": "#e07a9e", "azure": "#6fb8e8", ...
}
```

El layout inyecta estas variables en `:root[data-game="ff9"]` (o el slug correspondiente) y todo el CSS consume `var(--color-crystal)`, `var(--color-gold)`, etc. Cambiar de juego = cambiar el `data-game` del `<html>` y se repinta todo.

**Paletas actuales:**
- **FF9** — Cristal violeta + Tantalus gold (medieval, mágico)
- **FF7** — Mako green + Ember (corporativo, post-apocalíptico)
- **FF8** — Lionheart blue + Rose (romántico, futurista)
- **FF10** — Spira teal + Yuna pink (religioso, acuático)
- **FF6** — Maduin ember + Crimson (épico, decrépito)

## 🔧 Cómo añadir un juego nuevo

1. **Editar `data/games.json`**: añadir entrada con `title`, `slug`, `theme`, `sections` (estructura de páginas con `href` apuntando a eliteguias).
2. **Descargar**: `python3 scripts/download.py --game {slug}`.
3. **Build**: `npm run build` — el `import.meta.glob` en `src/lib/guide.ts` recoge automáticamente `data/games/{slug}/guide.json`.

No requiere tocar código de Astro si la paleta es suficiente con la paleta por defecto (FF9). Para un tema visual único, edita `theme` en el registro.

## 🔍 Búsqueda

`src/lib/search.ts` genera un índice con todos los capítulos de todos los juegos en build time. El modal ⌘K busca en cliente (vanilla JS) sobre ese índice, con ranking por nº de matches + bonus por match en título/heading. Cada resultado muestra el badge del juego (FF9, FF7, etc.).

## 🚢 Despliegue

Build estático (`dist/`) en cualquier host:

```bash
npm run build
# → dist/ con 281 HTML + 1620 imágenes (~280 MB)
```

Funciona en Cloudflare Pages, Vercel, Netlify, GitHub Pages. El `sitemap-index.xml` se genera automáticamente.

## 📝 Créditos

- **Contenido**: adaptado de la guía de [Eliteguias](https://www.eliteguias.com) © Eliteguias.
- **Juegos**: *Final Fantasy* © Square Enix.
- **Esta guía**: proyecto fan-made sin ánimo de lucro.

## 📜 Licencia del código

MIT — siéntete libre de reutilizar la arquitectura (no el contenido de Eliteguias).
