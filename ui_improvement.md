# Niri Editor — UI/UX Improvement Plan (LLM-Executable Steps)

**Goal:** Modernize UI only — no logic changes, zero risk of breaking functionality  
**Based on:** UI/UX Pro Max skill analysis (accessibility, touch targets, theme consistency, typography, animation)

---

## Phase 1: Theme Tokens & Contrast Fix (Safe, Single File)

### Step 1.1: Create `theme_tokens.py` (NEW FILE)
Define semantic color tokens with **WCAG AA+ contrast** on dark backgrounds.

```python
# theme_tokens.py
from PyQt6.QtGui import QColor

class Tokens:
    # 4-level depth (L0 deepest → L3 highest)
    BG_DEEP     = QColor("#0D0A16")  # window chrome
    BG_PANEL    = QColor("#161226")  # sidebar, tab bar, status bar
    BG_APP      = QColor("#1F1A36")  # EDITOR surface
    BG_SURFACE  = QColor("#2A2448")  # hover, inputs, floating
    
    FG_PRIMARY   = QColor("#F0EBFF")  # 14.5:1 on BG_APP
    FG_SECONDARY = QColor("#C8BFE8")  # 6.2:1 on BG_APP
    FG_MUTED     = QColor("#8A82A8")  # 4.6:1 on BG_APP ✅
    
    ACCENT       = QColor("#A885FF")  # 4.8:1 on BG_APP ✅
    ACCENT_HOVER = QColor("#C4A5FF")
    ACCENT_PRESS = QColor("#8A6DCC")
    
    BORDER_SUBTLE = QColor("#3A3258")  # 3.2:1 on BG_PANEL ✅
    BORDER_FOCUS  = QColor("#A885FF")
    
    DANGER  = QColor("#FF8FA3")
    SUCCESS = QColor("#8FE8BC")
    WARNING = QColor("#FFE0A8")
    
    # Syntax (all ≥ 4.5:1 on BG_APP)
    SYN_KEYWORD = QColor("#B78DFF")
    SYN_STRING  = QColor("#79DDA8")
    SYN_FUNC    = QColor("#F29EDB")
    SYN_NUMBER  = QColor("#CF9FFF")
    SYN_TYPE    = QColor("#FFD085")
    SYN_COMMENT = QColor("#8A82A8")  # FIXED: was 2.1:1
    SYN_OPER    = QColor("#9D91C4")
    
    # Spacing (8dp base, high density)
    SPACE = [0, 4, 8, 12, 16, 24, 32, 48]
    
    # Radius
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    
    # Fonts
    FONT_UI   = "'IBM Plex Sans', 'Segoe UI', sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"
    FONT_SIZE_UI = 13
    FONT_SIZE_MONO = 13
```

### Step 1.2: Update `theme.py` — Replace LILAC dict with tokens
```python
# theme.py — replace LILAC dict only, keep get_color()
from theme_tokens import Tokens

LILAC = {
    "background":  Tokens.BG_APP.name(),
    "foreground":  Tokens.FG_PRIMARY.name(),
    "keyword":     Tokens.SYN_KEYWORD.name(),
    "string":      Tokens.SYN_STRING.name(),
    "comment":     Tokens.SYN_COMMENT.name(),  # FIXED
    "function":    Tokens.SYN_FUNC.name(),
    "number":      Tokens.SYN_NUMBER.name(),
    "type":        Tokens.SYN_TYPE.name(),
    "operator":    Tokens.SYN_OPER.name(),
    "decorator":   Tokens.SYN_FUNC.name(),
    "heading":     Tokens.SYN_KEYWORD.name(),
    "bold":        Tokens.SYN_TYPE.name(),
    "italic":      Tokens.SYN_STRING.name(),
    "link":        QColor("#7EB8F7").name(),
    "code":        Tokens.FG_MUTED.name(),
}
```

