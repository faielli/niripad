#!/bin/bash
# Script di installazione per Niripad
set -e

PKGBUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGVER="1.0.0"
PKGNAME="niripad"

echo "==> Installazione di Niripad ${PKGVER}"

# Controlla che la cartella del sorgente esista
if [ -z "$1" ]; then
    echo "Uso: ./install.sh /percorso/al/sorgente"
    echo "Esempio: ./install.sh ~/progetti/niripad-src"
    exit 1
fi

SRC_DIR="$1"

if [ ! -d "$SRC_DIR" ]; then
    echo "Errore: cartella sorgente '$SRC_DIR' non trovata."
    exit 1
fi

if [ ! -f "$SRC_DIR/main.py" ]; then
    echo "Errore: '$SRC_DIR' non sembra la cartella corretta (main.py non trovato)."
    exit 1
fi

# Crea il tarball
echo "==> Creazione del tarball ${PKGNAME}-${PKGVER}.tar.gz..."
tar -czf "${PKGBUILD_DIR}/${PKGNAME}-${PKGVER}.tar.gz" \
    --exclude='*/__pycache__' \
    --exclude='*/.venv' \
    --exclude='*/*.pyc' \
    --transform "s|^$(basename "$SRC_DIR")|${PKGNAME}-${PKGVER}|" \
    -C "$(dirname "$SRC_DIR")" \
    "$(basename "$SRC_DIR")"

echo "==> Tarball creato."

# Build e installazione
cd "$PKGBUILD_DIR"
echo "==> Esecuzione di makepkg..."
makepkg -si --noconfirm

echo ""
echo "==> Niripad installato con successo!"
echo "    Avvia con: niripad"
