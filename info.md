# NiriPad — Feature Overview

Modern, lightweight code editor built with PyQt6. Catppuccin-inspired theming, dual-pane editing, and developer-focused UX.

---

## Editor Core

| Feature | Details |
|---------|---------|
| **Multi-tab editing** | Unlimited tabs, drag-to-reorder, close with `Ctrl+W` |
| **Split view** | Horizontal split (left/right panes), independent tab strips |
| **Syntax highlighting** | 12+ languages via `UniversalHighlighter` (Python, JS/TS, Rust, C++, SQL, JSON, YAML, TOML, Markdown, HTML, CSS, Bash) |
| **Code folding** | Regex-based folding per language (`def`, `class`, `if`, `for`, `function`, etc.) |
| **Line numbers** | Gutter with current-line highlight |
| **Bracket matching** | Real-time pair highlighting |
| **Margin guide** | Configurable column marker (default 80) |
| **Whitespace toggle** | Show/hide spaces/tabs |
| **Zoom** | `Ctrl++` / `Ctrl+-` / `Ctrl+0` (100%) |
| **Encoding / Line endings** | Status bar cycling: UTF-8/UTF-16/Latin-1/CP1252 · LF/CRLF/CR |
| **Tab width** | Cycle 2 / 4 / 8 spaces |

---

## File Management

| Feature | Details |
|---------|---------|
| **File tree** | Lazy-loaded sidebar, `..` parent navigation, context menu (New File/Folder, Rename, Delete) |
| **Drag & drop** | Reorder tabs, move between panes |
| **Recent files** | Persisted in config (max 10) |
| **Session restore** | Reopens tabs, split state, cursor positions on startup |
| **Auto-save** | Periodic + on close (configurable) |
| **Unsaved cache** | Unsaved buffers cached to `~/.cache/niripad/unsaved/` |

---

## Search & Navigation

| Feature | Details |
|---------|---------|
| **Search panel** | `Ctrl+F` — find, case-sensitive, regex, match count |
| **Replace** | Single / replace all |
| **Go to line** | `Ctrl+G` — inline panel |
| **Command palette** | `Ctrl+Shift+P` — fuzzy-search actions (save, split, theme, keybindings, etc.) |
| **File open** | `Ctrl+O` — native dialog (non-native on Linux) |

---

## Git Integration

| Feature | Details |
|---------|---------|
| **Branch display** | Status bar shows current branch (background worker, non-blocking) |
| **Auto-refresh** | On tab change / focus |
| **Graceful fallback** | Empty string if not a git repo or git unavailable |

---

## Theming & Appearance

| Theme | Palette |
|-------|---------|
| **Lilac** (default) | Catppuccin Mocha base — soft purples, dark bg |
| **Nord** | Classic Nord (blues/greys) |
| **Light** | Clean light theme |

- **Design tokens** (`theme_tokens.py`): colors, spacing, radii, fonts, shadows — single source of truth
- **QSS generation** (`qss_tokens.py`): tokens → stylesheet at runtime
- **Per-tab theme** — each editor tab can have its own theme

---

## Configuration

Stored in `~/.config/niripad/` (atomic JSON writes, UTF-8 safe):

| File | Contents |
|------|----------|
| `config.json` | Theme, font, tab width, margin, encoding, line ending, zoom, recent files |
| `keybindings.json` | User-customizable shortcuts (merged with defaults) |
| `session.json` | Open tabs, split state, cursor positions |

**Defaults** cover all common editor settings; validation on load prevents corrupt values.

---

## Keybindings (Defaults)

| Action | Shortcut |
|--------|----------|
| New file | `Ctrl+N` |
| Open file | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save as | `Ctrl+Shift+S` |
| Close tab | `Ctrl+W` |
| Find | `Ctrl+F` |
| Replace | `Ctrl+H` |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Y` |
| Command palette | `Ctrl+Shift+P` |
| Go to line | `Ctrl+G` |
| Split editor | Action in command palette |
| Theme cycle | Action in command palette |
| Zoom in/out/reset | `Ctrl++` / `Ctrl+-` / `Ctrl+0` |

*All customizable via **Keybindings** dialog.*

---

## Developer Features

| Feature | Details |
|---------|---------|
| **Logging** | Structured stderr + file (`test_report.txt`) |
| **Test suite** | 38+ tests (`python test.py`) — unit + Qt integration (offscreen) |
| **Type hints** | Full annotations across codebase |
| **Atomic config writes** | Temp file + `os.replace` — no corruption on crash |
| **UTF-8 roundtrip** | Tested for config/session with accents, CJK |

---

## Architecture

```
main.py
  └─ MainWindow (main_window.py)
       ├─ FileTree (file_tree.py)          ← sidebar
       ├─ EditorTab × N (editor_tab.py)    ← tabs (left/right)
       │    └─ CustomEditor                ← QPlainTextEdit subclass
       │         ├─ UniversalHighlighter   ← syntax (syntax_highlighter.py)
       │         ├─ LineNumberArea
       │         ├─ CodeFoldingArea
       │         └─ MarginLine
       ├─ SearchPanel / GoToLinePanel (search_dialog.py)
       ├─ CommandPalette (command_palette.py)
       ├─ KeybindingsDialog (keybindings_dialog.py)
       ├─ GitBranchWorker (QThread)
       └─ ConfigManager (config_manager.py)  ← singleton-ish QObject
```

---

## Requirements

```
PyQt6 >= 6.6
qtawesome >= 1.2  (optional — graceful fallback)
Python 3.10+
```

---

## Run

```bash
python main.py
```

## Test

```bash
python test.py          # full suite
```

---

## Known Issues

- `_is_path_safe()` does not block directory traversal (`../../etc/passwd` returns `True`) — marked `@expectedFailure` in tests
- Git worker does not auto-refresh on branch change (only on tab focus)
- No LSP / autocomplete (intentionally minimal)
