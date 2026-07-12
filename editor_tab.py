import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize, QPoint
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFontMetrics
from syntax_highlighter import UniversalHighlighter
from theme import Theme

def detect_language(file_path, content=""):
    if not file_path:
        return None
    
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
    
    if not lang and content.startswith("#!"):
        first_line = content.splitlines()[0] if content else ""
        if "python" in first_line:
            return "python"
        if "bash" in first_line or "sh" in first_line:
            return "bash"
            
    return lang

class CodeFoldingArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(20, 0)

    def mousePressEvent(self, event):
        cursor = self.editor.cursorForPosition(event.position().toPoint())
        block = cursor.block()
        if block.isValid():
            self.editor.toggle_fold(block.blockNumber())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.palette().window())
        
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(0, -self.editor.verticalScrollBar().value()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                fold_end = self.editor.foldable_blocks.get(block_number)
                if fold_end is not None:
                    is_folded = block_number in self.editor.folded_blocks
                    painter.setPen(self.palette().color(self.palette().ColorRole.Text))
                    if is_folded:
                        # Triangle pointing right (folded)
                        painter.drawPolygon([QPoint(5, top + 4), QPoint(5, top + 12), QPoint(12, top + 8)])
                    else:
                        # Triangle pointing down (unfolded)
                        painter.drawPolygon([QPoint(5, top + 6), QPoint(12, top + 6), QPoint(8, top + 12)])

            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CustomEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)
        self.foldingArea = CodeFoldingArea(self)
        self.foldable_blocks = {} # start_block: end_block
        self.folded_blocks = set() # set of start_blocks
        
        self.textChanged.connect(self.update_foldable_blocks)
        self.update_sidebar_width()
        self.update_foldable_blocks()

    def line_number_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        
        font = self.font()
        metrics = QFontMetrics(font)
        space = 5 # pixels for padding and separator
        
        return metrics.horizontalAdvance('9') * digits + space

    def folding_area_width(self):
        return 20 if self.foldable_blocks else 14

    def update_sidebar_width(self):
        width = self.line_number_width() + self.folding_area_width()
        self.setViewportMargins(width, 0, 0, 0)
        self.update_sidebar_area()

    def update_sidebar_area(self):
        ln_width = self.line_number_width()
        fold_width = self.folding_area_width()
        
        self.lineNumberArea.setGeometry(QRect(0, 0, ln_width, self.height()))
        self.foldingArea.setGeometry(QRect(ln_width, 0, fold_width, self.height()))

    def update_foldable_blocks(self):
        self.foldable_blocks = {}
        self.folded_blocks = set()
        
        # Scan for foldable blocks
        block = self.document().begin()
        while block.isValid():
            text = block.text()
            stripped = text.strip()
            
            # Python-style blocks
            is_python_fold = any(stripped.startswith(k) and stripped.endswith(':') for k in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except ', 'with '])
            # C-style blocks
            is_c_style_fold = stripped.endswith('{') and any(stripped.startswith(k) for k in ['if ', 'for ', 'while ', 'switch ', 'void ', 'int ', 'float ', 'char ', 'class ', 'struct '])
            
            if is_python_fold or is_c_style_fold:
                start_block = block.blockNumber()
                start_indent = len(text) - len(text.lstrip())
                
                next_block = block.next()
                last_block = start_block
                while next_block.isValid():
                    next_text = next_block.text()
                    if next_text.strip():
                        next_indent = len(next_text) - len(next_text.lstrip())
                        if next_indent <= start_indent:
                            break
                    last_block = next_block.blockNumber()
                    next_block = next_block.next()
                
                if last_block > start_block:
                    self.foldable_blocks[start_block] = last_block
            
            block = block.next()
        
        self.update_sidebar_width()
        self.update_sidebar_area()

    def toggle_fold(self, block_number):
        if block_number in self.foldable_blocks:
            if block_number in self.folded_blocks:
                # Unfold
                self.folded_blocks.remove(block_number)
                start = block_number + 1
                end = self.foldable_blocks[block_number]
                for i in range(start, end + 1):
                    block = self.document().findBlockByNumber(i)
                    if block.isValid():
                        block.setVisible(True)
            else:
                # Fold
                self.folded_blocks.add(block_number)
                start = block_number + 1
                end = self.foldable_blocks[block_number]
                for i in range(start, end + 1):
                    block = self.document().findBlockByNumber(i)
                    if block.isValid():
                        block.setVisible(False)
            
            self.update_sidebar_area() # Refresh triangles
            self.viewport().update()

    def keyPressEvent(self, event):
        # Auto-closure map
        pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '"': '"',
            "'": "'"
        }
        
        key = event.text()
        if key in pairs:
            # Insert opening and closing bracket
            self.insertPlainText(key)
            self.insertPlainText(pairs[key])
            # Move cursor back one position
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            self.update_sidebar_width()
            self.lineNumberArea.update()
            return

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Auto-indentation
            cursor = self.textCursor()
            line = cursor.block().text()
            
            # Find indentation of current line
            indent = ""
            for char in line:
                if char == ' ' or char == '\t':
                    indent += char
                else:
                    break
            
            # Extra indent if line ends with colon (e.g. Python)
            if line.strip().endswith(':'):
                indent += "    "
            
            # Insert newline and indentation
            self.insertPlainText('\n' + indent)
            self.update_sidebar_width()
            self.lineNumberArea.update()
            return

        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_sidebar_area()

    def updateRequest(self, rect, dy):
        super().updateRequest(rect, dy)
        sidebar_width = self.line_number_width() + self.folding_area_width()
        if rect.contains(QRect(0, 0, sidebar_width, self.height())):
            self.lineNumberArea.update()
            self.foldingArea.update()

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), self.palette().window())
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(0, -self.verticalScrollBar().value()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self.palette().color(self.palette().ColorRole.Text))
                painter.drawText(0, top, self.lineNumberArea.width() - 2, 
                                  self.fontMetrics().height(),
                                  Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
            
        # Draw vertical separator line on the right edge
        separator_x = self.lineNumberArea.width() - 1
        painter.setPen(QColor("#1e222a"))  # border color
        painter.drawLine(separator_x, 0, separator_x, self.height())

class EditorTab(QWidget):
    modified_changed = pyqtSignal(bool)

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self._is_modified = False
        self._language = None
        
        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.editor = CustomEditor()
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.blockCountChanged.connect(self.editor.update_sidebar_width)
        self.editor.update_sidebar_width()
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
        
        # Note: CustomEditor is a QPlainTextEdit, so we apply style to it
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
            self.editor.blockSignals(True)
            self.editor.setPlainText(content)
            self.editor.blockSignals(False)
            self.file_path = file_path
            self._is_modified = False
            
            lang = detect_language(file_path, content)
            print(f"[DEBUG] Detected language: {lang}")
            self._language = lang
            if lang:
                self.highlighter.set_language(lang)
                self.highlighter.rehighlight()
                
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")

    @property
    def language(self):
        return self._language

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
        if os.path.isfile(name):
            return os.path.basename(name)
        return name
