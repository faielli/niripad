import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from qss_tokens import qss, search_panel_qss, command_palette_qss, keybindings_dialog_qss


def main():
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setStyleSheet(qss() + search_panel_qss() + command_palette_qss() + keybindings_dialog_qss())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
