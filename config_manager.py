import json
import os
from pathlib import Path

class ConfigManager:
    CONFIG_DIR = Path.home() / ".config" / "niri-editor"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    KEYBINDINGS_FILE = CONFIG_DIR / "keybindings.json"
    SESSION_FILE = CONFIG_DIR / "session.json"
    CACHE_DIR = Path.home() / ".cache" / "niri-editor" / "unsaved"


    DEFAULT_CONFIG = {
        "theme": "nord",
        "font_family": "Consolas",
        "font_size": 12,
        "show_line_numbers": True,
        "auto_indent": True,
        "auto_close_brackets": True,
        "word_wrap": False,
        "tab_width": 4,
        "margin_column": 80,
        "encoding": "UTF-8",
        "line_ending": "LF",
        "zoom_level": 100,
        "recent_files": []
    }

    DEFAULT_KEYBINDINGS = {
        "new_file": "Ctrl+N",
        "open_file": "Ctrl+O",
        "save_file": "Ctrl+S",
        "save_as": "Ctrl+Shift+S",
        "close_tab": "Ctrl+W",
        "find": "Ctrl+F",
        "replace": "Ctrl+H",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "command_palette": "Ctrl+Shift+P",
        "goto_line": "Ctrl+G"
    }

    def __init__(self):
        self.config = {}
        self.keybindings = {}
        self._ensure_config_dir()
        self.load_config()
        self.load_keybindings()

    def _ensure_config_dir(self):
        if not self.CONFIG_DIR.exists():
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_keybindings(self):
        # Start with defaults
        self.keybindings = self.DEFAULT_KEYBINDINGS.copy()
        
        if self.KEYBINDINGS_FILE.exists():
            try:
                with open(self.KEYBINDINGS_FILE, 'r') as f:
                    user_bindings = json.load(f)
                    # Merge user bindings into defaults
                    self.keybindings.update(user_bindings)
            except Exception as e:
                print(f"Error loading keybindings: {e}")

        else:
            self.keybindings = self.DEFAULT_KEYBINDINGS.copy()
            self.save_keybindings()

    def save_keybindings(self):
        try:
            with open(self.KEYBINDINGS_FILE, 'w') as f:
                json.dump(self.keybindings, f, indent=4)
        except Exception as e:
            print(f"Error saving keybindings: {e}")

    def load_session(self):
        if self.SESSION_FILE.exists():
            try:
                with open(self.SESSION_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading session: {e}")
        return None

    def save_session(self, session_data):
        try:
            self._ensure_config_dir()
            with open(self.SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print(f"Error saving session: {e}")

    def get_cache_dir(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return self.CACHE_DIR

    def get(self, key, default=None):

        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_binding(self, action):
        return self.keybindings.get(action)

    def add_recent_file(self, path):
        resolved = str(Path(path).resolve())
        recent = self.config.get("recent_files", [])
        if resolved in recent:
            recent.remove(resolved)
        recent.insert(0, resolved)
        self.config["recent_files"] = recent[:10]
        self.save_config()

    def get_recent_files(self):
        return self.config.get("recent_files", [])

    def clear_recent_files(self):
        self.config["recent_files"] = []
        self.save_config()
