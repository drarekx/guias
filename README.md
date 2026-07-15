# Tomo del Cristal

Guías walkthrough de Final Fantasy (FF6 / FF7 / FF8 / FF9 / FF10) en español rioplatense. Contenido scrapeado de [eliteguias.com](https://www.eliteguias.com) y, para FF9, un bestiario extraído de la [Final Fantasy Wiki](https://finalfantasy.fandom.com/es/) (CC-BY-SA).

Stack: **Astro 5 + Tailwind v4**. Output 100% estático (`dist/`), deployable a cualquier host.

## Quick start

```bash
npm install
npm run dev          # http://127.0.0.1:4321
npm run build        # → dist/ (~261 MB)
npm run preview      # sirve dist/ local
```

Re-scrapear datos:

```bash
python3 scripts/download.py --game ff9
python3 scripts/download.py --game all
```

## MCP server

`scripts/mcp_server.py` expone la guía como tools de [Model Context Protocol](https://modelcontextprotocol.io/) (stdio, Python ≥ 3.10), para que agentes LLM como Claude Desktop o Cursor las consulten.

### Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Tools

| Tool | Input | Devuelve |
|---|---|---|
| `list_games` | — | slugs y títulos disponibles |
| `list_structure` | `game` | TOC por disc con slugs |
| `get_page` | `game`, `slug` | contenido completo (h2/h3/p/table/ul) |
| `search_guide` | `game`, `query`, `max_results?` | snippets con match |
| `list_enemies` | `game`, `group?` (`all`/`normales`/`jefes`/`bondadosos`) | bestiario (solo FF9) |
| `find_item` | `game`, `item_name` | páginas donde aparece un item en el walkthrough |

`search_guide` y `find_item` son case-insensitive. Cada celda linkable de las tablas (ej. nombres de enemigos del bestiario) también se indexa.

### Conectar a Claude Desktop

Editá `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Reiniciá Claude Desktop y las 6 tools aparecen en el selector de tools.

### Conectar a Cursor

Settings → Features → Model Context Protocol → Add new MCP server con la misma `command` y `args`.

### Smoke test

```bash
.venv/bin/python scripts/test_mcp.py
```

Ejecuta 6 invocaciones round-trip (initialize + tools/list + 4 tools/call) por stdio y muestra el output.

## Deploy

En el server corre `scripts/deploy-guias.sh` (instalado en `$PATH` como `deploy-guias`):

```bash
sudo deploy-guias latest      # última release de drarekx/guias
sudo deploy-guias v0.1.2      # release específica
```

Baja el tarball `tomo-del-cristal-vX.Y.Z.tar.gz` del último release, hace backup de `/var/www/guias`, extrae y recarga nginx. Rollback automático si la verificación falla.

El tarball lo genera `.github/workflows/release.yml` al pushear un tag `v*`.

## Estructura del proyecto

```
src/
├── layouts/GuideLayout.astro       # inyecto vars CSS por juego
├── lib/{games,guide,search}.ts     # registry, loaders, search index
├── pages/[game]/guia/[slug].astro  # rutas estaticas
└── components/                     # Sidebar, Search, ContentBlocks, ...

data/games/{slug}/
├── guide.json                      # contenido (93 paginas en ff9)
├── structure.json                  # TOC por disc
└── bestiario.json                  # solo ff9 (CC-BY-SA desde.fandom)

scripts/
├── download.py                     # scraper eliteguias
├── fetch-bestiario.py              # scraper MediaWiki API para bestiario
├── inject-bestiario.py             # inyecta bloque bestiario en guide.json
├── mcp_server.py                   # MCP server (stdio)
└── test_mcp.py                     # smoke test
```

Ver `AGENTS.md` para contexto extendido (sistema de temas, trucos no obvios, TODOs priorizados).

## Atribución

- Walkthroughs: [Eliteguias](https://www.eliteguias.com)
- Bestiario de FF9: [Final Fantasy Wiki](https://finalfantasy.fandom.com/es/) (CC-BY-SA)
