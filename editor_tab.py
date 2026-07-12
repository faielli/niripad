import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from syntax_highlighter import UniversalHighlighter
from theme import Theme

def detect_language(file_path, content=""):
    if not file_path:
        return None
    
    # Detection by extension
    ext_map = {
        ".py": "python",
        ".sh": "bash",
        ".bash": "bash",
        ".c": "cpp",
        ".cpp": "cpp",
        ".h": "cpp",
        ".hpp": "cpp",
        ".js": "javascript",
        ".ts": "javascript",
        ".jsx": "javascript",
        ".tsx": "javascript",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".markdown": "markdown",
        ".sql": "sql",
        ".rs": "rust",
    }
    
    _, ext = os.path.splitext(file_path)
    lang = ext_map.get(ext.lower())
    
    # Detection by shebang if extension is ambiguous or missing
    if not lang and content.startswith("#!"):
        first_line = content.splitlines()[0] if content else ""
        if "python" in first_line:
            return "python"
        if "bash" in first_line or "sh" in first_line:
            return "bash"
            
    return lang

class EditorTab(QWidget):
    modified_changed = pyqtSignal(bool)

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self._is_modified = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QPlainTextEdit()
        self.editor.textChanged.connect(self.on_text_changed)
        self.layout.addWidget(self.editor)

        # Setup theme and highlighter
        self.current_theme = Theme.NORD
        self.apply_theme()
        
        self.highlighter = UniversalHighlighter(self.editor.document(), self.current_theme)
        
        if file_path:
            self.load_file(file_path)

    def apply_theme(self):
        bg_color = Theme.get_color(self.current_theme, "background")
        fg_color = Theme.get_color(self.current_theme, "foreground")
        
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg_color.name()};
                color: {fg_color.name()};
                border: none;
                font-family: 'Consolas', 'Monospace', 'Courier New';
                font-size: 12pt;
            }}
        """)

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.file_path = file_path
            self._is_modified = False
            
            # Detect language and update highlighter
            lang = detect_language(file_path, content)
            print(f"[DEBUG] Detected language: {lang}")
            if lang:
                self.highlighter.set_language(lang)
                self.highlighter.rehighlight()
                
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")

    def save_file(self, file_path=None):
        if file_path:
            self.file_path = file_path
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self._is_modified = False
            self.modified_changed.emit(self._is_modified)
            return True
        except Exception as e:
            print(f"Error saving file {self.file_path}: {e}")
            return False

    def on_text_changed(self):
        if not self._is_modified:
            self._is_modified = True
            self.modified_changed.emit(self._is_modified)

    def is_modified(self):
        return self._is_modified

    def get_title(self):
        name = self.file_path if self.file_path else "Untitled"
        if self._is_modified:
            return f"*{name}"
        return name
