"""
Descargador + parser de guías de eliteguias.com.

Uso:
  python3 scripts/download.py                      # descarga la muestra MVP de FF9
  python3 scripts/download.py --game ff7           # descarga un juego completo
  python3 scripts/download.py --game all           # descarga todos los juegos del registry
  python3 scripts/download.py --game ff7 --slug ff7-p1  # solo una página

Lee la configuración de data/games.json (registry central).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.eliteguias.com"
ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "games.json"
DATA_DIR = ROOT / "data" / "games"
IMG_ROOT = ROOT / "public" / "img"


# ---- Tipos del registry -----------------------------------------------------
class GameConfig:
    def __init__(self, raw: dict):
        self.slug: str = raw["slug"]
        self.title: str = raw["title"]
        self.baseUrl: str = raw["baseUrl"]
        self.sections: list[dict] = raw["sections"]
        self.theme: dict = raw.get("theme", {})

    def all_items(self) -> list[dict]:
        out = []
        for sec in self.sections:
            for it in sec["items"]:
                out.append(it)
        return out

    def hrefs(self) -> list[str]:
        return [it["href"] for it in self.all_items()]


def load_registry() -> list[GameConfig]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [GameConfig(g) for g in data["games"]]


# ---- MVP: subset para probar rápido -----------------------------------------
MVP_GAME = "ff9"
MVP_SLUGS = {
    "ff9-p1", "ff9-p2", "ff9-p5", "ff9-p9", "ff9-p10", "ff9-p11",
    "ff9-p12", "ff9-p17", "ff9-p25",
    "ff9-chocobos", "ff9-invocaciones", "ff9-cartas", "ff9-ozma", "ff9-gran-caceria",
}


# ---- Sesión HTTP ------------------------------------------------------------
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
})


def fetch(url: str) -> str | None:
    try:
        r = session.get(url, timeout=30)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception as e:
        print(f"  ! error {url}: {e}", file=sys.stderr)
    return None


# ---- Paths por juego --------------------------------------------------------
def game_dirs(game: GameConfig) -> tuple[Path, Path]:
    raw_dir = DATA_DIR / game.slug / "raw"
    img_dir = IMG_ROOT / game.slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, img_dir


# ---- Descarga de HTML -------------------------------------------------------
def download_page(game: GameConfig, href: str, raw_dir: Path) -> str | None:
    url = game.baseUrl + href
    html = fetch(url)
    if not html:
        return None
    out = raw_dir / f"{href}.html"
    out.write_text(html, encoding="utf-8", errors="ignore")
    return str(out)


# ---- Extracción de imágenes del HTML ---------------------------------------
SKIP_IMG_PARENTS = {"nav", "header", "footer", "aside"}


def extract_image_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    for img in soup.find_all("img"):
        parent_chain = [p.name for p in img.parents if p.name]
        if any(p in SKIP_IMG_PARENTS for p in parent_chain):
            continue
        src = img.get("src", "").strip()
        if not src or src.startswith("data:"):
            continue
        low = src.lower()
        if any(x in low for x in ("logo", "icon", "facebook", "twitter", "youtube", "/recomendados/")):
            continue
        if low.endswith(".gif") and "loading" in low:
            continue
        urls.add(src)
    return sorted(urls)


def download_image(url: str, img_dir: Path) -> str | None:
    """Descarga imagen a img_dir/{flatname}.{ext}; devuelve path público."""
    parsed = urlparse(url)
    path = parsed.path
    ext = Path(path).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        ext = ".jpg"
    flat = re.sub(r"[^a-zA-Z0-9._-]+", "_", path).strip("_")
    if not flat:
        flat = f"img_{abs(hash(url))}{ext}"
    if not flat.endswith(ext):
        flat += ext
    out = img_dir / flat
    if out.exists() and out.stat().st_size > 0:
        return f"/img/{img_dir.name}/{flat}"
    full = url if url.startswith("http") else f"{BASE}{url}" if url.startswith("/") else f"{BASE}/{url}"
    try:
        r = session.get(full, timeout=30)
        if r.status_code != 200 or not r.content:
            return None
        out.write_bytes(r.content)
        return f"/img/{img_dir.name}/{flat}"
    except Exception as e:
        print(f"  ! img error {full}: {e}", file=sys.stderr)
        return None


# ---- Parseo de contenido ---------------------------------------------------
def parse_content(html_path: Path, img_dir: Path) -> dict:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    article = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"guia|contenido|content", re.I))
        or soup.find("div", id=re.compile(r"guia|contenido|content", re.I))
        or soup.find("main")
        or soup.body
    )

    title = ""
    h1 = article.find("h1") if article else None
    if h1:
        title = h1.get_text(strip=True)
    if not title and soup.title:
        title = soup.title.get_text(strip=True).split("|")[0].strip()
    if not title:
        title = html_path.stem

    if article:
        for tag in ["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]:
            for el in article.find_all(tag):
                el.decompose()
        for c in article.find_all(string=lambda t: isinstance(t, type(article.string)) and t.strip().startswith("<!--")):
            c.extract()

    intro_image = None
    if article:
        first_img = article.find("img")
        if first_img:
            intro_image = first_img.get("src", "")

    blocks: list[dict] = []
    intro_lines: list[str] = []
    intro_text_done = False

    def clean_text(el) -> str:
        return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

    container = article
    if container is None:
        return {"title": title, "intro": "", "blocks": []}

    for el in container.descendants:
        if not isinstance(el, __import__("bs4").Tag):
            continue
        if el.name == "h2":
            text = clean_text(el)
            if text:
                blocks.append({"type": "h2", "text": text})
                intro_text_done = True
        elif el.name == "h3":
            text = clean_text(el)
            if text:
                blocks.append({"type": "h3", "text": text})
                intro_text_done = True
        elif el.name == "h4":
            text = clean_text(el)
            if text:
                blocks.append({"type": "h4", "text": text})
                intro_text_done = True
        elif el.name == "p":
            text = clean_text(el)
            if not text:
                continue
            if el.find("a") and not re.search(r"[A-Za-záéíóúñÑ]{20,}", text):
                continue
            if not intro_text_done:
                intro_lines.append(text)
            else:
                blocks.append({"type": "p", "text": text})
        elif el.name == "ul" and el.find("li", recursive=False):
            items = [clean_text(li) for li in el.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                blocks.append({"type": "ul", "items": items})
                intro_text_done = True
        elif el.name == "ol" and el.find("li", recursive=False):
            items = [clean_text(li) for li in el.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                blocks.append({"type": "ol", "items": items})
                intro_text_done = True
        elif el.name == "img" and el.get("src"):
            src = el.get("src", "")
            if not src or src.startswith("data:"):
                continue
            parent_chain = [p.name for p in el.parents if p.name]
            if any(p in ("h1", "h2", "h3", "h4", "a") for p in parent_chain):
                continue
            local = download_image(src, img_dir) or src
            blocks.append({
                "type": "img",
                "src": local,
                "alt": el.get("alt", "").strip(),
                "caption": el.get("title", "").strip(),
            })
            intro_text_done = True
        elif el.name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [clean_text(c) for c in tr.find_all(["td", "th"])]
                if any(cells):
                    rows.append(cells)
            if rows:
                blocks.append({"type": "table", "rows": rows})
                intro_text_done = True

    cleaned: list[dict] = []
    for b in blocks:
        if cleaned and cleaned[-1]["type"] == b["type"] == "p":
            cleaned[-1]["text"] += " " + b["text"]
        elif cleaned and cleaned[-1]["type"] == b["type"] in ("ul", "ol"):
            cleaned[-1]["items"].extend(b["items"])
        else:
            cleaned.append(b)

    return {
        "title": title,
        "intro": " ".join(intro_lines).strip(),
        "image": intro_image,
        "blocks": cleaned,
    }


# ---- Procesar un juego ------------------------------------------------------
def process_game(game: GameConfig, slug_filter: set[str] | None = None, download: bool = True) -> list[dict]:
    raw_dir, img_dir = game_dirs(game)
    items = game.all_items()
    if slug_filter:
        items = [it for it in items if it["slug"] in slug_filter]

    print(f"\n=== {game.title} ({game.slug}) — {len(items)} páginas ===")

    # 1) Descargar HTML
    if download:
        for i, it in enumerate(items, 1):
            raw = raw_dir / f"{it['href']}.html"
            if raw.exists() and raw.stat().st_size > 1000:
                continue
            print(f"  [{i:>3}/{len(items)}] {it['href']} ...", end="", flush=True)
            t0 = time.time()
            res = download_page(game, it["href"], raw_dir)
            dt = time.time() - t0
            print(f" {len(res or ''):>7} chars  ({dt:.1f}s)" if res else " FAILED")
            time.sleep(0.2)

    # 2) Parsear + descargar imágenes
    out: list[dict] = []
    for i, it in enumerate(items, 1):
        html_path = raw_dir / f"{it['href']}.html"
        if not html_path.exists():
            print(f"  · falta {it['href']}")
            continue
        print(f"  · [{i:>3}/{len(items)}] parse {it['href']} ...", end="", flush=True)
        content = parse_content(html_path, img_dir)
        # Descargar imágenes adicionales que no estén en el contenido (p.ej. decorativas)
        html_text = html_path.read_text(encoding="utf-8", errors="ignore")
        for url in extract_image_urls(html_text):
            download_image(url, img_dir)
        n_img = sum(1 for b in content["blocks"] if b["type"] == "img")
        print(f" {len(content['blocks'])} bloques, {n_img} imgs")
        out.append({
            "slug": it["slug"],
            "disc": "Walkthrough",  # se sobreescribe abajo
            "title": it["title"],
            "href": it["href"],
            "content": content,
        })

    # Asignar disc según la sección
    slug_to_disc: dict[str, str] = {}
    for sec in game.sections:
        for it in sec["items"]:
            slug_to_disc[it["slug"]] = sec["disc"]
    for p in out:
        p["disc"] = slug_to_disc.get(p["slug"], "Walkthrough")

    # Limpiar tmp si quedó
    tmp = IMG_ROOT / "__tmp__"
    if tmp.exists():
        for f in tmp.iterdir():
            try: f.unlink()
            except: pass
        try: tmp.rmdir()
        except: pass

    # Guardar

    # Guardar
    out_path = DATA_DIR / game.slug / "guide.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    structure = [
        {"disc": sec["disc"], "items": [
            {"slug": it["slug"], "title": it["title"]}
            for it in sec["items"] if it["slug"] in {p["slug"] for p in out}
        ]}
        for sec in game.sections
    ]
    (DATA_DIR / game.slug / "structure.json").write_text(
        json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  OK → data/games/{game.slug}/guide.json ({len(out)} páginas)")
    return out


# ---- Main -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=MVP_GAME, help="slug del juego o 'all'")
    ap.add_argument("--slug", help="solo esta página (requiere --game)")
    ap.add_argument("--parse-only", action="store_true", help="no descargar HTML")
    args = ap.parse_args()

    if not REGISTRY.exists():
        print(f"! Falta {REGISTRY}", file=sys.stderr)
        sys.exit(1)

    games = load_registry()
    game_map = {g.slug: g for g in games}

    if args.game == "all":
        targets = games
    else:
        if args.game not in game_map:
            print(f"! Juego '{args.game}' no está en el registry. Disponibles: {list(game_map)}", file=sys.stderr)
            sys.exit(1)
        targets = [game_map[args.game]]

    for g in targets:
        slug_filter = {args.slug} if args.slug else None
        process_game(g, slug_filter=slug_filter, download=not args.parse_only)


if __name__ == "__main__":
    main()
