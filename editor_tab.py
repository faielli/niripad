from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal

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

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())
            self.file_path = file_path
            self._is_modified = False
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
