"""Inyecta la pagina de items perdibles en guide.json.

Lee los missables de data/games/ff9/missables.json (escrito a mano
basado en la guia de gamefaqs de bover_87, re-escritos en espanol)
y los agrega como una nueva pagina en guide.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MISS = ROOT / "data/games/ff9/missables.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Lista consolidada en base a la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/missable-item-walkthrough). "
    "Items y ubicaciones son datos factuales del juego; descripciones re-escritas en espanol rioplatense."
)


def build_page() -> dict:
    data = json.loads(MISS.read_text(encoding="utf-8"))
    blocks: list[dict] = [
        {
            "type": "p",
            "text": "Lista de items y acciones que solo se pueden conseguir o completar una vez en Final Fantasy IX. Si te los perdes, no hay vuelta atras (salvo cargar una partida anterior). Revisala antes de avanzar de CD.",
        },
    ]

    for disc in data["discs"]:
        blocks.append({"type": "h3", "text": f"{disc['title']} ({len(disc['items'])} items)"})
        for i, it in enumerate(disc["items"], 1):
            # Un h4 con el nombre del item + un parrafo con la accion concreta
            blocks.append({"type": "h4", "text": f"{i}. {it['name']}"})
            blocks.append({"type": "p", "text": it["how"]})

    blocks.append({"type": "h3", "text": "Resumen rapido por zona"})
    blocks.append({"type": "p", "text": data.get("resumen", "")})

    blocks.append({"type": "p", "text": ATTRIB})

    return {
        "slug": "ff9-missables",
        "disc": "Extras",
        "title": "Items perdibles",
        "href": "final-fantasy-ix_missables.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-missables"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_miss = sum(len(d["items"]) for d in json.loads(MISS.read_text())["discs"])
    print(f"Inyectado ff9-missables ({n_miss} items en {len(json.loads(MISS.read_text())['discs'])} discs)")


if __name__ == "__main__":
    main()