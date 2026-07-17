#!/bin/bash
# Script di installazione per Niripad
set -e

PKGBUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGVER="1.0.0"
PKGNAME="niripad"

echo "==> Installazione di Niripad ${PKGVER}"

# Crea il tarball dai file .py nella stessa cartella della repo
echo "==> Creazione del tarball ${PKGNAME}-${PKGVER}.tar.gz..."
tar -czf "${PKGBUILD_DIR}/${PKGNAME}-${PKGVER}.tar.gz" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --transform "s|^\.|${PKGNAME}-${PKGVER}|" \
    -C "${PKGBUILD_DIR}" \
    $(ls "${PKGBUILD_DIR}"/*.py)

echo "==> Tarball creato."

# Build e installazione
cd "$PKGBUILD_DIR"
echo "==> Esecuzione di makepkg..."
makepkg -si --noconfirm

echo ""
echo "==> Niripad installato con successo!"
echo "    Avvia con: niripad"