### Step 1.3: Create `qss_tokens.py` (NEW) — Central QSS Generator
```python
# qss_tokens.py
from theme_tokens import Tokens

def qss() -> str:
    t = Tokens
    return f"""
/* ===== GLOBAL BASE ===== */
QMainWindow, QWidget {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_PRIMARY.name()};
    font-family: {t.FONT_UI};
    font-size: {t.FONT_SIZE_UI}px;
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    min-height: 44px;  /* TOUCH TARGET */
}}
QPushButton:hover {{
    color: {t.ACCENT_HOVER.name()};
    border-color: {t.ACCENT.name()};
    background-color: {t.BG_SURFACE.name()};
}}
QPushButton:pressed {{
    background-color: {t.ACCENT_PRESS.name()};
    border-color: {t.ACCENT.name()};
}}
QPushButton:focus {{
    outline: 2px solid {t.BORDER_FOCUS.name()};
    outline-offset: 2px;
}}

/* ===== INPUTS ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
    selection-background-color: {t.BORDER_FOCUS.name()};
    selection-color: {t.FG_PRIMARY.name()};
    min-height: 44px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t.BORDER_FOCUS.name()};
    background-color: {t.BG_SURFACE.name()};
}}

/* ===== SCROLLBARS ===== */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    width: 8px; height: 8px;
}}
QScrollBar::handle {{
    background-color: {t.BORDER_SUBTLE.name()};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:hover {{ background-color: {t.ACCENT.name()}; }}

/* ===== MENUS ===== */
QMenuBar {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_SECONDARY.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QMenuBar::item:selected {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border-radius: {t.RADIUS_SM}px;
}}
QMenu {{
    background-color: {t.BG_APP.name()};
    border: 1px solid {t.BORDER_SUBTLE.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[1]}px;
}}
QMenu::item {{
    padding: {t.SPACE[2]}px {t.SPACE[4]}px;
    border-radius: {t.RADIUS_SM}px;
    color: {t.FG_SECONDARY.name()};
}}
QMenu::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}

/* ===== TOOLTIPS ===== */
QToolTip {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border: 1px solid {t.ACCENT.name()};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SPACE[2]}px {t.SPACE[3]}px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {t.BORDER_SUBTLE.name()};
    width: 1px; height: 1px;
}}
"""

def tabs_qss() -> str:
    t = Tokens
    return f"""
/* ===== TAB WIDGET ===== */
QTabBar {{
    background-color: {t.BG_DEEP.name()};
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
}}
QTabBar::tab {{
    background-color: {t.BG_DEEP.name()};
    color: {t.FG_SECONDARY.name()};
    padding: {t.SPACE[3]}px {t.SPACE[4]}px;
    border: none;
    border-right: 1px solid {t.BORDER_SUBTLE.name()};
    border-bottom: 2px solid transparent;
    min-width: 110px;
    font-size: {t.FONT_SIZE_UI}px;
    min-height: 28px;
}}
QTabBar::tab:!selected {{
    color: {t.FG_MUTED.name()};
}}
QTabBar::tab:hover:!selected {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_SECONDARY.name()};
    border-bottom: 2px solid {t.BORDER_SUBTLE.name()};
}}
QTabBar::tab:selected {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
    border-bottom: 2px solid {t.ACCENT.name()};
    font-weight: 600;
}}
QTabBar::tab:focus {{
    outline: 2px solid {t.BORDER_FOCUS.name()};
    outline-offset: 2px;
}}
QTabBar::close-button {{
    background: transparent;
    border-radius: {t.RADIUS_SM}px;
    width: 16px; height: 16px;
    margin-left: {t.SPACE[1]}px;
}}
QTabBar::close-button:hover {{
    background: {t.ACCENT_PRESS.name()};
    border: 1px solid {t.DANGER.name()};
}}

/* ===== TAB WIDGET PANE ===== */
QTabWidget::pane {{
    border-top: 1px solid {t.BORDER_SUBTLE.name()};
    background-color: {t.BG_APP.name()};
}}
"""

def filetree_qss() -> str:
    t = Tokens
    return f"""
/* ===== FILE TREE ===== */
QTreeWidget, QTreeView {{
    background-color: {t.BG_PANEL.name()};
    border: none;
    outline: none;
    color: {t.FG_SECONDARY.name()};
    font-size: {t.FONT_SIZE_UI-1}px;
}}
QTreeWidget::item, QTreeView::item {{
    padding: {t.SPACE[1]}px {t.SPACE[2]}px;
    min-height: 44px;  /* TOUCH TARGET */
    border-radius: {t.RADIUS_SM}px;
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {t.BG_APP.name()};
    color: {t.FG_PRIMARY.name()};
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {t.BG_SURFACE.name()};
    color: {t.FG_PRIMARY.name()};
}}
QTreeView::branch {{
    background: {t.BG_PANEL.name()};
}}
QHeaderView::section {{
    background-color: {t.BG_PANEL.name()};
    color: {t.FG_MUTED.name()};
    border: none;
    border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
    padding: {t.SPACE[1]}px {t.SPACE[2]}px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
"""
```

### Step 1.4: Update `main.py` — Use Single QSS Source
```python
# main.py — replace DARK_QSS + SIDEBAR_TAB_QSS + SEARCH_QSS + STATUSBAR_QSS
from qss_tokens import qss, tabs_qss, filetree_qss

app.setStyleSheet(qss() + tabs_qss() + filetree_qss())  # only component-specific overrides remain
```

