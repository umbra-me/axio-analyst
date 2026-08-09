"""Original Axio Analyst mark and the shared sidebar glyph set.

Every shape is drawn on a 24-unit grid with round caps and joins so the
sidebar icon and the in-widget action buttons share one stroke language. The
artwork is painted rather than shipped as an asset, so the development
installer has no binary file to package and the marks stay crisp at any dock
scale. Colours are supplied by the caller from the active Qt palette, which
keeps the glyphs readable on both light and dark Binary Ninja themes.
"""

from typing import Callable

from PySide6 import QtCore, QtGui

GRID = 24.0
ICON_SIZES = (16, 20, 24, 32)
SIDEBAR_ICON_SIZE = 56

Painter = Callable[[QtGui.QPainter, float, QtGui.QColor], None]


def _pen(color: QtGui.QColor, width: float, scale: float) -> QtGui.QPen:
    pen = QtGui.QPen(color)
    pen.setWidthF(width * scale)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    return pen


def _point(scale: float, x: float, y: float) -> QtCore.QPointF:
    return QtCore.QPointF(x * scale, y * scale)


def _stroke(painter, scale, color, points, width=2.0, close=False) -> None:
    painter.setPen(_pen(color, width, scale))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    path = QtGui.QPainterPath(_point(scale, *points[0]))
    for point in points[1:]:
        path.lineTo(_point(scale, *point))
    if close:
        path.closeSubpath()
    painter.drawPath(path)


def _line(painter, scale, color, x1, y1, x2, y2, width=2.0) -> None:
    _stroke(painter, scale, color, [(x1, y1), (x2, y2)], width)


def _dot(painter, scale, color, x, y, radius) -> None:
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(_point(scale, x, y), radius * scale, radius * scale)


def draw_mark(painter: QtGui.QPainter, size: float, color: QtGui.QColor) -> None:
    """The Axio Analyst mark: one node read two ways.

    A split diamond - solid on one side, stroked on the other - stands for a
    single bounded context examined from more than one reading. It keeps a
    heavy silhouette at sidebar sizes where outline-only marks thin out.
    """
    scale = size / GRID
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPolygon(
        QtGui.QPolygonF(
            [
                _point(scale, 12, 2.5),
                _point(scale, 21.5, 12),
                _point(scale, 12, 21.5),
            ]
        )
    )
    _stroke(
        painter,
        scale,
        color,
        [(12, 2.5), (21.5, 12), (12, 21.5), (2.5, 12)],
        close=True,
    )


def _glyph_scope(painter, size, color) -> None:
    scale = size / GRID
    inset, arm = 4.0, 4.5
    far = GRID - inset
    for points in (
        [(inset, inset + arm), (inset, inset), (inset + arm, inset)],
        [(far - arm, inset), (far, inset), (far, inset + arm)],
        [(far, far - arm), (far, far), (far - arm, far)],
        [(inset + arm, far), (inset, far), (inset, far - arm)],
    ):
        _stroke(painter, scale, color, points)


def _glyph_explain(painter, size, color) -> None:
    scale = size / GRID
    _dot(painter, scale, color, 12, 12, 3.0)
    for x1, y1, x2, y2 in (
        (12, 2.5, 12, 6),
        (12, 18, 12, 21.5),
        (2.5, 12, 6, 12),
        (18, 12, 21.5, 12),
        (5.6, 5.6, 8.0, 8.0),
        (16.0, 16.0, 18.4, 18.4),
        (18.4, 5.6, 16.0, 8.0),
        (8.0, 16.0, 5.6, 18.4),
    ):
        _line(painter, scale, color, x1, y1, x2, y2)


def _glyph_send(painter, size, color) -> None:
    scale = size / GRID
    _line(painter, scale, color, 3.5, 12, 17, 12)
    _stroke(painter, scale, color, [(12, 6.5), (17.5, 12), (12, 17.5)])
    _line(painter, scale, color, 20.5, 5.5, 20.5, 18.5)


def _glyph_stop(painter, size, color) -> None:
    scale = size / GRID
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(
        QtCore.QRectF(6 * scale, 6 * scale, 12 * scale, 12 * scale),
        2.0 * scale,
        2.0 * scale,
    )


