import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

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
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