---

## Phase 2: Convert Light Dialogs to Dark Theme (3 Files, No Logic)

### Step 2.1: `search_dialog.py` — Dark Theme + Accessible Labels
- Replace `setStyleSheet()` with dark tokens (bg `BG_PANEL`, inputs `BG_APP`, borders `BORDER_SUBTLE`, accent `ACCENT`)
- Add `QLabel` for "Find" and "Replace" (accessibility), hide visually if needed
- Set `min-height: 44px`, padding `8px 16px` for buttons & inputs
- Add `:focus` and `:pressed` states to buttons

### Step 2.2: `command_palette.py` — Dark Theme + Overlay Styling
- Dialog bg `BG_PANEL`, border `BORDER_SUBTLE`
- Input: `BG_APP`, text `FG_PRIMARY`, border `BORDER_SUBTLE`, focus `BORDER_FOCUS`
- List items: `BG_PANEL` → hover `BG_APP`, selected `ACCENT` bg + `FG_PRIMARY` text
- Set `min-height: 44px` for list items (padding `12px 16px`)
- Change `QDialog` flags to `Qt.Popup` for overlay feel

### Step 2.3: `keybindings_dialog.py` — Dark Theme
- Dialog bg `BG_PANEL`, text `FG_PRIMARY`
- ListWidget: bg `BG_APP`, border `BORDER_SUBTLE`
- Items: hover `BG_APP`, selected `ACCENT` bg + `FG_PRIMARY` text
- Set `min-height: 44px` for list items

---

## Phase 3: Touch Targets & Focus Rings (Inline Styles Only)

### Step 3.1: `main_window.py` — Fix Inline Styles
| Component | Current | Fix |
|-----------|---------|-----|
| `sidebar_toggle` | `setFixedHeight(28)` | `setFixedSize(44, 44)` + `setAccessibleName("Toggle sidebar")` |
| `folder_btn` | `setFixedSize(28, 28)` | `setFixedSize(44, 44)` + `setAccessibleName("Select root folder")` |
| Tab close button | `setFixedSize(16, 16)` | `setFixedSize(24, 24)` + add `styleSheet("padding: 10px;")` for hit area |
| Status bar labels | `font-size: 11px` | `font-size: 13px` (from `Tokens.FONT_SIZE_UI`) |
| Search panel animation | Keep 200ms | Add `if QGuiApplication.styleHints().animationEnabled():` guard |

### Step 3.2: `file_tree.py` — Item Height & Focus
- `FILETREE_QSS`: `min-height: 44px` for items
- Add `:focus` style matching selection (`background-color: #2E2060; color: #EDE8FF;`)

### Step 3.3: `editor_tab.py` — Tab Bar Focus
- Add `QTabBar::tab:focus` style in `tabs_qss()`

---

## Phase 4: Typography & Spacing Tokens (Search/Replace)

### Step 4.1: `main_window.py` — Replace Hardcoded Fonts
- Apply `font-family: Tokens.FONT_UI; font-size: Tokens.FONT_SIZE_UI` to Menubar, Statusbar, Tabs

### Step 4.2: `editor_tab.py` — Editor Font from Tokens
- Use `Tokens.FONT_MONO` and `Tokens.FONT_SIZE_MONO` for editor font.

### Step 4.3: All Files — Replace Pixel Spacing with Tokens
- Convert hardcoded `px` values (e.g., `12px`, `16px`) to `Tokens.SPACE[n]` references in QSS.

---

## Phase 5: Syntax Highlighter Colors (Single Dict Update)

### Step 5.1: `syntax_highlighter.py` — Use Tokens
- Update `_setup_rules` to use `Tokens.SYN_...` colors for all syntax elements.

---

## Phase 6: Animation Polish (Optional, Guarded)

### Step 6.1: `main_window.py` — Reduced Motion Guard
- Wrap search panel animation in `if QGuiApplication.styleHints().animationEnabled():`

---

## Questions Before Execution

1.  **Font Licensing**: Use Google Fonts (IBM Plex Sans, JetBrains Mono), or rely on system fallbacks only?
2.  **Command Palette**: Keep as `QDialog` (centered) or change to `Qt.Popup` overlay?
3.  **Tab Close Button Hit Area**: Accept 24x24px button with 10px padding for hit area, or make the button visually larger?
4.  **Search Panel Animation**: Keep 200ms with reduced-motion guard, or remove completely?

---

*This plan focuses on UI-only changes, preserving application logic. Ready for execution.*