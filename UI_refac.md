# NIRI EDITOR — UI REFACTOR PROMPT
> Ready-to-paste prompt for OpenCode (MiniMax M2.5 Plan + Gemma 4 31B Build)

---

## OBJECTIVE

Perform a full visual UI refactor of Niri Editor across all existing Python modules.
The goal is a **modern, minimal, functional dark editor UI** with a **soft lilac accent palette**,
rounded borders, smooth gradients, modern icon integration via `qtawesome`, and clean spatial hierarchy.
Do NOT change application logic, file structure, or keybindings — **only touch visual/QSS/style code**.

---

## DESIGN SYSTEM

### Color Palette — "Soft Dark Lilac"

Define these as Python constants in a dedicated `theme.py` (or `colors.py`) file
and import them everywhere instead of hardcoding hex values:

```python
# theme.py
BG_BASE       = "#1E1E2E"   # Main window background (deep cool dark)
BG_SURFACE    = "#252535"   # Cards, panels, sidebar
BG_ELEVATED   = "#2D2D42"   # Tab bar, toolbar, menus
BG_OVERLAY    = "#32324A"   # Hover states, dropdowns, tooltips

ACCENT_PRIMARY   = "#A78BFA"  # Lilac primary (violet-400)
ACCENT_SECONDARY = "#C4B5FD"  # Lighter lilac for hover/focus (violet-300)
ACCENT_DIM       = "#6D5FA6"  # Dimmed accent for inactive elements

TEXT_PRIMARY   = "#E2E0F0"   # Main readable text
TEXT_SECONDARY = "#9B99B8"   # Muted labels, metadata, line numbers
TEXT_DISABLED  = "#5A5870"   # Disabled / placeholder text

BORDER_SUBTLE  = "#3A3A55"   # Dividers, panel borders
BORDER_ACCENT  = "#A78BFA"   # Focused/active border highlight

SUCCESS = "#A3E4C7"   # Subtle green for saved/ok feedback
WARNING = "#F9C97C"   # Amber for warnings
ERROR   = "#F28BAB"   # Soft red for errors

RADIUS_SM = "4px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
```

### Typography
- Font: **JetBrains Mono** (already in use) — keep for editor area
- UI labels, menus, status bar: use system font stack or **Inter** if available via QFontDatabase
- Font scale: 11px (status/meta) → 12px (sidebar labels) → 13px (menus, tabs) → 14px (editor default)

### Spacing Rhythm
- Base unit: **4px**. All padding/margin in multiples: 4, 8, 12, 16, 24, 32
- Sidebar width open: **220px**, closed strip: **22px**
- Tab height: **34px**
- Menu bar height: **28px**
- Status bar height: **24px**
- Toolbar (if present): **36px**

---

## ICON SYSTEM — qtawesome

Use `qtawesome` (`qta`) throughout. Install guard at top of relevant file:

```python
try:
    import qtawesome as qta
    QTA_AVAILABLE = True
except ImportError:
    QTA_AVAILABLE = False
```

### Icon Mapping (use these exact names)

| Element              | qtawesome icon              | Size  |
|---------------------|-----------------------------|-------|
| New File             | `fa5s.file-alt`             | 14px  |
| Open File            | `fa5s.folder-open`          | 14px  |
| Save                 | `fa5s.save`                 | 14px  |
| Save All             | `fa5s.copy`                 | 14px  |
| Undo                 | `fa5s.undo`                 | 14px  |
| Redo                 | `fa5s.redo`                 | 14px  |
| Search               | `fa5s.search`               | 13px  |
| Replace              | `fa5s.exchange-alt`         | 13px  |
| Close Tab            | `fa5s.times`                | 10px  |
| Toggle Sidebar       | `fa5s.bars`                 | 13px  |
| File Tree / Explorer | `fa5s.sitemap`              | 13px  |
| Collapse Folder      | `fa5s.chevron-right`        | 10px  |
| Expand Folder        | `fa5s.chevron-down`         | 10px  |
| File (generic)       | `fa5s.file`                 | 12px  |
| Python file          | `fa5s.file-code`            | 12px  |
| Settings             | `fa5s.cog`                  | 13px  |
| Command Palette      | `fa5s.terminal`             | 13px  |
| Go To Line           | `fa5s.crosshairs`           | 13px  |
| Code Fold (collapse) | `fa5s.compress-alt`         | 11px  |
| Status OK            | `fa5s.check-circle`         | 11px  |
| Status Error         | `fa5s.exclamation-circle`   | 11px  |

Always tint icons to `TEXT_SECONDARY` by default; tint to `ACCENT_PRIMARY` on hover/active:

```python
icon = qta.icon('fa5s.save', color='#9B99B8')
# on hover/active:
icon_active = qta.icon('fa5s.save', color='#A78BFA')
```

---

## COMPONENT-BY-COMPONENT SPECS

### 1. MENU BAR (`QMenuBar` + `QMenu`)

