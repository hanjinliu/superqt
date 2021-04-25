import platform
import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Union

from .qtcompat.QtCore import Qt
from .qtcompat.QtGui import (
    QColor,
    QGradient,
    QLinearGradient,
    QPalette,
    QRadialGradient,
)
from .qtcompat.QtWidgets import QApplication, QSlider, QStyleOptionSlider

if TYPE_CHECKING:
    from ._qrangeslider import QRangeSlider


@dataclass
class RangeSliderStyle:
    brush_active: str = None
    brush_inactive: str = None
    brush_disabled: str = None
    pen_active: str = None
    pen_inactive: str = None
    pen_disabled: str = None
    vertical_thickness: float = None
    horizontal_thickness: float = None
    tick_offset: float = None
    tick_bar_alpha: float = None
    v_offset: float = None
    h_offset: float = None
    has_stylesheet: bool = False

    def brush(self, opt: QStyleOptionSlider) -> Union[QGradient, QColor]:
        cg = opt.palette.currentColorGroup()
        attr = {
            QPalette.Active: "brush_active",  # 0
            QPalette.Disabled: "brush_disabled",  # 1
            QPalette.Inactive: "brush_inactive",  # 2
        }[cg]
        val = getattr(self, attr) or getattr(SYSTEM_STYLE, attr)
        if isinstance(val, str):
            val = QColor(val)

        if opt.tickPosition != QSlider.NoTicks:
            val.setAlphaF(self.tick_bar_alpha or SYSTEM_STYLE.tick_bar_alpha)

        return val

    def pen(self, opt: QStyleOptionSlider) -> Union[Qt.PenStyle, QColor]:
        cg = opt.palette.currentColorGroup()
        attr = {
            QPalette.Active: "pen_active",  # 0
            QPalette.Disabled: "pen_disabled",  # 1
            QPalette.Inactive: "pen_inactive",  # 2
        }[cg]
        val = getattr(self, attr) or getattr(SYSTEM_STYLE, attr)
        if not val:
            return Qt.NoPen
        if isinstance(val, str):
            val = QColor(val)
        if opt.tickPosition != QSlider.NoTicks:
            val.setAlphaF(self.tick_bar_alpha or SYSTEM_STYLE.tick_bar_alpha)

        return val
    
    def offset(self, opt: QStyleOptionSlider) -> int:
        tp = opt.tickPosition
        off = 0
        if not self.has_stylesheet:
            if opt.orientation == Qt.Horizontal:
                off += self.h_offset or SYSTEM_STYLE.h_offset or 0
            else:
                off += self.v_offset or SYSTEM_STYLE.v_offset or 0
            if tp & QSlider.TicksAbove:
                off += self.tick_offset or SYSTEM_STYLE.tick_offset
            elif tp & QSlider.TicksBelow:
                off -= self.tick_offset or SYSTEM_STYLE.tick_offset
        return off

    def thickness(self, opt: QStyleOptionSlider) -> float:
        if opt.orientation == Qt.Horizontal:
            return self.horizontal_thickness or SYSTEM_STYLE.horizontal_thickness
        else:
            return self.vertical_thickness or SYSTEM_STYLE.vertical_thickness


# ##########  System-specific default styles ############

BASE_STYLE = RangeSliderStyle(
    brush_active="#3B88FD",
    brush_inactive="#8F8F8F",
    brush_disabled="#BBBBBB",
    pen_active = 'transparent',
    pen_inactive = 'transparent',
    pen_disabled = 'transparent',
    vertical_thickness = 4,
    horizontal_thickness = 4,
    tick_offset = 0,
    tick_bar_alpha = 0.3,
    v_offset = 0,
    h_offset = 0,
    has_stylesheet = False,
)

CATALINA_STYLE = replace(
    BASE_STYLE,
    brush_active="#3B88FD",
    brush_inactive="#8F8F8F",
    brush_disabled="#D2D2D2",
    horizontal_thickness=3,
    vertical_thickness=3,
    tick_bar_alpha=0.3,
    tick_offset=4,
)

BIG_SUR_STYLE = replace(
    CATALINA_STYLE,
    brush_active="#0A81FE",
    brush_inactive="#D5D5D5",
    brush_disabled="#E6E6E6",
    tick_offset=0,
    horizontal_thickness=4,
    vertical_thickness=4,
    h_offset=-2,
    tick_bar_alpha=0.2,
)

