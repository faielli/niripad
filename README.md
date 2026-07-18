# Niripad

A lightweight, keyboard-driven text editor built with **PyQt6**, designed for the [Niri](https://github.com/YaLTeR/niri) Wayland scrollable-tiling compositor on Arch Linux.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52?style=flat&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/license-GPL%20v3-blue?style=flat)
![Platform](https://img.shields.io/badge/platform-Linux%20%2F%20Wayland-FCC624?style=flat&logo=linux&logoColor=black)

---

## Overview

Niripad is a custom text editor tailored for a minimal Wayland desktop workflow. It prioritizes keyboard efficiency, a clean Catppuccin Mocha aesthetic, and tight integration with the Niri compositor environment — without depending on KDE or any heavy desktop framework.

---

## Features

- **Syntax highlighting** for common languages
- **Multi-tab editing** with session restore and autosave
- **Collapsible file tree** sidebar with lazy-loaded folder hierarchy
- **Command palette** for quick action dispatch
- **Search & Replace** with regex support
- **Auto-indentation**, auto-closing brackets
- **Go To Line** (`Ctrl+G`), undo/redo stack
- **Catppuccin Mocha** color palette, JetBrains Mono font
- Designed for **Niri / Wayland** — no KDE dependencies

---

## Requirements

- Arch Linux (or any Linux distro with Wayland)
- `python`
- `python-pyqt6`
- `python-qtawesome`

---

## Installation

### Arch Linux (via PKGBUILD)

```bash
git clone https://github.com/faielli/niripad.git
cd niripad
chmod +x install.sh
./install.sh
```

Lo script crea automaticamente il pacchetto e lo installa tramite `pacman`.

### Avvio

Dal launcher delle applicazioni cerca **Niripad**, oppure da terminale:

```bash
niripad
```

### Disinstallazione

```bash
sudo pacman -R niripad
```

### Aggiornamento

```bash
cd niripad
git pull
./install.sh
```

---

## Project Structure

```
niripad/
├── main.py                  # Entry point
├── main_window.py           # Main window and layout
├── editor_tab.py            # Core editor widget
├── file_tree.py             # Sidebar file tree
├── syntax_highlighter.py    # Syntax highlighting engine
├── theme.py                 # Theme definitions
├── theme_tokens.py          # Design tokens (colors, fonts)
├── qss_tokens.py            # Qt stylesheet generator
├── command_palette.py       # Command palette overlay
├── search_dialog.py         # Search & replace panel
├── keybindings_dialog.py    # Keybindings configuration
├── config_manager.py        # Settings and session manager
├── logging_config.py        # Logging setup
├── icon_utils.py            # Icon helpers (qtawesome)
├── PKGBUILD                 # Arch Linux package build
├── install.sh               # Automated install script
└── niripad.desktop          # Desktop entry
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI Framework | PyQt6 |
| Language | Python 3.11+ |
| Theme | Lilac |
| Font | JetBrains Mono |
| Icons | qtawesome |
| Compositor | Niri (Wayland) |
| Platform | Arch Linux |

---

## License

GPL v3 — see [LICENSE](LICENSE) for details.
