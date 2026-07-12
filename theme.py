from PyQt6.QtGui import QColor

class Theme:
    # Nord Theme
    NORD = {
        "background": "#2E3440",
        "foreground": "#D8DEE9",
        "keyword": "#81A1C1",
        "string": "#A3BE8C",
        "comment": "#4C566A",
        "function": "#88C0D0",
        "number": "#B48EAD",
        "type": "#EBCB8B",
        "operator": "#81A1C1",
        "decorator": "#B48EAD",
        "heading": "#81A1C1",
        "bold": "#EBCB8B",
        "italic": "#A3BE8C",
        "link": "#88C0D0",
        "code": "#4C566A",
    }

    # Basic Light Theme
    LIGHT = {
        "background": "#FFFFFF",
        "foreground": "#000000",
        "keyword": "#0000FF",
        "string": "#A31515",
        "comment": "#008000",
        "function": "#795E26",
        "number": "#098658",
        "type": "#267F99",
    }

    @staticmethod
    def get_color(theme_dict, key):
        return QColor(theme_dict.get(key, "#000000"))
