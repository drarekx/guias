#!/usr/bin/env bash
# deploy-guias — descarga y despliega la última release de drarekx/guias
# Uso: sudo deploy-guias [version|latest]
#
# Requiere: curl, python3, nginx sirviendo /var/www/guias
# Repo: https://github.com/drarekx/guias (público)

set -euo pipefail

VERSION="${1:-latest}"
DEST="/var/www/guias"
REPO="drarekx/guias"
WORK="/tmp/guias-release"
BACKUP="/var/www/guias.bak"

if [[ "$VERSION" == "latest" ]]; then
  echo "→ Consultando último release…"
  VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])")
fi

echo "→ Desplegando $REPO@$VERSION → $DEST"

# Backup
if [[ -d "$DEST" ]] && [[ -n "$(ls -A "$DEST" 2>/dev/null)" ]]; then
  rm -rf "$BACKUP"
  cp -a "$DEST" "$BACKUP"
  echo "  backup → $BACKUP"
fi

# Descargar
rm -rf "$WORK"; mkdir -p "$WORK"
URL="https://github.com/$REPO/releases/download/$VERSION/tomo-del-cristal-${VERSION}.tar.gz"
echo "  ↓ $URL"
curl -fsSL "$URL" -o "$WORK/release.tar.gz"

# Extraer (silencia warnings de xattr macOS)
mkdir -p "$DEST"
tar -xzf "$WORK/release.tar.gz" -C "$DEST" --strip-components=1 \
  --warning=no-unknown-keyword 2>/dev/null || \
  tar -xzf "$WORK/release.tar.gz" -C "$DEST" --strip-components=1
rm -rf "$WORK"

# Verificar
if [[ -f "$DEST/index.html" ]] && [[ -d "$DEST/img" ]]; then
  echo "✓ Desplegado correctamente"
  echo "  tamaño: $(du -sh "$DEST" | cut -f1)"
  echo "  HTML:   $(find "$DEST" -name '*.html' | wc -l) páginas"
  rm -rf "$BACKUP"
  systemctl reload nginx 2>/dev/null || true
else
  echo "✗ Verificación falló, restaurando backup…"
  rm -rf "$DEST"
  mv "$BACKUP" "$DEST"
  exit 1
fi
