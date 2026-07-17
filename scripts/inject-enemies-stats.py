"""Inyecta la pagina de enemies con stats en guide.json.

Formato:
- Tabla compacta con stats clave (Enemigo, HP, MP, NV, EXP, AP, Tipo, Debilidad).
- Bullets con notas por boss (steal raro, drop raro, tactica).
- Esto evita el problema de la tabla original con 10 columnas apretadas.
"""
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


def build_stats_table(enemies: list[dict]) -> dict:
    headers = ["Enemigo", "HP", "MP", "NV", "EXP", "AP", "Tipo", "Debilidad"]
    rows = [headers]
    for e in enemies:
        weakness = e.get("weakness", "")
        if e.get("resistance"):
            weakness += f" / R: {e['resistance']}"
        rows.append([
            e["name"],
            str(e["hp"]),
            str(e["mp"]),
            str(e["lvl"]),
            str(e["exp"]),
            str(e["ap"]),
            e["type"],
            weakness,
        ])
    return {"type": "table", "rows": rows}


def build_notes_for(e: dict) -> list[dict]:
    """Genera los bloques de notas para un enemigo."""
    blocks = []
    notes: list[str] = []
    if e.get("steal_rare") and e["steal_rare"] not in ("Ore", "Nothing"):
        notes.append(f"Steal notable: {e['steal_rare']}")
    if e.get("drop_rare") and e["drop_rare"] not in ("Ore", "Nothing"):
        notes.append(f"Drop notable: {e['drop_rare']}")
    if e.get("notes"):
        notes.append(e["notes"])
    if notes:
        blocks.append({"type": "p", "text": " · ".join(notes)})
    return blocks


def build_page() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    blocks: list[dict] = [{"type": "p", "text": data["intro"]}]
    blocks.append({"type": "p", "text": data["stats_explained"]})
    blocks.append({
        "type": "p",
        "text": "Estructura: tabla compacta con stats por enemigo + notas por boss (steal/drop notable/tactica). Para nombres de todos los enemigos normales sin stats, ver la pagina Bestiario.",
    })

    for disc_key in ("disc_1", "disc_2", "disc_3", "disc_4"):
        disc = data[disc_key]
        blocks.append({"type": "h3", "text": disc["title"]})
        blocks.append(build_stats_table(disc["enemies"]))
        # Notas individuales
        for e in disc["enemies"]:
            blocks.append({"type": "h4", "text": e["name"]})
            blocks.extend(build_notes_for(e))

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