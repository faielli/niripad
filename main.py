import sys
import os
from logging_config import setup_logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from qss_tokens import global_qss


def main():
    if "QT_QPA_PLATFORM" not in os.environ and sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    setup_logging()

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app.setStyleSheet(global_qss())

    window = MainWindow()
    window.show()

    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    for path in args:
        resolved = os.path.abspath(path)
        window.open_file(resolved)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
