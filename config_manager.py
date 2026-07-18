import copy
import json
import os
import tempfile
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class ConfigManager(QObject):
    CONFIG_DIR = Path.home() / ".config" / "niripad"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    KEYBINDINGS_FILE = CONFIG_DIR / "keybindings.json"
    SESSION_FILE = CONFIG_DIR / "session.json"
    CACHE_DIR = Path.home() / ".cache" / "niripad" / "unsaved"


    DEFAULT_CONFIG = {
        "theme": "lilac",
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

    bindings_changed = pyqtSignal(dict)

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
        super().__init__()
        self.config = {}
        self.keybindings = {}
        self._ensure_config_dir()
        self.load_config()
        self.load_keybindings()

    def _ensure_config_dir(self):
        if not self.CONFIG_DIR.exists():
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _atomic_write_json(self, target, data):
        self._ensure_config_dir()
        fd, tmp_path = tempfile.mkstemp(dir=self.CONFIG_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

    def load_config(self):
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error("Error loading config: %s", e)
                backup = self.CONFIG_FILE.with_suffix(".json.bad")
                try:
                    self.CONFIG_FILE.rename(backup)
                    logger.warning("Backed up corrupt config to %s", backup)
                except Exception:
                    pass
                self.config = {}
        else:
            self.config = {}

        merged = copy.deepcopy(self.DEFAULT_CONFIG)
        if isinstance(self.config, dict):
            merged.update({k: v for k, v in self.config.items() if k in merged})
        self.config = merged

        self._validate_config()

    def _validate_config(self):
        if not isinstance(self.config.get("tab_width"), int) or self.config["tab_width"] < 1 or self.config["tab_width"] > 16:
            self.config["tab_width"] = self.DEFAULT_CONFIG["tab_width"]
        if not isinstance(self.config.get("font_size"), int) or self.config["font_size"] < 6 or self.config["font_size"] > 72:
            self.config["font_size"] = self.DEFAULT_CONFIG["font_size"]
        if not isinstance(self.config.get("margin_column"), int) or self.config["margin_column"] < 20 or self.config["margin_column"] > 200:
            self.config["margin_column"] = self.DEFAULT_CONFIG["margin_column"]
        if not isinstance(self.config.get("zoom_level"), int) or self.config["zoom_level"] < 50 or self.config["zoom_level"] > 200:
            self.config["zoom_level"] = self.DEFAULT_CONFIG["zoom_level"]

    def save_config(self):
        try:
            self._atomic_write_json(str(self.CONFIG_FILE), self.config)
        except Exception as e:
            logger.error("Error saving config: %s", e)

    def load_keybindings(self):
        self.keybindings = copy.deepcopy(self.DEFAULT_KEYBINDINGS)
        
        if self.KEYBINDINGS_FILE.exists():
            try:
                with open(self.KEYBINDINGS_FILE, 'r', encoding='utf-8') as f:
                    user_bindings = json.load(f)
                    # Merge user bindings into defaults
                    self.keybindings.update(user_bindings)
            except Exception as e:
                logger.error("Error loading keybindings: %s", e)

        else:
            self.save_keybindings()

    def save_keybindings(self):
        seen = {}
        for action, shortcut in self.keybindings.items():
            if shortcut in seen:
                logger.warning("Duplicate shortcut %r for %r and %r", shortcut, action, seen[shortcut])
            seen[shortcut] = action
        try:
            self._atomic_write_json(str(self.KEYBINDINGS_FILE), self.keybindings)
        except Exception as e:
            logger.error("Error saving keybindings: %s", e)
        self.bindings_changed.emit(self.keybindings)

    def load_session(self):
        if self.SESSION_FILE.exists():
            try:
                with open(self.SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error("Error loading session: %s", e)
                backup = self.SESSION_FILE.with_suffix(".session.bad")
                try:
                    self.SESSION_FILE.rename(backup)
                    logger.warning("Backed up corrupt session to %s", backup)
                except Exception:
                    pass
        return {}

    def save_session(self, session_data):
        try:
            self._atomic_write_json(str(self.SESSION_FILE), session_data)
        except Exception as e:
            logger.error("Error saving session: %s", e)

    def get_cache_dir(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return self.CACHE_DIR

    def get(self, key, default=None):
        val = self.config.get(key)
        if val is not None:
            return val
        if key in self.DEFAULT_CONFIG:
            return self.DEFAULT_CONFIG[key]
        return default

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_binding(self, action):
        return self.keybindings.get(action)

    def add_recent_file(self, path):
        try:
            resolved = str(Path(path).resolve(strict=False))
        except Exception:
            return
        recent = self.config.get("recent_files")
        if not isinstance(recent, list):
            recent = []
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
