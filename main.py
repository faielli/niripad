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
    app.setStyleSheet(NORD_QSS)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

