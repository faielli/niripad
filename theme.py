import warnings
from PyQt6.QtGui import QColor
from theme_tokens import Tokens

class Theme:
    NORD = {
        "background": QColor("#2E3440"),
        "foreground": QColor("#D8DEE9"),
        "keyword": QColor("#81A1C1"),
        "string": QColor("#A3BE8C"),
        "comment": QColor("#4C566A"),
        "function": QColor("#88C0D0"),
        "number": QColor("#B48EAD"),
        "type": QColor("#EBCB8B"),
        "operator": QColor("#81A1C1"),
        "decorator": QColor("#B48EAD"),
        "heading": QColor("#81A1C1"),
        "bold": QColor("#EBCB8B"),
        "italic": QColor("#A3BE8C"),
        "link": QColor("#88C0D0"),
        "code": QColor("#4C566A"),
        "selection_background": QColor("#434C5E"),
        "selection_foreground": QColor("#ECEFF4"),
        "gutter_bg": QColor("#2E3440"),
        "line_number_fg": QColor("#4C566A"),
        "current_line_bg": QColor("#3B4252"),
    }

    LILAC = {
        "background":  Tokens.BG_APP,
        "foreground":  Tokens.FG_PRIMARY,
        "keyword":     Tokens.SYN_KEYWORD,
        "string":      Tokens.SYN_STRING,
        "comment":     Tokens.SYN_COMMENT,
        "function":    Tokens.SYN_FUNC,
        "number":      Tokens.SYN_NUMBER,
        "type":        Tokens.SYN_TYPE,
        "operator":    Tokens.SYN_OPER,
        "decorator":   Tokens.SYN_FUNC,
        "heading":     Tokens.SYN_KEYWORD,
        "bold":        Tokens.SYN_TYPE,
        "italic":      Tokens.SYN_STRING,
        "link":        Tokens.ACCENT,
        "code":        Tokens.SYN_COMMENT,
        "selection_background": Tokens.SELECTION_BG,
        "selection_foreground": Tokens.FG_PRIMARY,
        "gutter_bg": Tokens.BG_PANEL,
        "line_number_fg": Tokens.FG_MUTED,
        "current_line_bg": Tokens.CURRENT_LINE_BG,
    }

    LIGHT = {
        "background": QColor("#FFFFFF"),
        "foreground": QColor("#000000"),
        "keyword": QColor("#0000FF"),
        "string": QColor("#A31515"),
        "comment": QColor("#008000"),
        "function": QColor("#795E26"),
        "number": QColor("#098658"),
        "type": QColor("#267F99"),
        "operator": QColor("#666666"),
        "decorator": QColor("#795E26"),
        "heading": QColor("#0000FF"),
        "bold": QColor("#000000"),
        "italic": QColor("#A31515"),
        "link": QColor("#0563C1"),
        "code": QColor("#008000"),
        "selection_background": QColor("#ADD6FF"),
        "selection_foreground": QColor("#000000"),
        "gutter_bg": QColor("#F0F0F0"),
        "line_number_fg": QColor("#888888"),
        "current_line_bg": QColor("#E8E8E8"),
    }

    THEMES = {
        "nord": NORD,
        "lilac": LILAC,
        "light": LIGHT,
    }

    @staticmethod
    def by_name(name):
        if name not in Theme.THEMES:
            warnings.warn(f"Unknown theme '{name}', falling back to lilac")
            return Theme.LILAC
        return Theme.THEMES[name]

    @staticmethod
    def get_color(theme_dict, key):
        if not isinstance(theme_dict, dict):
            return QColor(str(theme_dict)) if not isinstance(theme_dict, QColor) else theme_dict
        val = theme_dict.get(key, Tokens.FG_PRIMARY)
        if isinstance(val, QColor):
            return val
        return QColor(val)
