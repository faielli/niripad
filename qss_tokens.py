from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from theme_tokens import Tokens

t = Tokens


def apply_shadow(widget: QWidget):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(t.SHADOW_BLUR)
    effect.setOffset(t.SHADOW_OFFSET[0], t.SHADOW_OFFSET[1])
    effect.setColor(t.SHADOW_COLOR)
    widget.setGraphicsEffect(effect)


def global_qss() -> str:
    return f"""
QMainWindow {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
}}

QWidget {{
    color: {t.FG_PRIMARY.name()};
    font-family: {t.FONT_UI};
    font-size: {t.FONT_SIZE_UI}px;
}}

QMenuBar {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
    padding: 2px 4px;
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
    spacing: 0px;
}}
QMenuBar::item {{
    padding: 4px 12px;
    border-radius: 6px;
    background: transparent;
}}
QMenuBar::item:selected, QMenuBar::item:pressed {{
    background-color: {t.ACCENT_PRESS.name()};
    color: {t.ACCENT_HOVER.name()};
}}
QMenu {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: 4px;
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
}}
QMenu::item {{
    padding: 6px 28px 6px 12px;
    border-radius: {t.RADIUS_SM}px;
    background: transparent;
    color: {t.FG_PRIMARY.name()};
}}
QMenu::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}
QMenu::separator {{
    height: 1px;
    background: {t.BORDER_SUBTLE.name()};
    margin: 4px 8px;
}}
QMenu::indicator {{
    width: 14px;
    height: 14px;
}}

QTabWidget::pane {{
    border: none;
    background: {t.BG_DEEP.name()};
}}
QTabWidget::tab-bar {{
    alignment: left;
}}
QTabWidget > QWidget {{
    background-color: {t.BG_DEEP.name()};
}}
QTabBar {{
    background: {t.BG_PANEL.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QTabBar::tab {{
    background: transparent;
    color: {t.FG_MUTED.name()};
    font-size: 13px;
    padding: 0px 24px;
    height: 34px;
    min-width: 130px;
    max-width: 220px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}}
QTabBar::tab:hover {{
    background: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
}}
QTabBar::tab:selected {{
    background: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
    border-bottom: 2px solid {t.ACCENT.name()};
    font-weight: 500;
}}
QTabBar::tab:!selected {{
    margin-top: 2px;
}}
QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
    padding: 2px;
}}

QTreeWidget {{
    background: {t.BG_PANEL.name()};
    border: none;
    color: {t.FG_PRIMARY.name()};
    font-size: 12px;
    outline: none;
    padding: 4px 0;
}}
QTreeWidget::item {{
    padding: 4px 8px;
    border-radius: {t.RADIUS_SM}px;
    min-height: 24px;
    color: {t.FG_PRIMARY.name()};
}}
QTreeWidget::item:hover {{
    background: {t.BG_APP.name()};
}}
QTreeWidget::item:selected {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}
QTreeWidget::branch {{
    background: transparent;
}}

QPlainTextEdit, QTextEdit {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
    font-family: {t.FONT_MONO};
    font-size: {t.FONT_SIZE_MONO}pt;
    line-height: 1.6;
    border: none;
    selection-background-color: {t.BG_SURFACE.name()};
    selection-color: {t.FG_PRIMARY.name()};
    padding: 8px 0;
}}

QStatusBar {{
    background-color: #1A1A2E;
    color: {t.FG_MUTED.name()};
    font-size: 11px;
    font-family: {t.FONT_MONO};
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
    padding: 0 12px;
    min-height: 24px;
    max-height: 24px;
}}
QStatusBar::item {{
    border: none;
    padding: 0 8px;
}}
QStatusBar QLabel {{
    color: {t.FG_MUTED.name()};
    background: transparent;
    padding: 0 4px;
}}

QScrollBar:vertical {{
    background: {t.BG_DEEP.name()};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.BORDER_SUBTLE.name()};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.ACCENT.name()};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {t.BG_DEEP.name()};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {t.BORDER_SUBTLE.name()};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t.ACCENT.name()};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── File Dialog ─────────────────────────────────────── */
QFileDialog {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
}}
QFileDialog QWidget {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
}}
QFileDialog QListView,
QFileDialog QTreeView {{
    background: {t.BG_PANEL.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: 6px;
    outline: none;
}}
QFileDialog QListView::item:selected,
QFileDialog QTreeView::item:selected {{
    background: {t.BG_APP.name()};
    color: {t.ACCENT_HOVER.name()};
}}
QFileDialog QListView::item:hover,
QFileDialog QTreeView::item:hover {{
    background: {t.BG_APP.name()};
}}
QFileDialog QLineEdit {{
    background: {t.BG_DEEP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: 6px;
    color: {t.FG_PRIMARY.name()};
    padding: 5px 10px;
    font-size: 13px;
}}
QFileDialog QLineEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
}}
QFileDialog QComboBox {{
    background: {t.BG_PANEL.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: 6px;
    color: {t.FG_PRIMARY.name()};
    padding: 4px 10px;
    font-size: 13px;
}}
QFileDialog QComboBox:hover {{
    border-color: {t.BORDER_FOCUS.name()};
}}
QFileDialog QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QFileDialog QPushButton {{
    background: {t.BG_APP.name()};
    color: {t.ACCENT_HOVER.name()};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    min-width: 72px;
}}
QFileDialog QPushButton:hover {{
    background: {t.ACCENT.name()};
    color: {t.BG_DEEP.name()};
}}
QFileDialog QPushButton:pressed {{
    background: {t.ACCENT_PRESS.name()};
    color: {t.FG_PRIMARY.name()};
}}
QFileDialog QToolButton {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {t.FG_SECONDARY.name()};
    padding: 4px;
}}
QFileDialog QToolButton:hover {{
    background: {t.BG_APP.name()};
    color: {t.ACCENT.name()};
}}
QFileDialog QHeaderView::section {{
    background: {t.BG_PANEL.name()};
    color: {t.FG_SECONDARY.name()};
    border: none;
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
    padding: 4px 8px;
    font-size: 12px;
}}
QFileDialog QSplitter::handle {{
    background: {t.BORDER_SUBTLE.name()};
}}
QFileDialog QLabel {{
    color: {t.FG_SECONDARY.name()};
    font-size: 13px;
}}

QSplitter::handle {{
    background: {t.BORDER_SUBTLE.name()};
    width: 1px;
    height: 1px;
}}
QSplitter::handle:hover {{
    background: {t.ACCENT.name()};
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
    padding: 6px 10px;
}}

QPushButton {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_SECONDARY.name()};
    padding: 4px 12px;
    min-height: 28px;
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
    border: 2px solid {t.BORDER_FOCUS.name()};
}}
QPushButton:disabled {{
    color: {t.FG_MUTED.name()};
    border-color: {t.BORDER_SUBTLE.name()};
    background-color: {t.BG_PANEL.name()};
}}

QLineEdit {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_SM}px;
    padding: 5px 10px;
    selection-background-color: {t.BG_SURFACE.name()};
    selection-color: {t.FG_PRIMARY.name()};
    min-height: 24px;
}}
QLineEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
    background-color: {t.BG_DEEP.name()};
}}

QToolButton {{
    background: transparent;
    border: none;
    border-radius: {t.RADIUS_SM}px;
    padding: 2px;
}}
QToolButton:hover {{
    background-color: {t.BG_APP.name()};
}}
QToolButton:pressed {{
    background-color: {t.BG_SURFACE.name()};
}}

/* ── Sidebar Header ──────────────────────────────────── */
QWidget#sidebar_header {{
    background-color: {t.BG_PANEL.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QWidget#sidebar_header QToolButton {{
    background: transparent;
    border: none;
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_SECONDARY.name()};
    padding: 3px;
}}
QWidget#sidebar_header QToolButton:hover {{
    background: {t.BG_APP.name()};
    color: {t.ACCENT.name()};
}}

/* ── Command Palette ─────────────────────────────────── */
#command_palette {{
    background: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: 12px;
}}
#command_search_input {{
    background: {t.BG_DEEP.name()};
    border: 1px solid {t.BORDER_FOCUS.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_PRIMARY.name()};
    font-size: 14px;
    padding: 10px 14px;
    selection-background-color: {t.BG_SURFACE.name()};
    font-family: {t.FONT_UI};
    min-height: 24px;
}}
#command_action_list {{
    background: transparent;
    border: none;
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
    outline: none;
    font-family: {t.FONT_UI};
}}
#command_action_list::item {{
    padding: 8px 12px;
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_PRIMARY.name()};
}}
#command_action_list::item:selected {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}
#command_action_list::item:hover {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}

/* ── Keybindings Dialog ──────────────────────────────── */
#keybindings_dialog {{
    background: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_LG}px;
}}
#keybindings_list {{
    background-color: {t.BG_DEEP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
    outline: none;
    padding: 4px;
}}
#keybindings_list::item {{
    padding: 8px 12px;
    border-radius: {t.RADIUS_SM}px;
    min-height: 28px;
}}
#keybindings_list::item:selected {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}
#keybindings_list::item:hover {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
}}
#keybindings_label {{
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
}}
#keybindings_save_btn {{
    background-color: {t.ACCENT.name()};
    color: {t.BG_DEEP.name()};
    border: none;
    border-radius: {t.RADIUS_SM}px;
    padding: 6px 16px;
    min-height: 28px;
    font-weight: 500;
}}
#keybindings_save_btn:hover {{
    background-color: {t.ACCENT_HOVER.name()};
}}
#keybindings_save_btn:pressed {{
    background-color: {t.ACCENT_PRESS.name()};
}}
#keybindings_cancel_btn {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_SECONDARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_SM}px;
    padding: 6px 16px;
    min-height: 28px;
}}
#keybindings_cancel_btn:hover {{
    color: {t.ACCENT_HOVER.name()};
    border-color: {t.ACCENT.name()};
    background-color: {t.BG_SURFACE.name()};
}}
"""


