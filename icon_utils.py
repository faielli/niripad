from PyQt6.QtGui import QIcon, QColor

try:
    import qtawesome as qta
    QTA_AVAILABLE = True
except ImportError:
    qta = None
    QTA_AVAILABLE = False

from theme_tokens import Tokens

ICON_DEFAULT = Tokens.FG_SECONDARY.name()
ICON_HOVER = Tokens.ACCENT.name()
ICON_ACTIVE = Tokens.ACCENT_HOVER.name()


def get_icon(name, color=ICON_DEFAULT, size=14):
    if QTA_AVAILABLE and qta:
        return qta.icon(name, color=color)
    return QIcon()


class Icons:
    _cache = {}

    def __init__(self, color: QColor = None):
        self._c = color or Tokens.FG_SECONDARY

    def _qta(self, name, size=14):
        return get_icon(name, self._c.name(), size)

    def chevron_left(self, size=14):
        return self._qta("fa5s.chevron-left", size)

    def chevron_right(self, size=14):
        return self._qta("fa5s.chevron-right", size)

    def chevron_up(self, size=14):
        return self._qta("fa5s.chevron-up", size)

    def chevron_down(self, size=14):
        return self._qta("fa5s.chevron-down", size)

    def folder(self, size=14):
        return self._qta("fa5s.folder", size)

    def folder_open(self, size=14):
        return self._qta("fa5s.folder-open", size)

    def close(self, size=12):
        return self._qta("fa5s.times", size)

    def search(self, size=14):
        return self._qta("fa5s.search", size)

    def bars(self, size=14):
        return self._qta("fa5s.bars", size)

    def file(self, size=14):
        return self._qta("fa5s.file", size)

    def file_code(self, size=14):
        return self._qta("fa5s.file-code", size)

    def file_alt(self, size=14):
        return self._qta("fa5s.file-alt", size)

    def save(self, size=14):
        return self._qta("fa5s.save", size)

    def copy(self, size=14):
        return self._qta("fa5s.copy", size)

    def undo(self, size=14):
        return self._qta("fa5s.undo", size)

    def redo(self, size=14):
        return self._qta("fa5s.redo", size)

    def sitemap(self, size=14):
        return self._qta("fa5s.sitemap", size)

    def cog(self, size=14):
        return self._qta("fa5s.cog", size)

    def terminal(self, size=14):
        return self._qta("fa5s.terminal", size)

    def crosshairs(self, size=14):
        return self._qta("fa5s.crosshairs", size)

    def exchange_alt(self, size=14):
        return self._qta("fa5s.exchange-alt", size)

    def compress_alt(self, size=12):
        return self._qta("fa5s.compress-alt", size)

    def check_circle(self, size=12):
        return self._qta("fa5s.check-circle", size)

    def exclamation_circle(self, size=12):
        return self._qta("fa5s.exclamation-circle", size)