```css
QMenuBar {
    background-color: #252535;
    color: #E2E0F0;
    font-size: 13px;
    padding: 2px 4px;
    border-bottom: 1px solid #3A3A55;
    spacing: 0px;
}
QMenuBar::item {
    padding: 4px 12px;
    border-radius: 6px;
    background: transparent;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background-color: #3A3A55;
    color: #C4B5FD;
}
QMenu {
    background-color: #2D2D42;
    border: 1px solid #3A3A55;
    border-radius: 8px;
    padding: 4px;
    color: #E2E0F0;
    font-size: 13px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 6px;
    background: transparent;
}
QMenu::item:selected {
    background-color: #3D3D5A;
    color: #C4B5FD;
}
QMenu::separator {
    height: 1px;
    background: #3A3A55;
    margin: 4px 8px;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
}
```

**Menu structure** — ensure menus are organized as:
- **File**: New, Open, Save, Save As, Save All, — , Recent Files, — , Exit
- **Edit**: Undo, Redo, — , Cut, Copy, Paste, — , Find, Replace, Go To Line
- **View**: Toggle Sidebar, Command Palette, — , Zoom In, Zoom Out, Reset Zoom
- **Help**: About, Keyboard Shortcuts

Add `qtawesome` icons to every menu action using `action.setIcon(qta.icon(...))`.

---

### 2. TAB BAR (`QTabWidget` + `QTabBar`)

```css
QTabWidget::pane {
    border: none;
    background: #1E1E2E;
}
QTabWidget::tab-bar {
    alignment: left;
}
QTabBar {
    background: #252535;
    border-bottom: 1px solid #3A3A55;
}
QTabBar::tab {
    background: transparent;
    color: #9B99B8;
    font-size: 13px;
    padding: 0px 14px;
    height: 34px;
    min-width: 100px;
    max-width: 200px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}
QTabBar::tab:hover {
    background: #2D2D42;
    color: #E2E0F0;
}
QTabBar::tab:selected {
    background: #1E1E2E;
    color: #C4B5FD;
    border-bottom: 2px solid #A78BFA;
    font-weight: 500;
}
QTabBar::tab:!selected {
    margin-top: 2px;
}
QTabBar::close-button {
    image: none;
    subcontrol-position: right;
    padding: 2px;
}
```

**Close button**: render via qtawesome `fa5s.times` at 10px, color `#5A5870`, hover color `#F28BAB`.
Use explicit index capture lambda (avoid closure bug):

```python
def make_close_handler(idx):
    return lambda: self.close_tab(idx)
```

**Unsaved indicator**: prefix tab title with `●` in `ACCENT_PRIMARY` color when file is modified.

---

### 3. SIDEBAR (File Tree)

Sidebar container:

```css
QWidget#sidebar {
    background-color: #252535;
    border-right: 1px solid #3A3A55;
}
```

File tree (`QTreeWidget`):

```css
QTreeWidget {
    background: #252535;
    border: none;
    color: #E2E0F0;
    font-size: 12px;
    outline: none;
    padding: 4px 0;
}
QTreeWidget::item {
    padding: 4px 8px;
    border-radius: 6px;
    min-height: 24px;
}
QTreeWidget::item:hover {
    background: #2D2D42;
}
QTreeWidget::item:selected {
    background: #3D3A5E;
    color: #C4B5FD;
}
QTreeWidget::branch {
    background: transparent;
}
QTreeWidget::branch:has-children:closed {
    image: none; /* replaced by qtawesome chevron-right */
}
QTreeWidget::branch:has-children:open {
    image: none; /* replaced by qtawesome chevron-down */
}
```

Sidebar toggle strip (when closed):

```css
QWidget#sidebar_strip {
    background: #252535;
    border-right: 1px solid #3A3A55;
    min-width: 22px;
    max-width: 22px;
}
QPushButton#sidebar_toggle {
    background: transparent;
    border: none;
    color: #9B99B8;
    font-size: 11px;
    padding: 0;
}
QPushButton#sidebar_toggle:hover {
    color: #A78BFA;
}
```

File icons in tree: use `qta.icon('fa5s.file-code', color='#9B99B8')` for `.py`, `fa5s.file` for others,
`fa5s.folder` / `fa5s.folder-open` for directories.

---

### 4. EDITOR AREA (`QPlainTextEdit` or `QTextEdit`)

```css
QPlainTextEdit, QTextEdit {
    background-color: #1E1E2E;
    color: #E2E0F0;
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
    line-height: 1.6;
    border: none;
    selection-background-color: #4A3F7A;
    selection-color: #E2E0F0;
    padding: 8px 0;
    caret-color: #A78BFA;
}
```

Line number gutter:

```css
/* LineNumberArea widget */
background-color: #1E1E2E;
color: #5A5870;          /* TEXT_DISABLED */
font-family: "JetBrains Mono", monospace;
font-size: 12px;
padding-right: 12px;
border-right: 1px solid #3A3A55;
```

Current line highlight: `QColor("#252535")` via `setExtraSelections()`.

