from PyQt6.QtGui import QColor

class Tokens:
    BG_DEEP     = QColor("#1E1E2E")
    BG_PANEL    = QColor("#252535")
    BG_APP      = QColor("#2D2D42")
    BG_SURFACE  = QColor("#32324A")

    FG_PRIMARY   = QColor("#E2E0F0")
    FG_SECONDARY = QColor("#9B99B8")
    FG_MUTED     = QColor("#5A5870")

    ACCENT       = QColor("#A78BFA")
    ACCENT_HOVER = QColor("#C4B5FD")
    ACCENT_PRESS = QColor("#6D5FA6")

    BORDER_SUBTLE = QColor("#3A3A55")
    BORDER_FOCUS  = QColor("#A78BFA")

    DANGER  = QColor("#F28BAB")
    SUCCESS = QColor("#A3E4C7")
    WARNING = QColor("#F9C97C")

    SYN_KEYWORD = QColor("#B78DFF")
    SYN_STRING  = QColor("#A3E4C7")
    SYN_FUNC    = QColor("#F29EDB")
    SYN_NUMBER  = QColor("#CF9FFF")
    SYN_TYPE    = QColor("#F9C97C")
    SYN_COMMENT = QColor("#7A7899")
    SYN_OPER    = QColor("#9D91C4")

    BRACKET_MATCH  = QColor("#A78BFA")
    MARGIN_LINE    = QColor("#3A3A55")
    WHITESPACE_DOT = QColor("#5A5870")

    SPACE = [0, 4, 8, 12, 16, 24, 32, 48]

    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12

    FONT_UI   = "'Inter', 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"
    FONT_SIZE_UI = 13
    FONT_SIZE_MONO = 14

    ICON_STROKE       = QColor("#9B99B8")
    ICON_STROKE_HOVER = QColor("#E2E0F0")
    ICON_ACTIVE       = QColor("#A78BFA")

    SHADOW_BLUR   = 24
    SHADOW_OFFSET = (0, 8)
    SHADOW_COLOR  = QColor(0, 0, 0, 153)

    GRADIENTS = {
        "sidebar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #252535, stop:1 #1E1E2E)",
        "tabbar":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #252535, stop:1 #1E1E2E)",
        "editor":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1E2E, stop:1 #1E1E2E)",
        "search_panel": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #252535, stop:1 #1E1E2E)",
        "statusbar":    "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A1A2E, stop:1 #161628)",
        "toolbar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2D2D42, stop:1 #252535)",
    }