def _glyph_compare(painter, size, color) -> None:
    scale = size / GRID
    painter.setPen(_pen(color, 2.0, scale))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(
        QtCore.QRectF(3 * scale, 6 * scale, 11 * scale, 12 * scale),
        2.0 * scale,
        2.0 * scale,
    )
    _stroke(painter, scale, color, [(17, 6), (21, 6), (21, 18), (17, 18)])


def _glyph_export(painter, size, color) -> None:
    scale = size / GRID
    _stroke(
        painter,
        scale,
        color,
        [(7.5, 6.5), (4, 6.5), (4, 20), (20, 20), (20, 6.5), (16.5, 6.5)],
    )
    _line(painter, scale, color, 12, 3.5, 12, 14.5)
    _stroke(painter, scale, color, [(8, 7.5), (12, 3.5), (16, 7.5)])


def _glyph_clear(painter, size, color) -> None:
    scale = size / GRID
    _line(painter, scale, color, 4, 6.5, 20, 6.5)
    _stroke(painter, scale, color, [(9, 6.5), (9, 4), (15, 4), (15, 6.5)])
    _stroke(
        painter,
        scale,
        color,
        [(6.5, 6.5), (7.5, 20.5), (16.5, 20.5), (17.5, 6.5)],
    )
    _line(painter, scale, color, 10.5, 10.5, 10.5, 16.5)
    _line(painter, scale, color, 13.5, 10.5, 13.5, 16.5)


def _glyph_settings(painter, size, color) -> None:
    scale = size / GRID
    _line(painter, scale, color, 3.5, 7.5, 20.5, 7.5)
    _line(painter, scale, color, 3.5, 16.5, 20.5, 16.5)
    _dot(painter, scale, color, 9, 7.5, 2.6)
    _dot(painter, scale, color, 15.5, 16.5, 2.6)


def _glyph_overflow(painter, size, color) -> None:
    scale = size / GRID
    for x in (5.5, 12, 18.5):
        _dot(painter, scale, color, x, 12, 1.9)


def _glyph_back(painter, size, color) -> None:
    scale = size / GRID
    _line(painter, scale, color, 20.5, 12, 6, 12)
    _stroke(painter, scale, color, [(11.5, 6.5), (6, 12), (11.5, 17.5)])


def _glyph_preview(painter, size, color) -> None:
    scale = size / GRID
    _stroke(
        painter,
        scale,
        color,
        [(2.5, 12), (7, 6.5), (17, 6.5), (21.5, 12), (17, 17.5), (7, 17.5)],
        close=True,
    )
    _dot(painter, scale, color, 12, 12, 2.6)


def _glyph_chevron_down(painter, size, color) -> None:
    scale = size / GRID
    _stroke(painter, scale, color, [(6, 9.5), (12, 15.5), (18, 9.5)])


def _glyph_chevron_right(painter, size, color) -> None:
    scale = size / GRID
    _stroke(painter, scale, color, [(9.5, 6), (15.5, 12), (9.5, 18)])


GLYPHS: dict[str, Painter] = {
    "scope": _glyph_scope,
    "explain": _glyph_explain,
    "send": _glyph_send,
    "stop": _glyph_stop,
    "compare": _glyph_compare,
    "export": _glyph_export,
    "clear": _glyph_clear,
    "settings": _glyph_settings,
    "overflow": _glyph_overflow,
    "back": _glyph_back,
    "preview": _glyph_preview,
    "chevron-down": _glyph_chevron_down,
    "chevron-right": _glyph_chevron_right,
}


def render(painter: Painter, size: int, color: QtGui.QColor) -> QtGui.QImage:
    image = QtGui.QImage(
        size, size, QtGui.QImage.Format.Format_ARGB32_Premultiplied
    )
    image.fill(0)
    device = QtGui.QPainter(image)
    device.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
    painter(device, float(size), color)
    device.end()
    return image


def sidebar_icon() -> QtGui.QImage:
    """Binary Ninja tints this image itself, so paint it opaque white."""
    return render(draw_mark, SIDEBAR_ICON_SIZE, QtGui.QColor(255, 255, 255))


def glyph_icon(name: str, color: QtGui.QColor) -> QtGui.QIcon:
    icon = QtGui.QIcon()
    for size in ICON_SIZES:
        icon.addPixmap(QtGui.QPixmap.fromImage(render(GLYPHS[name], size, color)))
    return icon
