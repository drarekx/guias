"""Inyecta la pagina de enemies con stats en guide.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/games/ff9/enemies-stats.json"
GUIDE = ROOT / "data/games/ff9/guide.json"

ATTRIB = (
    "Basado en la guia de bover_87 en GameFAQs "
    "(https://gamefaqs.gamespot.com/ps/197338-final-fantasy-ix/faqs/71891/enemy-list). "
    "Bosses y enemigos notables con stats; datos factuales del juego; descripciones re-escritas en espanol rioplatense."
)


def build_table(enemies: list[dict]) -> dict:
    headers = ["Enemigo", "HP", "MP", "NV", "EXP", "AP", "Gil", "Tipo", "Debilidad", "Notas"]
    rows = [headers]
    for e in enemies:
        weakness = e.get("weakness", "")
        if e.get("resistance"):
            weakness += f" (R: {e['resistance']})"
        notes_parts = []
        if e.get("steal_rare") and e["steal_rare"] != "Ore" and e["steal_rare"] != "Nothing":
            notes_parts.append(f"Steal raro: {e['steal_rare']}")
        if e.get("drop_rare") and e["drop_rare"] != "Ore" and e["drop_rare"] != "Nothing":
            notes_parts.append(f"Drop raro: {e['drop_rare']}")
        if e.get("notes"):
            notes_parts.append(e["notes"])
        notes = " | ".join(notes_parts)
        rows.append([
            e["name"],
            str(e["hp"]),
            str(e["mp"]),
            str(e["lvl"]),
            str(e["exp"]),
            str(e["ap"]),
            str(e["gil"]),
            e["type"],
            weakness,
            notes,
        ])
    return {"type": "table", "rows": rows}


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    blocks.append({"type": "p", "text": data["stats_explained"]})
    for disc_key in ("disc_1", "disc_2", "disc_3", "disc_4"):
        disc = data[disc_key]
        blocks.append({"type": "h3", "text": disc["title"]})
        blocks.append(build_table(disc["enemies"]))
    blocks.append({"type": "h3", "text": "Bosses y enemigos notables de CD 4 (extra)"})
    blocks.append({"type": "p", "text": "Ozma es el boss opcional mas dificil del juego. Hades se pelea dos veces (Crystal World + Trance final). Deathguise aparece solo en Memoria Crystal World."})
    blocks.append({"type": "p", "text": "Para los enemigos normales sin stats, ver la pagina Bestiario."})
    blocks.append({"type": "p", "text": ATTRIB})
    return {
        "slug": "ff9-enemies-stats",
        "disc": "Extras",
        "title": "Enemigos (stats)",
        "href": "final-fantasy-ix_enemies_stats.php",
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
    guide = [p for p in guide if p.get("slug") != "ff9-enemies-stats"]
    guide.append(page)
    GUIDE.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    total = sum(len(data[k]["enemies"]) for k in ("disc_1", "disc_2", "disc_3", "disc_4"))
    print(f"Inyectado ff9-enemies-stats ({total} enemigos notables)")


if __name__ == "__main__":
    main()