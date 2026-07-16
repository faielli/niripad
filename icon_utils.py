from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPolygon
from PyQt6.QtCore import Qt, QPoint, QPointF


class Icons:
    def __init__(self, color: QColor):
        self._c = color

    def _pix(self, draw_func, size=16):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._c, 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        draw_func(painter, size)
        painter.end()
        return QIcon(pixmap)

    def _s(self, pt, size):
        return int(round(pt * size / 16))

    def chevron_left(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(self._s(10, s), self._s(4, s)),
                      QPoint(self._s(4, s), self._s(8, s)),
                      QPoint(self._s(10, s), self._s(12, s))])
        ), size)

    def chevron_right(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(self._s(4, s), self._s(4, s)),
                      QPoint(self._s(10, s), self._s(8, s)),
                      QPoint(self._s(4, s), self._s(12, s))])
        ), size)

    def chevron_up(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(self._s(4, s), self._s(10, s)),
                      QPoint(self._s(8, s), self._s(4, s)),
                      QPoint(self._s(12, s), self._s(10, s))])
        ), size)

    def chevron_down(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(self._s(4, s), self._s(6, s)),
                      QPoint(self._s(8, s), self._s(12, s)),
                      QPoint(self._s(12, s), self._s(6, s))])
        ), size)

    def folder(self, size=16):
        return self._pix(lambda p, s: (
            p.drawLine(QPoint(2, 12), QPoint(2, 6)),
            p.drawLine(QPoint(2, 6), QPoint(5, 3)),
            p.drawLine(QPoint(5, 3), QPoint(s - 2, 3)),
            p.drawLine(QPoint(s - 2, 3), QPoint(s - 2, s - 3)),
            p.drawLine(QPoint(s - 2, s - 3), QPoint(2, s - 3)),
        ), size)

    def close(self, size=12):
        m = 2
        return self._pix(lambda p, s: (
            p.drawLine(QPoint(m, m), QPoint(s - m, s - m)),
            p.drawLine(QPoint(s - m, m), QPoint(m, s - m)),
        ), size)

    def search(self, size=16):
        return self._pix(lambda p, s: (
            p.drawEllipse(QPointF(self._s(5.5, s), self._s(5.5, s)), self._s(4, s), self._s(4, s)),
            p.drawLine(QPoint(self._s(9, s), self._s(9, s)), QPoint(self._s(14, s), self._s(14, s))),
        ), size)