def search_panel_qss() -> str:
    return f"""
#search_panel {{
    background: {t.BG_PANEL.name()};
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
    padding: 6px 12px;
}}
#search_panel QLineEdit {{
    background-color: {t.BG_DEEP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_PRIMARY.name()};
    font-size: 13px;
    padding: 5px 10px;
    min-width: 200px;
}}
#search_panel QLineEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
}}
#search_panel QPushButton {{
    background: {t.BG_SURFACE.name()};
    color: {t.ACCENT_HOVER.name()};
    border: none;
    border-radius: {t.RADIUS_SM}px;
    padding: 5px 12px;
    font-size: 12px;
}}
#search_panel QPushButton:hover {{
    background: {t.ACCENT.name()};
    color: {t.BG_DEEP.name()};
}}
#search_panel QPushButton:checked {{
    background: {t.ACCENT_PRESS.name()};
    color: {t.ACCENT_HOVER.name()};
}}
#search_panel QLabel {{
    color: {t.FG_MUTED.name()};
    font-size: 11px;
}}

#goto_line_panel {{
    background: {t.BG_PANEL.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
#goto_line_panel QLineEdit {{
    background-color: {t.BG_DEEP.name()};
    border: 1px solid {t.BORDER_FOCUS.name()};
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_PRIMARY.name()};
    padding: 5px 10px;
    font-family: {t.FONT_MONO};
    min-height: 24px;
}}
#goto_line_panel QLineEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
    background-color: {t.BG_DEEP.name()};
}}
"""

