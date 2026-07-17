"""Inyecta la pagina de otros minijuegos en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/otros-minijuegos.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/sidequests-mini-games). "
    "Items y ubicaciones son datos factuales del juego; descripciones re-escritas en espanol rioplatense."
)


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [
        {"type": "p", "text": data["intro"]},
    ]
    for g in data["games"]:
        blocks.append({"type": "h3", "text": g["title"]})
        blocks.append({"type": "p", "text": f"Donde: {g['where']}. Recompensa: {g['reward']}."})
        for par in g["how"].split("\n\n"):
            par = par.strip()
            if par:
                blocks.append({"type": "p", "text": par})
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-otros-minijuegos",
        "disc": "Extras",
        "title": "Otros minijuegos",
        "href": "final-fantasy-ix_otros-minijuegos.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-otros-minijuegos"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"Inyectado ff9-otros-minijuegos ({len(data['games'])} minijuegos)")


if __name__ == "__main__":
    main()