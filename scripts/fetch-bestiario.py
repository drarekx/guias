"""
Saca la lista de enemigos de FF9 desde fandom.com (CC-BY-SA).

Lee la pagina 'Lista de enemigos de Final Fantasy IX' via la API de MediaWiki
en modo wikitext. Cada seccion esta delimitada por '==LETRA=='. El contenido
tiene los nombres concatenados sin espacio ('Ballena ZombiBasiliscoBégimo...').

Spliteamos por frontera minuscula->Mayuscula sin espacio y post-procesamos
sufijos como 'A', 'II', 'No. 1' (variantes 'Mago Negro A/B/C').

Fuente: Final Fantasy Wiki (es.finalfantasy.fandom.com), bajo CC-BY-SA.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import requests

API = "https://finalfantasy.fandom.com/es/api.php"
PAGE = "Lista de enemigos de Final Fantasy IX"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "games" / "ff9" / "bestiario.json"


def fetch_wikitext() -> str:
    r = requests.get(
        API,
        params={"action": "parse", "page": PAGE, "format": "json", "prop": "wikitext"},
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (ff9-guia bestiario one-shot)"},
    )
    r.raise_for_status()
    return r.json()["parse"]["wikitext"]["*"]


def wiki_url_for(name: str) -> str:
    quoted = name.replace(" ", "+").replace("(", "%28").replace(")", "%29")
    return f"https://finalfantasy.fandom.com/es/wiki/Special:Search?query={quoted}"


def parse_gallery(body: str) -> list[str]:
    """Extrae display names de un <gallery>...</gallery> de MediaWiki.

    Cada linea es tipo:
      Imagen:Nombre_archivo.ext|Display name
    Devuelve solo los display names (lo que va despues del ultimo '|').
    """
    out: list[str] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("Imagen:"):
            continue
        if "|" not in line:
            continue
        display = line.rsplit("|", 1)[-1].strip()
        if display:
            out.append(display)
    return out


def main() -> None:
    wikitext = fetch_wikitext()

    # Sections: separados por '==HEADER==' en sus propios lines.
    # Devuelve [(header, body)]
    sections: list[tuple[str, str]] = []
    current_header = "_"
    current_body: list[str] = []
    for line in wikitext.split("\n"):
        m = re.match(r"^==\s*(.+?)\s*==\s*$", line)
        if m:
            sections.append((current_header, "\n".join(current_body)))
            current_header = m.group(1).strip()
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_header, "\n".join(current_body)))

    normales: list[dict] = []
    jefes: list[str] = []
    bondadosos: list[str] = []

    for header, body in sections:
        # Limpiar body: quitar markup, refs, links
        cleaned = body
        cleaned = re.sub(r"<ref[^>]*/?>", "", cleaned)
        cleaned = re.sub(r"<ref[^>]*>.*?</ref>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\[\[[^]]*\|([^]]+)\]\]", r"\1", cleaned)
        cleaned = cleaned.replace("[[", "").replace("]]", "")
        cleaned = cleaned.replace("'''", "").replace("''", "")
        cleaned = re.sub(r"={3,}[^=]*={3,}", "", cleaned)
        m_letter = re.match(r"^([A-ZÁÉÍÓÚÑÜ])$", header)
        if m_letter:
            letra = m_letter.group(1)
            nombres = parse_gallery(cleaned)
            for n in nombres:
                normales.append({"nombre": n, "url": wiki_url_for(n), "letra": letra})
        elif header == "Jefes":
            nombres = parse_gallery(cleaned)
            jefes.extend(nombres)
        elif header == "Monstruos bondadosos":
            nombres = parse_gallery(cleaned)
            bondadosos.extend(nombres)

    payload = {
        "_source": "Final Fantasy Wiki (es.finalfantasy.fandom.com), CC-BY-SA",
        "normales": normales,
        "jefes": [{"nombre": n, "url": wiki_url_for(n)} for n in jefes],
        "bondadosos": [{"nombre": n, "url": wiki_url_for(n)} for n in bondadosos],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"normales:   {len(payload['normales'])}")
    print(f"jefes:      {len(payload['jefes'])}")
    print(f"bondadosos: {len(payload['bondadosos'])}")
    print()
    print("PRIMEROS 30 NORMALES:")
    for n in payload["normales"][:30]:
        print(f"  [{n['letra']}] {n['nombre']}")
    print()
    print("JEFES:")
    for n in payload["jefes"]:
        print(f"  {n['nombre']}")
    print()
    print("BONDADOSOS:")
    for n in payload["bondadosos"]:
        print(f"  {n['nombre']}")


if __name__ == "__main__":
    main()
