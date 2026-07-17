# Maintainer: faielli on github
pkgname=niripad
pkgver=1.0.0
pkgrel=1
pkgdesc="A lightweight PyQt6 text editor for Wayland/X11"
arch=('any')
url="https://github.com/faielli/niripad/"
license=('GPL3')
depends=('python' 'python-pyqt6' 'python-qtawesome')

source=(
    "${pkgname}-${pkgver}.tar.gz"
    "niripad.sh"
    "niripad.desktop"
)
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {
    local app_dir="/usr/lib/${pkgname}"
    local bin_dir="/usr/bin"
    local desktop_dir="/usr/share/applications"
    local src_dir="${srcdir}/${pkgname}-${pkgver}"

    # Installa tutti i file .py automaticamente
    install -dm755 "${pkgdir}${app_dir}"
    for f in "${src_dir}"/*.py; do
        install -Dm644 "${f}" "${pkgdir}${app_dir}/$(basename ${f})"
    done

    install -Dm755 "${srcdir}/niripad.sh" "${pkgdir}${bin_dir}/niripad"
    install -Dm644 "${srcdir}/niripad.desktop" "${pkgdir}${desktop_dir}/niripad.desktop"
}
