import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

# ---------------------------------------------------------------------------
# Dark Lilac palette — gerarchia di profondità a 4 livelli
# ---------------------------------------------------------------------------
# L0  bg-deep     #13101F   il nero dell'app, titlebar, bordi esterni
# L1  bg-panel    #1E1A2E   sidebar, tabbar, statusbar — un gradino sopra
# L2  bg-app      #2A2440   editor, surface principale — più chiaro, in evidenza
# L3  bg-surface  #332E50   hover, input, elementi flottanti
#
# accent          #9B6DFF   lilla principale
# accent-bright   #B78DFF   hover / testo accent
# accent-dim      #6B4DC0   pressed
# accent-glow     #2E2060   soft glow bg
#
# text-hi         #EDE8FF   testo primario (alta luminosità)
# text-mid        #A89CC8   testo secondario
# text-lo         #5C5478   testo muted / line numbers
#
# border-subtle   #2F2A47   divisori quasi invisibili
# border-visible  #3D3660   divisori leggibili
# border-accent   #5A4E8A   bordi accentuati
#
# syntax: keyword #B78DFF · string #79DDA8 · fn #F29EDB
#         number  #CF9FFF · type   #FFD085 · comment #5C5478
#         op      #9D91C4 · decorator #F29EDB
#
# danger          #FF6B8A   rosso-rosa
# success         #79DDA8   verde menta
# warning         #FFD085   ambra
# ---------------------------------------------------------------------------

FONT_UI   = "'Quicksand', 'Comfortaa', 'Segoe UI', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"

DARK_QSS = f"""
/* ── Global base ── */
QMainWindow, QWidget {{
    background-color: #1E1A2E;
    color: #EDE8FF;
    font-family: {FONT_UI};
    font-size: 12px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: #2A2440;
    border: 1px solid #3D3660;
    border-radius: 8px;
    color: #A89CC8;
    padding: 5px 12px;
}}
QPushButton:hover {{
    color: #B78DFF;
    border-color: #5A4E8A;
    background-color: #332E50;
}}
QPushButton:pressed {{
    background-color: #2E2060;
    border-color: #9B6DFF;
}}
QPushButton:checked {{
    background-color: #2E2060;
    border-color: #9B6DFF;
    color: #B78DFF;
}}

/* ── Text inputs ── */
QLineEdit, QTextEdit {{
    background-color: #2A2440;
    color: #EDE8FF;
    border: 1px solid #3D3660;
    border-radius: 8px;
    padding: 4px 10px;
    selection-background-color: #3D3660;
    selection-color: #EDE8FF;
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: #9B6DFF;
    background-color: #2E2060;
}}

/* ── Plain text / code editor ── */
QPlainTextEdit {{
    background-color: #2A2440;
    color: #EDE8FF;
    border: none;
    font-family: {FONT_MONO};
    selection-background-color: #3D3660;
    selection-color: #EDE8FF;
}}

/* ── Menu bar ── */
QMenuBar {{
    background-color: #13101F;
    color: #A89CC8;
    border-bottom: 1px solid #2F2A47;
}}
QMenuBar::item {{
    padding: 5px 12px;
    border-radius: 6px;
    color: #A89CC8;
}}
QMenuBar::item:selected {{
    background-color: #2A2440;
    color: #EDE8FF;
}}

/* ── Dropdown menus ── */
QMenu {{
    background-color: #2A2440;
    color: #EDE8FF;
    border: 1px solid #3D3660;
    border-radius: 10px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 22px;
    border-radius: 6px;
    color: #A89CC8;
}}
QMenu::item:selected {{
    background-color: #332E50;
    color: #EDE8FF;
}}
QMenu::separator {{
    height: 1px;
    background: #2F2A47;
    margin: 4px 8px;
}}

/* ── Scrollbars ── */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    width: 8px;
    height: 8px;
}}
QScrollBar::handle {{
    background-color: #3D3660;
    border-radius: 4px;
    min-height: 20px;
    min-width: 10px;
}}
QScrollBar::handle:hover {{
    background-color: #5A4E8A;
}}
QScrollBar::handle:pressed {{
    background-color: #9B6DFF;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ── Dialogs ── */
QDialog, QMessageBox {{
    background-color: #1E1A2E;
    color: #EDE8FF;
    border: 1px solid #3D3660;
}}

/* ── Tooltips ── */
QToolTip {{
    background-color: #2A2440;
    color: #EDE8FF;
    border: 1px solid #9B6DFF;
    border-radius: 6px;
    padding: 4px 8px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: #2F2A47;
    width: 1px;
    height: 1px;
}}
"""

