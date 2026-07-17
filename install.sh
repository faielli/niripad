#!/bin/bash
# Script di installazione per Niripad
set -e

PKGBUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGVER="1.0.0"
PKGNAME="niripad"

echo "==> Installazione di Niripad ${PKGVER}"

# Crea una cartella temporanea con la struttura corretta
TMPDIR=$(mktemp -d)
SRCDIR="${TMPDIR}/${PKGNAME}-${PKGVER}"
mkdir -p "${SRCDIR}"

# Copia i file .py nella cartella temporanea
cp "${PKGBUILD_DIR}"/*.py "${SRCDIR}/"

# Crea il tarball dalla cartella temporanea
echo "==> Creazione del tarball ${PKGNAME}-${PKGVER}.tar.gz..."
tar -czf "${PKGBUILD_DIR}/${PKGNAME}-${PKGVER}.tar.gz" \
    -C "${TMPDIR}" \
    "${PKGNAME}-${PKGVER}/"

# Pulizia
rm -rf "${TMPDIR}"

echo "==> Tarball creato."

# Verifica
echo "==> Contenuto del tarball:"
tar -tzf "${PKGBUILD_DIR}/${PKGNAME}-${PKGVER}.tar.gz"

# Build e installazione
cd "$PKGBUILD_DIR"
echo "==> Esecuzione di makepkg..."
makepkg -si --noconfirm

echo ""
echo "==> Niripad installato con successo!"
echo "    Avvia con: niripad"