LINUX_STYLE = replace(
    BASE_STYLE,
    brush_active='#44A0D9',
    brush_inactive='#44A0D9',
    brush_disabled='#44A0D9',
    pen_active = '#286384',
    pen_inactive = '#286384',
    pen_disabled = '#286384',
)

SYSTEM = platform.system()
if SYSTEM == "Darwin":
    if int(platform.mac_ver()[0].split(".", maxsplit=1)[0]) >= 11:
        SYSTEM_STYLE = BIG_SUR_STYLE
    else:
        SYSTEM_STYLE = CATALINA_STYLE
elif SYSTEM == "Windows":
    SYSTEM_STYLE = BASE_STYLE
elif SYSTEM == "Linux":
    SYSTEM_STYLE = LINUX_STYLE
else:
    SYSTEM_STYLE = BASE_STYLE


# ################ Stylesheet parsing logic ########################

qlineargrad_pattern = re.compile(
    r"""
    qlineargradient\(
        x1:\s*(?P<x1>\d*\.?\d+),\s*
        y1:\s*(?P<y1>\d*\.?\d+),\s*
        x2:\s*(?P<x2>\d*\.?\d+),\s*
        y2:\s*(?P<y2>\d*\.?\d+),\s*
        stop:0\s*(?P<stop0>\S+),.*
        stop:1\s*(?P<stop1>\S+)
    \)""",
    re.X,
)

qradial_pattern = re.compile(
    r"""
    qradialgradient\(
        cx:\s*(?P<cx>\d*\.?\d+),\s*
        cy:\s*(?P<cy>\d*\.?\d+),\s*
        radius:\s*(?P<radius>\d*\.?\d+),\s*
        fx:\s*(?P<fx>\d*\.?\d+),\s*
        fy:\s*(?P<fy>\d*\.?\d+),\s*
        stop:0\s*(?P<stop0>\S+),.*
        stop:1\s*(?P<stop1>\S+)
    \)""",
    re.X,
)


def parse_color(color: str) -> Union[str, QGradient]:
    qc = QColor(color)
    if qc.isValid():
        return qc

    # try linear gradient:
    match = qlineargrad_pattern.match(color)
    if match:
        grad = QLinearGradient(*[float(i) for i in match.groups()[:4]])
        grad.setColorAt(0, QColor(match.groupdict()["stop0"]))
        grad.setColorAt(1, QColor(match.groupdict()["stop1"]))
        return grad

    # try linear gradient:
    match = qradial_pattern.match(color)
    print("match", match.groupdict())
    if match:
        grad = QRadialGradient(*[float(i) for i in match.groups()[:5]])
        grad.setColorAt(0, QColor(match.groupdict()["stop0"]))
        grad.setColorAt(1, QColor(match.groupdict()["stop1"]))
        return grad

    # fallback to dark gray
    return "#333"


def update_styles_from_stylesheet(obj: "QRangeSlider"):
    qss = obj.styleSheet()
    p = obj
    while p.parent():
        qss = p.styleSheet() + qss
        p = p.parent()
    qss = QApplication.instance().styleSheet() + qss

    obj._style.has_stylesheet = False

    # Find bar color
    # TODO: optional horizontal or vertical
    match = re.search(r"Slider::sub-page:?([^{\s]*)?\s*{\s*([^}]+)}", qss, re.S)
    if match:
        orientation, content = match.groups()
        for line in reversed(content.splitlines()):
            bgrd = re.search(r"background(-color)?:\s*([^;]+)", line)
            if bgrd:
                color = parse_color(bgrd.groups()[-1])
                obj._style.brush_active = color
                # TODO: parse for inactive and disabled
                obj._style.brush_inactive = color
                obj._style.brush_disabled = color
                obj._style.has_stylesheet = True
                class_name = type(obj).__name__
                _ss = f"\n{class_name}::sub-page:{orientation}{{background: none}}"
                # TODO: block double event
                obj.setStyleSheet(qss + _ss)
                break

    # Find bar height/width
    for orient, dim in (("horizontal", "height"), ("vertical", "width")):
        match = re.search(rf"Slider::groove:{orient}\s*{{\s*([^}}]+)}}", qss, re.S)
        if match:
            for line in reversed(match.groups()[0].splitlines()):
                bgrd = re.search(rf"{dim}\s*:\s*(\d+)", line)
                if bgrd:
                    thickness = float(bgrd.groups()[-1])
                    setattr(obj._style, f"{orient}_thickness", thickness)
                    obj._style.has_stylesheet = True
