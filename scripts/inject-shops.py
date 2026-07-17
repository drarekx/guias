"""Inyecta la pagina de shops en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/shops.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/shops). "
    "Catalogo compacto de tiendas con items notables y precios; descripciones re-escritas en espanol rioplatense."
)


def build_table(shop: dict) -> dict:
    is_synth = any("ingredients" in it for it in shop["items"])
    if is_synth:
        headers = ["Item", "Ingredientes", "Costo"]
        rows = [headers]
        for it in shop["items"]:
            rows.append([
                it["name"],
                it.get("ingredients", ""),
                f"{it.get('cost', '?')} gil" if isinstance(it.get('cost'), int) else it.get('cost', ''),
            ])
    else:
        headers = ["Item", "Precio"]
        rows = [headers]
        for it in shop["items"]:
            row = [it["name"]]
            price = it.get("price")
            if isinstance(price, int):
                row.append(f"{price} gil")
            else:
                row.append(str(price) if price else "")
            rows.append(row)
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    for shop in data["shops"]:
        blocks.append({"type": "h3", "text": shop["title"]})
        blocks.append({"type": "p", "text": shop["where"]})
        if "note" in shop:
            blocks.append({"type": "p", "text": shop["note"]})
        blocks.append(build_table(shop))
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-shops",
        "disc": "Extras",
        "title": "Tiendas",
        "href": "final-fantasy-ix_shops.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-shops"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = sum(len(s["items"]) for s in data["shops"])
    print(f"Inyectado ff9-shops ({items} items en {len(data['shops'])} tiendas)")


if __name__ == "__main__":
    main()