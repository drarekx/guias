"""Inyecta el bloque del bestiario en data/games/ff9/guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BESTIARIO = ROOT / "data/games/ff9/bestiario.json"
GUIDE = ROOT / "data/games/ff9/guide.json"


def to_cell(name: str, url: str) -> dict:
    return {"text": name, "href": url}


def build_table(items: list[dict], header: str) -> list:
    rows = [[to_cell(header, "")]]  # placeholder header sin link; override abajo
    rows = [[header]]
    rows.extend([[to_cell(it["nombre"], it["url"])] for it in items])
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(BESTIARIO.read_text(encoding="utf-8"))
    normales = data["normales"]
    jefes = data["jefes"]
    bondadosos = data["bondadosos"]
    src = data["_source"]

    blocks: list[dict] = [
        {"type": "p",
         "text": "Listado de enemigos de Final Fantasy IX. Cada nombre enlaza a su ficha en la Final Fantasy Wiki (búsqueda) o a su página individual cuando existe."},
        {"type": "h3", "text": f"Enemigos normales ({len(normales)})"},
        build_table(normales, "Nombre"),
        {"type": "h3", "text": f"Jefes ({len(jefes)})"},
        build_table(jefes, "Nombre"),
        {"type": "h3", "text": f"Monstruos bondadosos ({len(bondadosos)})"},
        build_table(bondadosos, "Nombre"),
        {"type": "p",
         "text": f"Fuente: {src}."},
    ]

    return {
        "slug": "ff9-bestiario",
        "disc": "Extras",
        "title": "Bestiario",
        "href": "final-fantasy-ix_bestiario.php",
        "content": {
            "title": "Guía Final Fantasy IX",
            "intro": "",
            "image": None,
            "blocks": blocks,
        },
    }


def main() -> None:
    page = build_page()
    guide = json.loads(GUIDE.read_text(encoding="utf-8"))
    # quitar un bestiario previo si existe (idempotente)
    guide = [p for p in guide if p.get("slug") != "ff9-bestiario"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Inyectado ff9-bestiario ({len(page['content']['blocks'])} bloques)")


if __name__ == "__main__":
    main()
