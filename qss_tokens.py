from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from theme_tokens import Tokens

t = Tokens


def apply_shadow(widget: QWidget):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(t.SHADOW_BLUR)
    effect.setOffset(t.SHADOW_OFFSET[0], t.SHADOW_OFFSET[1])
    effect.setColor(t.SHADOW_COLOR)
    widget.setGraphicsEffect(effect)


def qss() -> str:
    return f"""
QMainWindow, QWidget {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_PRIMARY.name()};
    font-family: {t.FONT_UI};
    font-size: {t.FONT_SIZE_UI}px;
}}

QPushButton {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    min-height: 44px;
}}
QPushButton:hover {{
    color: {t.ACCENT_HOVER.name()};
    border-color: {t.ACCENT.name()};
    background-color: {t.BG_SURFACE.name()};
}}
QPushButton:pressed {{
    background-color: {t.ACCENT_PRESS.name()};
    border-color: {t.ACCENT.name()};
}}
QPushButton:checked {{
    background-color: {t.ACCENT_PRESS.name()};
    border-color: {t.ACCENT.name()};
    color: {t.ACCENT_HOVER.name()};
}}
QPushButton:focus {{
    outline: 2px solid {t.BORDER_FOCUS.name()};
    outline-offset: 2px;
}}
QPushButton:disabled {{
    color: {t.FG_MUTED.name()};
    border-color: {t.BORDER_SUBTLE.name()};
    background-color: {t.BG_PANEL.name()};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    selection-background-color: {t.BORDER_FOCUS.name()};
    selection-color: {t.FG_PRIMARY.name()};
    min-height: 44px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
    background-color: {t.BG_SURFACE.name()};
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    width: 8px;
    height: 8px;
}}
QScrollBar::handle {{
    background-color: {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_SM}px;
    min-height: 20px;
    min-width: 10px;
}}
QScrollBar::handle:hover {{
    background-color: {t.ACCENT.name()};
}}
QScrollBar::handle:pressed {{
    background-color: {t.ACCENT_HOVER.name()};
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenuBar {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_SECONDARY.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QMenuBar::item {{
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_SECONDARY.name()};
}}
QMenuBar::item:selected {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
}}

QMenu {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[1]}px;
}}
QMenu::item {{
    padding: {t.SPACE[2]}px {t.SPACE[4]}px;
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_SECONDARY.name()};
}}
QMenu::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
QMenu::separator {{
    height: 1px;
    background: {t.BORDER_SUBTLE.name()};
    margin: {t.SPACE[1]}px {t.SPACE[2]}px;
}}

QDialog, QMessageBox {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
}}

QToolTip {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.ACCENT.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
}}

QSplitter::handle {{
    background-color: {t.BORDER_SUBTLE.name()};
    width: 1px;
    height: 1px;
}}

QStatusBar {{
    background: {t.GRADIENTS['statusbar']};
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
    font-family: {t.FONT_MONO};
    font-size: 11px;
    color: {t.FG_MUTED.name()};
    min-height: 28px;
    max-height: 28px;
    padding: 0 {t.SPACE[2]}px;
}}
QStatusBar::item {{
    background: transparent;
    border: none;
}}
QStatusBar QLabel {{
    color: {t.FG_SECONDARY.name()};
    background: transparent;
    padding: 0 {t.SPACE[1]}px;
}}

QPlainTextEdit {{
    background: {t.GRADIENTS['editor']};
    color: {t.FG_PRIMARY.name()};
    border: none;
    selection-background-color: {t.BG_SURFACE.name()};
    selection-color: {t.FG_PRIMARY.name()};
}}

QTreeWidget, QTreeView {{
    background: {t.GRADIENTS['sidebar']};
    border: none;
    border-right: 1px solid {t.BORDER_SUBTLE.name()};
    outline: 0;
    font-size: {t.FONT_SIZE_UI - 1}px;
    color: {t.FG_SECONDARY.name()};
}}
QTreeWidget::item, QTreeView::item {{
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[1]}px {t.SPACE[2]}px;
    min-height: 44px;
    border-radius: {t.RADIUS_SM}px;
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
QTreeView::branch {{
    background: {t.BG_PANEL.name()};
}}

QHeaderView::section {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_MUTED.name()};
    border: none;
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
    padding: {t.SPACE[1]}px {t.SPACE[2]}px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QTabWidget {{
    background-color: {t.BG_APP.name()};
}}
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
    background-color: {t.BG_APP.name()};
}}
QTabWidget > QWidget {{
    background-color: {t.BG_DEEP.name()};
}}

QTabBar {{
    background: {t.GRADIENTS['tabbar']};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QTabBar::tab {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[3]}px {t.SPACE[4]}px;
    border: none;
    border-right: 1px solid {t.BORDER_SUBTLE.name()};
    border-bottom: 2px solid transparent;
    min-width: 110px;
    max-width: 240px;
    min-height: 28px;
    font-size: {t.FONT_SIZE_UI}px;
}}
QTabBar::tab:!selected {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_MUTED.name()};
}}
QTabBar::tab:hover:!selected {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_SECONDARY.name()};
    border-bottom: 2px solid {t.BORDER_SUBTLE.name()};
}}
QTabBar::tab:selected {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border-bottom: 2px solid {t.ACCENT.name()};
    font-weight: 600;
}}
QTabBar::tab:focus {{
    outline: 2px solid {t.BORDER_FOCUS.name()};
    outline-offset: -2px;
}}
QTabBar::close-button {{
    background: transparent;
    border-radius: {t.RADIUS_SM}px;
    width: 14px;
    height: 14px;
}}
QTabBar::close-button:hover {{
    background: {t.ACCENT_PRESS.name()};
    border: 1px solid {t.DANGER.name()};
}}
"""


