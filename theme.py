from PyQt6.QtGui import QColor

class Theme:
    NORD = {
        "background": "#2E3440", "foreground": "#D8DEE9",
        "keyword": "#81A1C1", "string": "#A3BE8C", "comment": "#4C566A",
        "function": "#88C0D0", "number": "#B48EAD", "type": "#EBCB8B",
        "operator": "#81A1C1", "decorator": "#B48EAD", "heading": "#81A1C1",
        "bold": "#EBCB8B", "italic": "#A3BE8C", "link": "#88C0D0", "code": "#4C566A",
    }

    # Dark Lilac — editor background è L2 (#2A2440), testo leggibile su di esso
    LILAC = {
        "background":  "#2A2440",   # L2 — editor bg
        "foreground":  "#EDE8FF",   # testo principale
        "keyword":     "#B78DFF",   # lilla chiaro
        "string":      "#79DDA8",   # menta
        "comment":     "#5C5478",   # muted — quasi invisibile, buono per commenti
        "function":    "#F29EDB",   # rosa
        "number":      "#CF9FFF",   # lavanda
        "type":        "#FFD085",   # ambra
        "operator":    "#9D91C4",   # grigio-lilla
        "decorator":   "#F29EDB",   # rosa (uguale a function)
        "heading":     "#B78DFF",
        "bold":        "#FFD085",
        "italic":      "#79DDA8",
        "link":        "#7EB8F7",
        "code":        "#5C5478",
    }

    LIGHT = {
        "background": "#FFFFFF", "foreground": "#000000",
        "keyword": "#0000FF", "string": "#A31515", "comment": "#008000",
        "function": "#795E26", "number": "#098658", "type": "#267F99",
    }

    @staticmethod
    def get_color(theme_dict, key):
        return QColor(theme_dict.get(key, "#EDE8FF"))
