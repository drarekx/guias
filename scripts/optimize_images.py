"""
Optimiza las imágenes de todos los juegos:
- Convierte JPG/PNG a WebP (calidad 80, method 6)
- Redimensiona a max 1280px de ancho preservando aspect ratio
- Actualiza data/games/{slug}/guide.json con las nuevas rutas
- Elimina los originales

Uso:
  python3 scripts/optimize_images.py            # procesa todos los juegos
  python3 scripts/optimize_images.py --game ff9 # solo un juego
  python3 scripts/optimize_images.py --quality 85 --max-width 1600
  python3 scripts/optimize_images.py --keep-originals # no borra los JPG/PNG
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_ROOT = ROOT / "public" / "img"
DATA_ROOT = ROOT / "data" / "games"

QUALITY_DEFAULT = 80
MAX_WIDTH_DEFAULT = 1280
LOSSLESS = False


def is_already_webp(p: Path) -> bool:
    return p.suffix.lower() == ".webp"


def optimize_one(src: Path, quality: int, max_width: int) -> tuple[Path, int, int] | None:
    """Convierte una imagen a WebP. Devuelve (ruta_original, bytes_original, bytes_nuevo)."""
    if not src.exists():
        return None
    if is_already_webp(src):
        return None

    try:
        original_size = src.stat().st_size
        dst = src.with_suffix(".webp")

        with Image.open(src) as im:
            im.load()
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            elif im.mode != "RGB":
                im = im.convert("RGB")
            if im.width > max_width:
                ratio = max_width / im.width
                new_size = (max_width, max(1, round(im.height * ratio)))
                im = im.resize(new_size, Image.LANCZOS)
            im.save(dst, "WEBP", quality=quality, method=6)

        return (src, original_size, dst.stat().st_size)
    except Exception as e:
        print(f"  ! error {src.name}: {e}", file=sys.stderr)
        return None


def process_game(slug: str, quality: int, max_width: int, keep_originals: bool) -> dict:
    img_dir = IMG_ROOT / slug
    guide_path = DATA_ROOT / slug / "guide.json"

    if not img_dir.exists():
        return {"slug": slug, "skipped": "no img dir"}

    print(f"\n=== {slug} ===")

    # Encontrar todas las imágenes JPG/PNG
    sources = [p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif"}]
    print(f"  imágenes: {len(sources)}")

    before_total = sum(p.stat().st_size for p in sources)
    print(f"  tamaño inicial: {before_total / 1024 / 1024:.1f} MB")

    converted = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(optimize_one, s, quality, max_width): s for s in sources}
        for i, f in enumerate(as_completed(futures), 1):
            r = f.result()
            if r:
                converted.append(r)
            if i % 200 == 0:
                print(f"  procesadas {i}/{len(sources)}...")

    after_total = sum(r[2] for r in converted)
    saved_bytes = sum(r[1] - r[2] for r in converted)
    print(f"  convertido:    {len(converted)}")
    print(f"  tamaño final:  {after_total / 1024 / 1024:.1f} MB")
    print(f"  ahorro:        {saved_bytes / 1024 / 1024:.1f} MB ({100 * saved_bytes / max(1, before_total):.0f}%)")

    # Actualizar guide.json: cambiar rutas .jpg/.png → .webp
    if guide_path.exists():
        guide = json.loads(guide_path.read_text(encoding="utf-8"))
        updated = 0
        for page in guide:
            for block in page.get("content", {}).get("blocks", []):
                if block.get("type") == "img" and isinstance(block.get("src"), str):
                    src = block["src"]
                    if src.startswith("/img/") and not src.endswith(".webp"):
                        for ext in (".jpg", ".jpeg", ".png", ".gif"):
                            if src.endswith(ext):
                                block["src"] = src[: -len(ext)] + ".webp"
                                updated += 1
                                break
        if updated:
            guide_path.write_text(json.dumps(guide, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  guide.json:    {updated} rutas actualizadas")

    # Eliminar originales
    removed = 0
    if not keep_originals:
        for src, _, _ in converted:
            try:
                src.unlink()
                removed += 1
            except OSError:
                pass
        print(f"  originales borrados: {removed}")

    return {
        "slug": slug,
        "converted": len(converted),
        "before_mb": before_total / 1024 / 1024,
        "after_mb": after_total / 1024 / 1024,
        "saved_mb": saved_bytes / 1024 / 1024,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", help="solo este juego (default: todos)")
    ap.add_argument("--quality", type=int, default=QUALITY_DEFAULT, help=f"calidad WebP (default {QUALITY_DEFAULT})")
    ap.add_argument("--max-width", type=int, default=MAX_WIDTH_DEFAULT, help=f"ancho máximo (default {MAX_WIDTH_DEFAULT})")
    ap.add_argument("--keep-originals", action="store_true", help="no borrar JPG/PNG originales")
    args = ap.parse_args()

    if not IMG_ROOT.exists():
        print(f"! {IMG_ROOT} no existe", file=sys.stderr)
        sys.exit(1)

    if args.game:
        slugs = [args.game]
    else:
        slugs = sorted(p.name for p in IMG_ROOT.iterdir() if p.is_dir())

    print(f"Procesando {len(slugs)} juego(s) | quality={args.quality} max-width={args.max_width}")
    results = [process_game(s, args.quality, args.max_width, args.keep_originals) for s in slugs]

    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    total_before = sum(r.get("before_mb", 0) for r in results)
    total_after = sum(r.get("after_mb", 0) for r in results)
    total_saved = sum(r.get("saved_mb", 0) for r in results)
    for r in results:
        if "skipped" in r:
            print(f"  {r['slug']:10s}  SKIP  {r['skipped']}")
        else:
            print(f"  {r['slug']:10s}  {r.get('before_mb', 0):6.1f} → {r.get('after_mb', 0):6.1f} MB  (ahorro {r.get('saved_mb', 0):5.1f} MB)")
    print("  " + "-" * 48)
    print(f"  {'TOTAL':10s}  {total_before:6.1f} → {total_after:6.1f} MB  (ahorro {total_saved:5.1f} MB)")


if __name__ == "__main__":
    main()
