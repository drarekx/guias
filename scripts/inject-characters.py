"""Inyecta la pagina de characters en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/characters.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/characters). "
    "Stats y equipo del juego; descripciones re-escritas en espanol rioplatense."
)


def build_playable_table(characters: list[dict]) -> dict:
    headers = ["Personaje", "Equipo", "Comandos", "Ultimate", "Stats"]
    rows = [headers]
    for c in characters:
        stats = f"Strong: {c['strong']}. Weak: {c['weak']}."
        rows.append([
            c["name"],
            f"W: {c['weapon']}\nA: {c['armor']}",
            ", ".join(c["commands"]),
            c["ultimate"],
            stats,
        ])
    return {"type": "table", "rows": rows}


def build_temporary_table(temps: list[dict]) -> dict:
    headers = ["Personaje", "Donde", "Equipo"]
    rows = [headers]
    for t in temps:
        rows.append([t["name"], t["where"], t["equipment"]])
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    blocks.append({"type": "h3", "text": "Personajes jugables (8)"})
    blocks.append(build_playable_table(data["playable"]))
    for c in data["playable"]:
        blocks.append({"type": "h4", "text": c["name"]})
        blocks.append({"type": "p", "text": f"Trance: {c['trance']}. Inicial: {c['initial']}."})
        blocks.append({"type": "p", "text": c["notes"]})
    blocks.append({"type": "h3", "text": "Personajes temporales"})
    blocks.append({"type": "p", "text": "Personajes que se unen brevemente al party en secciones especificas del walkthrough."})
    blocks.append(build_temporary_table(data["temporaries"]))
    for t in data["temporaries"]:
        blocks.append({"type": "h4", "text": t["name"]})
        blocks.append({"type": "p", "text": t["role"]})
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-characters",
        "disc": "Extras",
        "title": "Personajes",
        "href": "final-fantasy-ix_characters.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-characters"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"Inyectado ff9-characters ({len(data['playable'])} jugables + {len(data['temporaries'])} temporales)")


if __name__ == "__main__":
    main()