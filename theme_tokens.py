from PyQt6.QtGui import QColor

class Tokens:
    BG_DEEP     = QColor("#13101F")
    BG_PANEL    = QColor("#1E1A2E")
    BG_APP      = QColor("#2A2440")
    BG_SURFACE  = QColor("#332E50")

    FG_PRIMARY   = QColor("#EDE8FF")
    FG_SECONDARY = QColor("#C8BFE8")
    FG_MUTED     = QColor("#9B8FD0")

    ACCENT       = QColor("#A885FF")
    ACCENT_HOVER = QColor("#C4A5FF")
    ACCENT_PRESS = QColor("#8A6DCC")

    BORDER_SUBTLE = QColor("#5A4E8A")
    BORDER_FOCUS  = QColor("#A885FF")

    DANGER  = QColor("#FF6B8A")
    SUCCESS = QColor("#79DDA8")
    WARNING = QColor("#FFD085")

    SYN_KEYWORD = QColor("#B78DFF")
    SYN_STRING  = QColor("#79DDA8")
    SYN_FUNC    = QColor("#F29EDB")
    SYN_NUMBER  = QColor("#CF9FFF")
    SYN_TYPE    = QColor("#FFD085")
    SYN_COMMENT = QColor("#9B8FD0")
    SYN_OPER    = QColor("#9D91C4")

    SPACE = [0, 4, 8, 12, 16, 24, 32, 48]

    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12

    FONT_UI   = "'Quicksand', 'Comfortaa', 'Segoe UI', sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', 'Monospace'"
    FONT_SIZE_UI = 13
    FONT_SIZE_MONO = 13

    ICON_STROKE      = QColor("#C8BFE8")
    ICON_STROKE_HOVER = QColor("#EDE8FF")
    ICON_ACTIVE      = QColor("#A885FF")

    SHADOW_BLUR   = 8
    SHADOW_OFFSET = (0, 2)
    SHADOW_COLOR  = QColor(0, 0, 0, 25)

    GRADIENTS = {
        "sidebar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2A2440, stop:1 #1E1A2E)",
        "tabbar":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1A2E, stop:1 #13101F)",
        "editor":       "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2A2440, stop:1 #242038)",
        "search_panel": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1A2E, stop:1 #161226)",
        "statusbar":    "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #13101F, stop:1 #0D0A16)",
        "toolbar":      "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2A2440, stop:1 #1E1A2E)",
    }
