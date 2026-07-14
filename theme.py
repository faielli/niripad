from PyQt6.QtGui import QColor
from theme_tokens import Tokens

class Theme:
    NORD = {
        "background": "#2E3440", "foreground": "#D8DEE9",
        "keyword": "#81A1C1", "string": "#A3BE8C", "comment": "#4C566A",
        "function": "#88C0D0", "number": "#B48EAD", "type": "#EBCB8B",
        "operator": "#81A1C1", "decorator": "#B48EAD", "heading": "#81A1C1",
        "bold": "#EBCB8B", "italic": "#A3BE8C", "link": "#88C0D0", "code": "#4C566A",
    }

    LILAC = {
        "background":  Tokens.BG_APP.name(),
        "foreground":  Tokens.FG_PRIMARY.name(),
        "keyword":     Tokens.SYN_KEYWORD.name(),
        "string":      Tokens.SYN_STRING.name(),
        "comment":     Tokens.SYN_COMMENT.name(),
        "function":    Tokens.SYN_FUNC.name(),
        "number":      Tokens.SYN_NUMBER.name(),
        "type":        Tokens.SYN_TYPE.name(),
        "operator":    Tokens.SYN_OPER.name(),
        "decorator":   Tokens.SYN_FUNC.name(),
        "heading":     Tokens.SYN_KEYWORD.name(),
        "bold":        Tokens.SYN_TYPE.name(),
        "italic":      Tokens.SYN_STRING.name(),
        "link":        QColor("#7EB8F7").name(),
        "code":        Tokens.SYN_COMMENT.name(),
    }

    LIGHT = {
        "background": "#FFFFFF", "foreground": "#000000",
        "keyword": "#0000FF", "string": "#A31515", "comment": "#008000",
        "function": "#795E26", "number": "#098658", "type": "#267F99",
    }

    @staticmethod
    def get_color(theme_dict, key):
        return QColor(theme_dict.get(key, Tokens.FG_PRIMARY.name()))
