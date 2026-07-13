import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

NORD_QSS = """
/* Global */
QWidget {
    background-color: #2E3440;
    color: #D8DEE9;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
}

/* Buttons */
QPushButton {
    background-color: #3B4252;
    border: 1px solid #1e222a;
    border-radius: 5px;
    color: #8892a0;
    padding: 4px 10px;
}
QPushButton:hover {
    color: #88C0D0;
    border-color: #88C0D0;
}
QPushButton:pressed {
    background-color: #434C5E;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2E3440;
    color: #D8DEE9;
    border: 1px solid #1e222a;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #88C0D0;
}

/* Menus */
QMenuBar, QMenu {
    background-color: #252A33;
    color: #8892a0;
    border: 1px solid #4C566A;
}
QMenuBar::item:selected, QMenu::item:selected {
    background-color: #3B4252;
    color: #D8DEE9;
}

/* Scrollbars */
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #2E3440;
    width: 8px;
    height: 8px;
}
QScrollBar::handle {
    background-color: #3B4252;
    border-radius: 4px;
}
QScrollBar::handle:hover {
    background-color: #434C5E;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
}

/* Dialogs */
QDialog, QMessageBox {
    background-color: #2E3440;
    color: #D8DEE9;
    border: 1px solid #1e222a;
}

/* Tooltips */
QToolTip {
    background-color: #252A33;
    color: #D8DEE9;
    border: 1px solid #1e222a;
    border-radius: 4px;
    padding: 4px 8px;
}
"""

SIDEBAR_TAB_QSS = """
/* ===== QTreeView (Sidebar) ===== */
QTreeView {
    background-color: #252A33;  /* bg1 */
    border: none;
    show-decoration-selected: 1;
    outline: 0;
    font-size: 11px;
}
QTreeView::item {
    color: #8892a0;  /* fg1 */
    padding: 5px 10px;
    border-left: 3px solid transparent;
}
QTreeView::item:hover {
    background-color: #3B4252;  /* bg2 */
    color: #D8DEE9;  /* fg0 */
    border-left-color: #88C0D0;  /* accent */
}
QTreeView::item:selected {
    background-color: #434C5E;  /* bg3 */
    color: #D8DEE9;  /* fg0 */
    border-left-color: #88C0D0;  /* accent */
    font-weight: bold;
}
QTreeView::branch {
    background: transparent;
}

QHeaderView::section {
    background-color: #252A33;  /* bg1 */
    color: #4C566A;  /* fg2 */
    border: none;
    border-bottom: 1px solid #1e222a;  /* border */
    padding: 4px 8px;
}

/* ===== QTabWidget / QTabBar ===== */
QTabWidget::pane {
    border-top: 1px solid #1e222a;  /* border */
    background-color: #2E3440;  /* bg0 */
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #252A33;  /* bg1 */
    color: #4C566A;  /* fg2 */
    padding: 8px 14px;
    border: 1px solid #1e222a;  /* border */
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    min-width: 180px;
    max-width: 300px;
    min-height: 28px;
    line-height: 1.3;
}
QTabBar::tab:hover {
    background-color: #2E3440;
    color: #D8DEE9;  /* fg0 */
}
QTabBar::tab:selected {
    background-color: #3B4252;  /* bg2 */
    color: #ECEFF4;  /* snow storm */
    border-color: #434C5E;  /* bg3 */
    border-bottom: 2px solid #88C0D0;  /* accent */
    padding-bottom: 5px;
}

QTabBar::close-button {
    background: transparent;
    border: 1px solid #4C566A;
    border-radius: 3px;
    width: 16px;
    height: 16px;
    color: #8892a0;
}
QTabBar::tab:selected QTabBar::close-button {
    color: #D8DEE9;
}
QTabBar::close-button:hover {
    background: #3B4252;
    border-color: #BF616A;
}
"""

SEARCH_QSS = """
#search_panel {
    background-color: #252A33;
    border-top: 1px solid #1e222a;
}
#search_panel QLineEdit {
    background-color: #3B4252;
    border: 1px solid #1e222a;
    border-radius: 4px;
    padding: 2px 8px;
    color: #D8DEE9;
}
#search_panel QLineEdit:focus {
    border-color: #88C0D0;
}
#search_panel QPushButton {
    background-color: #3B4252;
    border: 1px solid #1e222a;
    border-radius: 4px;
    color: #D8DEE9;
    padding: 2px 8px;
}
#search_panel QPushButton:checked {
    border-color: #88C0D0;
    color: #88C0D0;
}
#search_panel QLabel {
    color: #4C566A;
    font-size: 10px;
}
#search_panel QPushButton[text="Find Next ↓"], 
#search_panel QPushButton[text="Find Prev ↑"] {
    background-color: transparent;
    border: none;
    color: #8892a0;
}
#search_panel QPushButton[text="Find Next ↓"]:hover,
#search_panel QPushButton[text="Find Prev ↑"]:hover {
    color: #88C0D0;
}
"""

STATUSBAR_QSS = """
QStatusBar {
    background-color: #252A33;
    border-top: 1px solid #1e222a;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #4C566A;
    min-height: 24px;
    max-height: 24px;
    padding: 0 8px;
}
QStatusBar::item {
    border: none;
    background: transparent;
}
QLabel {
    color: inherit;
    background: transparent;
    padding: 0 4px;
}
"""

def main():
    # Wayland / Niri / NVIDIA specific configurations
    
    # Force Wayland platform
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb" 
    
    # Minimal Client Side Decorations for Niri
    # os.environ["QT_WAYLAND_DISABLE_WINDOWDECORATION"] = "1"
    
    # NVIDIA Wayland stability suggestions
    # os.environ["__GL_GSYNC_ALLOWED"] = "1"
    # os.environ["__GL_VRR_ALLOWED"] = "1"

    app = QApplication(sys.argv)
    app.setStyleSheet(NORD_QSS + SIDEBAR_TAB_QSS + SEARCH_QSS + STATUSBAR_QSS)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


