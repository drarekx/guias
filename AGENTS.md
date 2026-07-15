# AGENTS.md — Tomo del Cristal

Guía de contexto para sesiones futuras. Léeme primero antes de tocar nada.

## Qué es esto

Colección de guías de Final Fantasy (FF6/7/8/9/10) construidas con **Astro 5 + Tailwind v4**. Cada juego es un "tomo" con su propia paleta cromática. Contenido scrapeado de `eliteguias.com` por un parser en Python (`scripts/download.py`) → JSON en `data/games/{slug}/`.

Output: estático, deployable a cualquier host. `dist/` pesa ~261 MB / 281 HTML + 1620 imágenes.

## Mapa de archivos clave

```
src/
├── layouts/GuideLayout.astro      # Layout con sidebar, inyecta vars CSS por juego
├── lib/
│   ├── games.ts                   # Registry + themeVars() + lighten()
│   ├── guide.ts                   # import.meta.glob de guide.json/structure.json + CACHE
│   └── search.ts                  # SEARCH_INDEX cross-game (lee en build, no en cliente)
├── pages/
│   ├── index.astro                # Games index
│   ├── 404.astro
│   └── [game]/
│       ├── index.astro            # Home del juego (hero + stats + índice)
│       └── guia/[slug].astro      # Página de capítulo
├── components/
│   ├── Sidebar.astro              # Nav desktop + bottom-bar móvil + drawer TOC
│   ├── Search.astro               # Modal ⌘K con índice inlined ⚠
│   ├── ProgressTracker.astro      # Listener global de [data-progress-toggle] + [data-nav-slug]
│   ├── ReadingProgress.astro      # Barra de scroll ⚠
│   ├── ContentBlocks.astro        # Renderiza blocks (h2/h3/h4/p/ul/ol/img/table)
│   ├── ChapterNav.astro           # Sticky prev/next bajo el header
│   ├── PageNav.astro              # Prev/next al final del artículo
│   ├── Lightbox.astro             # Click en <img> dentro de .prose-guide → modal
│   ├── ThemeToggle.astro          # Toggle dark/light, persistido en localStorage
│   ├── ProgressToggle.astro       # Botón individual de "marcar completado"
│   ├── Breadcrumbs.astro
│   ├── BackToTop.astro
│   ├── Logo.astro                 # Cristal SVG + monograma del juego
│   └── Crystal.astro
├── styles/global.css              # @theme dark + override :root.light, .card, .prose-guide
data/games/{slug}/{guide,structure}.json
scripts/
├── download.py                    # Descargador + parser (game-agnostic)
├── screenshot.mjs                 # Verificador visual con Playwright
└── screenshot-themes.mjs          # Screenshots cross-game
```

## Sistema de temas (lo más importante que NO es obvio)

Cada juego define `theme` en `data/games.json`:
```json
"theme": {
  "primary": { "name": "crystal", "hex": "#9b7aff", "ink": "#2d1f5e" },
  "accent":  { "name": "gold",    "hex": "#e8b75d", "ink": "#5a3a0e" },
  "rose": "#e07a9e", "azure": "#6fb8e8", "ember": "#e88a5a", "crimson": "#d04a5e",
  "emerald": "#6dc899", "void": "#07061a", "bg": "#0c0a1f"
}
```

`GuideLayout.astro:45` inyecta un bloque `<style is:inline>` con:
```css
:root[data-game="ff9"] { --color-crystal: #9b7aff; --color-gold: #e8b75d; ... }
```

Todo el CSS consume `var(--color-*)`. Cambiar de juego = cambiar `data-game` del `<html>` y se repinta todo. **NO hardcodear colores del juego** — usar siempre las custom properties.

`global.css` define los colores neutros (`--color-bg`, `--color-surface-1/2/3`, `--color-text*`, etc.) y se sobreescriben en modo light con pergamino genérico en `:root.light` (líneas 60-78).

## Trucos no obvios

