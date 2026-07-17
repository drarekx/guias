"""Inyecta la pagina de abilities en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/abilities.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/abilities). "
    "Catalogo compacto de Action y Support abilities; descripciones re-escritas en espanol rioplatense."
)


def build_action_table(abilities: list[dict]) -> dict:
    headers = ["Command", "Ability", "MP", "Quien", "Aprende de", "Efecto"]
    rows = [headers]
    for a in abilities:
        rows.append([
            a["cmd"],
            a["name"],
            str(a.get("mp", 0)),
            a.get("user", ""),
            a.get("learn", ""),
            a.get("effect", ""),
        ])
    return {"type": "table", "rows": rows}


def build_support_table(abilities: list[dict]) -> dict:
    headers = ["Ability", "Efecto", "Aprende de"]
    rows = [headers]
    for a in abilities:
        rows.append([a["name"], a["effect"], a.get("learn", "")])
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    blocks.append({"type": "h3", "text": "Action Abilities"})
    blocks.append({"type": "p", "text": "Habilidades que gastan ATB durante la batalla. Agrupadas por command (Steal, Skill, Blk Mag, Swd Art, Summon, Wht Mag, Jump, Dragon, Blu Mag, Flair, etc)."})
    blocks.append(build_action_table(data["action_abilities"]))
    blocks.append({"type": "h3", "text": "Support Abilities"})
    blocks.append({"type": "p", "text": "Habilidades pasivas siempre activas mientras el item que las ensena esta equipado. Killer abilities (Bird/Dragon/etc) son muy utiles para subir el damage contra tipos especificos."})
    blocks.append(build_support_table(data["support_abilities"]))
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-abilities",
        "disc": "Extras",
        "title": "Abilities",
        "href": "final-fantasy-ix_abilities.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-abilities"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"Inyectado ff9-abilities ({len(data['action_abilities'])} action + {len(data['support_abilities'])} support)")


if __name__ == "__main__":
    main()