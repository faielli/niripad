from PyQt6.QtGui import QColor

class Tokens:
    BG_DEEP     = QColor("#11111B")  # Catppuccin Mocha crust
    BG_PANEL    = QColor("#181825")  # Catppuccin Mocha mantle
    BG_APP      = QColor("#1E1E2E")  # Catppuccin Mocha base
    BG_SURFACE  = QColor("#313244")  # Catppuccin Mocha surface0

    FG_PRIMARY   = QColor("#CDD6F4")  # Catppuccin Mocha text
    FG_SECONDARY = QColor("#BAC2DE")  # Catppuccin Mocha subtext1
    FG_MUTED     = QColor("#6C7086")  # Catppuccin Mocha overlay0

    ACCENT       = QColor("#CBA6F7")  # Catppuccin Mocha mauve
    ACCENT_HOVER = QColor("#F5C2E7")  # Catppuccin Mocha pink
    ACCENT_PRESS = QColor("#B4BEFE")  # Catppuccin Mocha lavender

    BORDER_SUBTLE = QColor("#313244")  # surface0
    BORDER_FOCUS  = QColor("#CBA6F7")  # mauve

    DANGER  = QColor("#F38BA8")  # Catppuccin Mocha red
    SUCCESS = QColor("#A6E3A1")  # Catppuccin Mocha green
    WARNING = QColor("#F9E2AF")  # Catppuccin Mocha yellow

    SYN_KEYWORD = QColor("#CBA6F7")  # mauve
    SYN_STRING  = QColor("#A6E3A1")  # green
    SYN_FUNC    = QColor("#F5C2E7")  # pink
    SYN_NUMBER  = QColor("#FAB387")  # peach
    SYN_TYPE    = QColor("#F9E2AF")  # yellow
    SYN_COMMENT = QColor("#6C7086")  # overlay0
    SYN_OPER    = QColor("#89DCEB")  # sky

    CURRENT_LINE_BG = QColor("#A37EBE")  # mauve scuro — current line tint
    SELECTION_BG    = QColor("#FFD8F0")  # pink chiaro — base for rgba selection

    BRACKET_MATCH  = QColor("#FAB387")  # peach
    MARGIN_LINE    = QColor("#313244")  # surface0
    WHITESPACE_DOT = QColor("#45475A")  # surface1

    SPACE = [0, 4, 8, 12, 16, 24, 32, 48]

    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12

    FONT_UI   = "'Inter', 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"
    FONT_SIZE_UI = 13
    FONT_SIZE_MONO = 14

    ICON_STROKE       = QColor("#BAC2DE")  # subtext1
    ICON_STROKE_HOVER = QColor("#CDD6F4")  # text
    ICON_ACTIVE       = QColor("#CBA6F7")  # mauve

    SHADOW_BLUR   = 24
    SHADOW_OFFSET = (0, 8)
    SHADOW_COLOR  = QColor(0, 0, 0, 153)

    GRADIENTS = {
        "sidebar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #181825, stop:1 #11111B)",
        "tabbar":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #181825, stop:1 #11111B)",
        "editor":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1E2E, stop:1 #1E1E2E)",
        "search_panel": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #181825, stop:1 #11111B)",
        "statusbar":    "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #11111B, stop:1 #11111B)",
        "toolbar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1E2E, stop:1 #181825)",
    }