- **`ThemeToggle` se renderiza 2 veces** (sidebar + bottom-bar móvil), por eso usa `__themeInit` global flag para no duplicar listeners. Lo mismo hace `ReadingProgress`. Patrón frágil, ver TODO #10.
- **`Search.astro:4`** usa `define:vars={{ indexJson: JSON.stringify(SEARCH_INDEX) }}` para meter el índice de búsqueda en el cliente. Esto es lo que causa el bloat (ver TODO #1).
- **`guide.ts:6-13`** usa `import.meta.glob` con `eager: true` para cargar todos los JSON en build, los cachea en un `Map` por slug.
- **`isGameAvailable()`** se llama en cada `getStaticPaths` — si un juego no tiene datos, sus rutas no se generan. Por eso en `index.astro` los juegos sin datos aparecen con `pointer-events: none` y label "próximamente".
- **`[slug].astro:69-79`** filtra el primer `h2` que coincide normalizado con el título de la página (muchos capítulos lo repiten).
- **Progreso en localStorage** con key por juego: `guide-progress-{slug}`. `ProgressTracker` es un solo `<script>` global que maneja TODOS los botones `[data-progress-toggle]` y marca TODOS los `[data-nav-slug]` como `.is-completed`.
- **`Logo.astro`** tiene IDs de gradiente (`lg-crystal`, `lgc2`, etc.) que colisionan si el logo se renderiza varias veces en la misma página. Ya está parcialmente mitigado con sufijo `2` en la versión "mark". Cuidado si añadís una tercera variante.

## Convenciones

- TypeScript estricto, sin `any` salvo en `[slug].astro:23` (TODO #2).
- **No** añadir comentarios al código salvo que sean sobre decisiones no obvias (luego los borro yo).
- Tono: español rioplatense neutro, contenido en castellano.
- IDs/anchor de headings: `slugify()` en `ContentBlocks.astro:6-10` — lowercase + sin acentos + `-`.
- Estilos con Tailwind v4 `@theme` + `@layer components`. Preferir CSS vars sobre utility classes hardcoded.

## TODOs priorizados (de la sesión 2026-06-19)

### 🔴 Performance
1. **Extraer `SEARCH_INDEX` a `/search-index.json` estático** y hacer `fetch()` desde `Search.astro`. Hoy cada HTML embebe ~635 KB del índice × 281 páginas = ~178 MB duplicados. **Impacto enorme en el bundle.**
2. **Borrar línea 23 de `[slug].astro`**: `const { game, slug } = { ...Astro.params, ...Astro.props as any };` es código muerto.
3. **`ReadingProgress` debe medir el scroll del `<article>`**, no del `documentElement`. Hoy llega al 100% antes de terminar el contenido real.

### 🟡 UX
4. **Export/import de progreso** desde la sidebar. Botones chiquitos que serialicen `localStorage[KEY]` a un archivo `.json` descargable y permitan re-importarlo. Útil para cambio de navegador/dispositivo.
5. **`@media print` en `global.css`**: esconder sidebar, bottom-bar, ChapterNav, ReadingProgress, Lightbox. Expandir `<main>` a ancho completo. Quitar gradientes del body.
6. **Debounce + word-boundaries en búsqueda** (`Search.astro:75-118`). Regex `\b` con tolerancia a acentos, debounce 80ms. Opcional: toggle "solo este juego".
7. **Swipe-to-close en mobile TOC drawer** (`Sidebar.astro:130-151`). `touchend` con `deltaY < -threshold` cierra.
8. **Botón "marcar sección completa"** en el `<summary>` de cada `details` del Sidebar. Itera los `it.slug` y los togglea todos en el Set.

### 🟢 Polish
9. **Light mode per-game** (en lugar del pergamino genérico). El TODO ya está documentado en `games.ts:57-58`. Cada juego necesitaría su propia paleta light — empezar con FF6 (apocalíptico) y FF10 (acuático) para validar.
10. **Refactor de `__themeInit` / `__readingProgressInit`**: mover a un único `<script>` en el layout, o usar `astro:page-load` para deduplicar listeners.
11. **SEO**: añadir `<meta name="robots">`, `og:image` (usar el hero de cada juego), canonical URL (`<link rel="canonical" href={Astro.url}>`).
12. **404 lightweight**: el `GuideLayout` carga sidebar CSS + componentes para nada. Crear un `MinimalLayout.astro` o hacer que `GuideLayout` no importe los componentes pesados cuando `game` es undefined.

## Cosas que ya sé que NO hay que tocar

- El patrón `define:vars` en Astro (es la forma correcta de pasar datos del frontmatter al `<script is:inline>`).
- El `import.meta.glob` con `eager: true` para auto-descubrir juegos nuevos sin tocar código.
- El doble render del ThemeToggle (es por diseño, no es un bug).

## Cómo añadir un juego nuevo

1. Editar `data/games.json`: añadir entrada con `title`, `slug`, `theme`, `sections` (estructura de páginas con `href` apuntando a eliteguias).
2. `python3 scripts/download.py --game {slug}`.
3. `npm run build` — el `import.meta.glob` recoge el nuevo `guide.json` automáticamente.
4. No requiere tocar código de Astro si la paleta es suficiente con la default.

## Comandos útiles

```bash
npm run dev               # http://127.0.0.1:4321
npm run build             # → dist/ (~261 MB, 281 HTML)
python3 scripts/download.py --game ff9
python3 scripts/download.py --game all
```

## Deploy

En el server corre `scripts/deploy-guias.sh` (instalado en `$PATH` como `deploy-guias`):

```bash
sudo deploy-guias latest      # última release de drarekx/guias
sudo deploy-guias v0.1.2      # release específica
```

Baja el último tag vía la API de GitHub, descarga `tomo-del-cristal-vX.Y.Z.tar.gz`, hace backup de `/var/www/guias`, extrae y recarga nginx. Rollback automático si la verificación falla.

El tarball lo genera `.github/workflows/release.yml` al pushear un tag `v*` (publica `.tar.gz` + `.zip` como assets del release en GitHub).

## MCP server

`scripts/mcp_server.py` expone las guias como tools de Model Context Protocol (stdio) para que agentes LLM (Claude Desktop, Cursor, etc.) las consulten. Lee `data/games/{slug}/{guide,structure,bestiario}.json`. Requiere Python ≥ 3.10.

Setup (una vez):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Tools: `list_games`, `list_structure(game)`, `get_page(game, slug)`, `search_guide(game, query, max_results=10)`, `list_enemies(game, group="all")`, `find_item(game, item_name)`.

Conectar a Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tomo-del-cristal": {
      "command": "/Users/mrdrarek/dev/guia/ff9/.venv/bin/python",
      "args": ["/Users/mrdrarek/dev/guia/ff9/scripts/mcp_server.py"]
    }
  }
}
```

Smoke test: `python3 scripts/test_mcp.py`.

No hay test suite ni linter configurado. El verificador visual es `scripts/screenshot.mjs` (Playwright).