def search_panel_qss() -> str:
    return f"""
#search_panel {{
    background: {t.GRADIENTS['search_panel']};
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
}}
#search_panel QLineEdit {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    color: {t.FG_PRIMARY.name()};
    min-height: 44px;
}}
#search_panel QLineEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
    background-color: {t.BG_SURFACE.name()};
}}
#search_panel QPushButton {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    min-height: 28px;
    max-height: 28px;
}}
#search_panel QPushButton:hover {{
    background-color: {t.BG_SURFACE.name()};
    border-color: {t.ACCENT.name()};
    color: {t.ACCENT_HOVER.name()};
}}
#search_panel QPushButton:checked {{
    border-color: {t.ACCENT.name()};
    color: {t.ACCENT_HOVER.name()};
    background-color: {t.ACCENT_PRESS.name()};
}}
#search_panel QLabel {{
    color: {t.FG_MUTED.name()};
    font-size: {t.FONT_SIZE_UI - 2}px;
}}
"""


def command_palette_qss() -> str:
    return f"""
#command_palette {{
    background-color: {t.BG_PANEL.name()};
    border: 1px solid {t.ACCENT.name()};
    border-radius: {t.RADIUS_LG}px;
}}
#command_palette QLineEdit {{
    background-color: transparent;
    border: none;
    font-size: 14px;
    padding: {t.SPACE[3]}px {t.SPACE[4]}px;
    color: {t.FG_PRIMARY.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
    font-family: {t.FONT_UI};
    min-height: 44px;
}}
#command_palette QLineEdit:focus {{
    background-color: {t.BG_SURFACE.name()};
}}
#command_palette QListWidget {{
    background-color: transparent;
    border: none;
    padding: {t.SPACE[1]}px;
    outline: 0;
    font-family: {t.FONT_UI};
    font-size: {t.FONT_SIZE_UI}px;
}}
#command_palette QListWidget::item {{
    padding: {t.SPACE[3]}px {t.SPACE[4]}px;
    color: {t.FG_SECONDARY.name()};
    font-size: {t.FONT_SIZE_UI}px;
    border-radius: {t.RADIUS_MD}px;
    margin: {t.SPACE[1]}px {t.SPACE[1]}px;
    min-height: 44px;
}}
#command_palette QListWidget::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
#command_palette QListWidget::item:hover {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
"""


def keybindings_dialog_qss() -> str:
    return f"""
#keybindings_dialog QListWidget {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_PRIMARY.name()};
    font-size: {t.FONT_SIZE_UI}px;
    outline: 0;
    padding: {t.SPACE[1]}px;
}}
#keybindings_dialog QListWidget::item {{
    padding: {t.SPACE[3]}px {t.SPACE[3]}px;
    border-radius: {t.RADIUS_SM}px;
    min-height: 44px;
}}
#keybindings_dialog QListWidget::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
#keybindings_dialog QListWidget::item:hover {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
"""
