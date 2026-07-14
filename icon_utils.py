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

    def chevron_left(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(10, 4), QPoint(4, 8), QPoint(10, 12)])
        ), size)

    def chevron_right(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(4, 4), QPoint(10, 8), QPoint(4, 12)])
        ), size)

    def chevron_up(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(4, 10), QPoint(8, 4), QPoint(12, 10)])
        ), size)

    def chevron_down(self, size=16):
        return self._pix(lambda p, s: p.drawPolyline(
            QPolygon([QPoint(4, 6), QPoint(8, 12), QPoint(12, 6)])
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
            p.drawEllipse(QPointF(5.5, 5.5), 4, 4),
            p.drawLine(QPoint(9, 9), QPoint(14, 14)),
        ), size)