SIDEBAR_TAB_QSS = f"""
/* ── File tree / sidebar ── */
QTreeWidget, QTreeView {{
    background-color: #1E1A2E;
    border: none;
    outline: 0;
    font-size: 12px;
    color: #A89CC8;
}}
QTreeWidget::item, QTreeView::item {{
    color: #A89CC8;
    padding: 3px 6px;
    min-height: 22px;
    border-radius: 5px;
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: #2A2440;
    color: #EDE8FF;
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: #2E2060;
    color: #EDE8FF;
}}
QTreeView::branch {{
    background: #1E1A2E;
}}

QHeaderView::section {{
    background-color: #1E1A2E;
    color: #5C5478;
    border: none;
    border-bottom: 1px solid #2F2A47;
    padding: 4px 8px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Tab widget pane (editor area) ── */
QTabWidget {{
    background-color: #2A2440;
}}
QTabWidget::pane {{
    border: none;
    border-top: 1px solid #2F2A47;
    background-color: #2A2440;
}}
QTabWidget > QWidget {{
    background-color: #13101F;
}}

/* ── Tab bar ── */
QTabBar {{
    background-color: #13101F;
    border-bottom: 1px solid #2F2A47;
}}
QTabBar::tab {{
    background-color: #13101F;
    color: #5C5478;
    padding: 7px 18px;
    border: none;
    border-right: 1px solid #2F2A47;
    border-bottom: 2px solid transparent;
    min-width: 110px;
    max-width: 240px;
    min-height: 28px;
    font-size: 12px;
}}
QTabBar::tab:!selected {{
    background-color: #13101F;
    color: #5C5478;
}}
QTabBar::tab:hover:!selected {{
    background-color: #1E1A2E;
    color: #A89CC8;
    border-bottom: 2px solid #3D3660;
}}
QTabBar::tab:selected {{
    background-color: #2A2440;
    color: #EDE8FF;
    border-bottom: 2px solid #9B6DFF;
    font-weight: 600;
}}
QTabBar::close-button {{
    background: transparent;
    border-radius: 4px;
    width: 14px;
    height: 14px;
}}
QTabBar::close-button:hover {{
    background: #3D1525;
    border: 1px solid #FF6B8A;
}}
"""

SEARCH_QSS = f"""
#search_panel {{
    background-color: #1E1A2E;
    border-top: 1px solid #2F2A47;
}}
#search_panel QLineEdit {{
    background-color: #2A2440;
    border: 1px solid #3D3660;
    border-radius: 7px;
    padding: 3px 10px;
    color: #EDE8FF;
}}
#search_panel QLineEdit:focus {{
    border-color: #9B6DFF;
    background-color: #2E2060;
}}
#search_panel QPushButton {{
    background-color: #2A2440;
    border: 1px solid #3D3660;
    border-radius: 7px;
    color: #A89CC8;
    padding: 3px 10px;
}}
#search_panel QPushButton:hover {{
    background-color: #332E50;
    border-color: #5A4E8A;
    color: #B78DFF;
}}
#search_panel QPushButton:checked {{
    border-color: #9B6DFF;
    color: #B78DFF;
    background-color: #2E2060;
}}
#search_panel QLabel {{
    color: #5C5478;
    font-size: 11px;
}}
"""

STATUSBAR_QSS = f"""
QStatusBar {{
    background-color: #13101F;
    border-top: 1px solid #2F2A47;
    font-family: {FONT_MONO};
    font-size: 11px;
    color: #5C5478;
    min-height: 24px;
    max-height: 24px;
    padding: 0 8px;
}}
QStatusBar::item {{
    background: transparent;
    border: none;
}}
QStatusBar QLabel {{
    color: #5C5478;
    background: transparent;
    padding: 0 4px;
}}
"""

def main():
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS + SIDEBAR_TAB_QSS + SEARCH_QSS + STATUSBAR_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