---

### 5. STATUS BAR (`QStatusBar`)

```css
QStatusBar {
    background-color: #1A1A2E;
    color: #9B99B8;
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
    border-top: 1px solid #3A3A55;
    padding: 0 12px;
    min-height: 24px;
    max-height: 24px;
}
QStatusBar::item {
    border: none;
    padding: 0 8px;
}
QLabel#status_mode {
    color: #A78BFA;
    font-weight: 600;
    padding-right: 12px;
}
```

Status bar sections (left → right):
`[mode/language]  [cursor: Ln X, Col Y]  [encoding: UTF-8]  [indent: spaces/tabs]  [autosave status]`

---

### 6. SCROLLBARS

```css
QScrollBar:vertical {
    background: #1E1E2E;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3A3A55;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #A78BFA;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1E1E2E;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #3A3A55;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #A78BFA;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
```

---

### 7. COMMAND PALETTE (`QDialog`)

```css
QDialog#command_palette {
    background: #2D2D42;
    border: 1px solid #3A3A55;
    border-radius: 12px;
}
QLineEdit#palette_input {
    background: #1E1E2E;
    border: 1px solid #A78BFA;
    border-radius: 8px;
    color: #E2E0F0;
    font-size: 14px;
    padding: 10px 14px;
    selection-background-color: #4A3F7A;
}
QListWidget#palette_results {
    background: transparent;
    border: none;
    color: #E2E0F0;
    font-size: 13px;
    outline: none;
}
QListWidget#palette_results::item {
    padding: 8px 12px;
    border-radius: 6px;
}
QListWidget#palette_results::item:selected {
    background: #3D3A5E;
    color: #C4B5FD;
}
```

Flags: `Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup`
Add drop shadow via `QGraphicsDropShadowEffect`: blur=24, color=`#000000` at 60% opacity, offset=(0,8).

---

### 8. SEARCH & REPLACE BAR

```css
QWidget#search_bar {
    background: #252535;
    border-bottom: 1px solid #3A3A55;
    padding: 6px 12px;
}
QLineEdit#search_input, QLineEdit#replace_input {
    background: #1E1E2E;
    border: 1px solid #3A3A55;
    border-radius: 6px;
    color: #E2E0F0;
    font-size: 13px;
    padding: 5px 10px;
    min-width: 200px;
}
QLineEdit#search_input:focus, QLineEdit#replace_input:focus {
    border-color: #A78BFA;
}
QPushButton#search_btn {
    background: #3D3A5E;
    color: #C4B5FD;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
}
QPushButton#search_btn:hover {
    background: #A78BFA;
    color: #1E1E2E;
}
```

---

### 9. SPLITTER

```css
QSplitter::handle {
    background: #3A3A55;
    width: 1px;
}
QSplitter::handle:hover {
    background: #A78BFA;
}
```

---

## GLOBAL APPLICATION STYLESHEET

Apply a single `app.setStyleSheet(GLOBAL_QSS)` in `main.py` or the main window `__init__`.
Build `GLOBAL_QSS` by concatenating all the per-component QSS strings above.

**CRITICAL**: after `app.setStyleSheet(GLOBAL_QSS)`, do **NOT** call `widget.setStyleSheet(...)` on
individual widgets unless using a more specific selector (e.g. `QTabBar#editor_tabs`), or the global
QSS will be overridden and accent colors will break.

---

## IMPLEMENTATION CHECKLIST

Before committing, verify:

- [ ] `theme.py` exists with all color constants; no raw hex values elsewhere
- [ ] `qtawesome` icons applied to: all menu actions, sidebar toggle, close tab button, file tree items
- [ ] All `border-radius` values use `RADIUS_MD` (8px) for panels, `RADIUS_SM` (4px) for inputs/buttons
- [ ] Tab close button uses explicit index capture (no closure bug)
- [ ] Line number rendering uses `blockBoundingGeometry()` not `cursorRect()`
- [ ] Command palette uses `FramelessWindowHint` + drop shadow
- [ ] Status bar shows: language, cursor position, encoding, indent mode
- [ ] Scrollbars are thin (8px), rounded, lilac on hover
- [ ] Global QSS applied once in main window; no conflicting inline `setStyleSheet` calls on same widgets
- [ ] Sidebar strip shows `fa5s.bars` icon at 13px when collapsed

---

## CONSTRAINTS

- **Do NOT** modify any application logic, file parsing, keybindings, or shortcut definitions
- **Do NOT** change module names or file structure
- **Do NOT** add new dependencies beyond `qtawesome` (already in scope)
- **Do NOT** use `Qt.WindowFlags` deprecated forms — use `Qt.WindowType.FramelessWindowHint`
- Use `QApplication.instance().setStyleSheet(...)` if `app` reference is not directly available in the window init

---

## GIT COMMIT (after agent completes)

```bash
git add -A
git commit -m "refactor: full UI overhaul — soft dark lilac theme, qtawesome icons, rounded components"
```
