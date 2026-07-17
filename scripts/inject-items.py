"""Inyecta la pagina de items en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/items.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/items). "
    "Catalogo compacto con stats resumidos; descripciones re-escritas en espanol rioplatense."
)


def cell_str(value) -> str:
    """Serializa un item field para una celda."""
    if isinstance(value, bool):
        return "Perdible" if value else ""
    return str(value)


def build_table(items: list[dict]) -> dict:
    """Genera una tabla con columnas: Item, Stats (atk/def/special), Where, Notas."""
    headers = ["Item", "Stats", "Donde", "Notas"]
    rows = [headers]
    for it in items:
        name = it["name"]
        # Stats: combine numeric + ability + special + element + add_status + soul_blade
        stats_parts: list[str] = []
        for key in ("atk", "def", "ability", "soul_blade", "add_status", "element", "special", "effect"):
            if key in it:
                v = it[key]
                if key == "atk":
                    stats_parts.append(f"Atk {v}")
                elif key == "def":
                    stats_parts.append(f"Def {v}")
                elif key == "add_status":
                    stats_parts.append(f"+{v}")
                elif key == "soul_blade":
                    stats_parts.append(f"Soul: {v}")
                elif key == "effect":
                    stats_parts.append(v)
                else:
                    stats_parts.append(v)
        stats = " · ".join(stats_parts)

        where = it.get("where", "")

        flags: list[str] = []
        if it.get("missable"):
            flags.append("Perdible")
        if it.get("unique"):
            flags.append("Unico")
        if it.get("broken"):
            flags.append("Overpowered")
        notes = ", ".join(flags)

        rows.append([name, stats, where, notes])
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    for cat in data["categories"]:
        blocks.append({"type": "h3", "text": cat["title"]})
        if "note" in cat:
            blocks.append({"type": "p", "text": cat["note"]})
        blocks.append(build_table(cat["items"]))
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-items",
        "disc": "Extras",
        "title": "Items",
        "href": "final-fantasy-ix_items.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-items"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    total = sum(len(cat["items"]) for cat in data["categories"])
    print(f"Inyectado ff9-items ({total} items en {len(data['categories'])} categorias)")


if __name__ == "__main__":
    main()