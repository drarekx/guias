"""
MCP server para Tomo del Cristal.

Expone las guias de los juegos (FF6/7/8/9/10) como tools de Model Context
Protocol, para que agentes LLM (Claude Desktop, Cursor, etc.) puedan
consultarlas.

Tools:
  list_games()                          -> juegos disponibles
  list_structure(game)                  -> TOC por disc
  get_page(game, slug)                  -> contenido completo de una pagina
  search_guide(game, query, max_results=10)
                                         -> busqueda full-text con snippets
  list_enemies(game, group="all")       -> bestiario si existe (ff9 hoy)
  find_item(game, item_name)            -> donde aparece un item/objeto en el walkthrough

Conexion (Claude Desktop / Cursor / etc.) en el cliente MCP:
  command: python3.12 (o el python de tu venv)
  args:    [/path/a/este/repo/scripts/mcp_server.py]

Lee los JSON desde data/games/{slug}/{guide,structure,bestiario}.json.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "games"
REGISTRY = ROOT / "data" / "games.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def available_games() -> list[dict]:
    """Juegos con guide.json presente."""
    if not REGISTRY.exists():
        return []
    reg = _load(REGISTRY)
    out: list[dict] = []
    for g in reg.get("games", []):
        if (DATA / g["slug"] / "guide.json").exists():
            out.append({"slug": g["slug"], "title": g["title"]})
    return out


def load_guide(slug: str) -> list[dict] | None:
    p = DATA / slug / "guide.json"
    return _load(p) if p.exists() else None


def load_structure(slug: str) -> list[dict] | None:
    p = DATA / slug / "structure.json"
    return _load(p) if p.exists() else None


def load_bestiario(slug: str) -> dict | None:
    p = DATA / slug / "bestiario.json"
    return _load(p) if p.exists() else None


def page_plain_text(page: dict) -> str:
    """Concatena el texto de todos los bloques de una pagina en minusculas,
    para indexar/buscar. Espejo de guide.ts:pagePlainText."""
    parts: list[str] = [page["title"], page["disc"], page["content"].get("intro", "")]
    for b in page["content"]["blocks"]:
        t = b["type"]
        if t in ("p", "h2", "h3", "h4"):
            parts.append(b["text"])
        elif t in ("ul", "ol"):
            parts.append(" ".join(b["items"]))
        elif t == "img":
            parts.append(b.get("alt", ""))
            parts.append(b.get("caption", ""))
        elif t == "table":
            cells: list[str] = []
            for row in b["rows"]:
                for c in row:
                    if isinstance(c, str):
                        cells.append(c)
                    else:
                        cells.append(c.get("text", ""))
            parts.append(" ".join(cells))
    return "\n".join(parts).lower()


def snippet_around(text: str, idx: int, before: int = 120, after: int = 220) -> str:
    start = max(0, idx - before)
    end = min(len(text), idx + after)
    return ("…" if start > 0 else "") + text[start:end].strip() + ("…" if end < len(text) else "")


def search_game(slug: str, query: str, max_results: int = 10) -> list[dict]:
    pages = load_guide(slug)
    if not pages:
        return []
    q = query.lower()
    out: list[dict] = []
    for page in pages:
        text = page_plain_text(page)
        idx = text.find(q)
        if idx == -1:
            continue
        out.append({
            "slug": page["slug"],
            "title": page["title"],
            "disc": page["disc"],
            "snippet": snippet_around(text, idx),
        })
        if len(out) >= max_results:
            break
    return out


app = Server("tomo-del-cristal")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="list_games", description="Lista los juegos disponibles con sus slugs.",
             inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="list_structure", description="Lista el TOC (structure) de un juego por disc.",
             inputSchema={"type": "object",
                          "properties": {"game": {"type": "string", "description": "slug (ff6/ff7/ff8/ff9/ff10)"}},
                          "required": ["game"]}),
        Tool(name="get_page", description="Devuelve el contenido completo de una pagina.",
             inputSchema={"type": "object",
                          "properties": {"game": {"type": "string"}, "slug": {"type": "string", "description": "slug de la pagina (ej. ff9-p2)"}},
                          "required": ["game", "slug"]}),
        Tool(name="search_guide", description="Busqueda full-text con snippets. Case-insensitive.",
             inputSchema={"type": "object",
                          "properties": {
                              "game": {"type": "string"},
                              "query": {"type": "string"},
                              "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                          },
                          "required": ["game", "query"]}),
        Tool(name="list_enemies", description="Lista el bestiario si existe (ff9 tiene; otros no).",
             inputSchema={"type": "object",
                          "properties": {
                              "game": {"type": "string"},
                              "group": {"type": "string", "enum": ["all", "normales", "jefes", "bondadosos"], "default": "all"},
                          },
                          "required": ["game"]}),
        Tool(name="find_item", description="Busca donde se consigue/consigue un item en el walkthrough.",
             inputSchema={"type": "object",
                          "properties": {"game": {"type": "string"}, "item_name": {"type": "string"}},
                          "required": ["game", "item_name"]}),
    ]


def _text(s: str) -> list[TextContent]:
    return [TextContent(type="text", text=s)]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "list_games":
            games = available_games()
            if not games:
                return _text("No hay juegos con datos cargados.")
            return _text("\n".join(f"- {g['slug']}: {g['title']}" for g in games))

        if name == "list_structure":
            slug = arguments["game"]
            struct = load_structure(slug)
            if struct is None:
                return _text(f"Juego '{slug}' no encontrado.")
            lines: list[str] = []
            for sec in struct:
                lines.append(f"\n## {sec['disc']}")
                for it in sec["items"]:
                    lines.append(f"  - {it['slug']}: {it['title']}")
            return _text("\n".join(lines))

        if name == "get_page":
            slug = arguments["game"]
            page_slug = arguments["slug"]
            pages = load_guide(slug)
            if pages is None:
                return _text(f"Juego '{slug}' no encontrado.")
            page = next((p for p in pages if p["slug"] == page_slug), None)
            if page is None:
                available = ", ".join(p["slug"] for p in pages[:5]) + ", ..."
                return _text(f"Pagina '{page_slug}' no encontrada en {slug}. Disponibles: {available}")
            return _text(json.dumps(page, ensure_ascii=False, indent=2))

        if name == "search_guide":
            slug = arguments["game"]
            query = arguments["query"]
            max_r = arguments.get("max_results", 10)
            matches = search_game(slug, query, max_r)
            if not matches:
                return _text(f"Sin resultados para '{query}' en {slug}.")
            lines = [f"Resultados para '{query}' en {slug} ({len(matches)}):"]
            for m in matches:
                lines.append(f"\n### {m['title']} [{m['disc']}] — slug: {m['slug']}")
                lines.append(m["snippet"])
            return _text("\n".join(lines))

        if name == "list_enemies":
            slug = arguments["game"]
            group = arguments.get("group", "all")
            best = load_bestiario(slug)
            if best is None:
                return _text(f"No hay bestiario para '{slug}' (solo ff9 lo tiene hoy).")
            lines: list[str] = []
            if group in ("all", "normales"):
                normales = best["normales"]
                lines.append(f"## Enemigos normales ({len(normales)})")
                lines.append("\n".join(f"- {n['nombre']}" for n in normales))
            if group in ("all", "jefes"):
                jefes = best["jefes"]
                lines.append(f"\n## Jefes ({len(jefes)})")
                lines.append("\n".join(f"- {n['nombre']}" for n in jefes))
            if group in ("all", "bondadosos"):
                b = best["bondadosos"]
                lines.append(f"\n## Monstruos bondadosos ({len(b)})")
                lines.append("\n".join(f"- {n['nombre']}" for n in b))
            return _text("\n".join(lines))

        if name == "find_item":
            slug = arguments["game"]
            item = arguments["item_name"]
            matches = search_game(slug, item, max_results=15)
            if not matches:
                return _text(f"'{item}' no aparece en el walkthrough de {slug}.")
            lines = [f"Donde aparece '{item}' en {slug}:"]
            for m in matches:
                lines.append(f"\n### {m['title']} [{m['disc']}]")
                lines.append(m["snippet"])
            return _text("\n".join(lines))

        return _text(f"Tool desconocida: {name}")
    except Exception as e:  # noqa: BLE001
        return _text(f"Error: {e!r}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())