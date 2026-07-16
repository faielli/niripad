import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QTextEdit
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize, QPoint
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFontMetrics, QTextCursor, QFont, QTextOption
from syntax_highlighter import UniversalHighlighter
from theme import Theme
from theme_tokens import Tokens

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
        painter.fillRect(event.rect(), QColor("#1E1A2E"))
        
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(0, -self.editor.verticalScrollBar().value()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                fold_end = self.editor.foldable_blocks.get(block_number)
                if fold_end is not None:
                    is_folded = block_number in self.editor.folded_blocks
                    painter.setPen(QColor("#9B6DFF"))
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


class MarginLine(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(Tokens.MARGIN_LINE.name()))
        painter.end()

class CustomEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.language = None
        self.lineNumberArea = LineNumberArea(self)
        self.foldingArea = CodeFoldingArea(self)
        self.marginLine = MarginLine(self)
        self.foldable_blocks = {}
        self.folded_blocks = set()

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        font = QFont(Tokens.FONT_MONO.split(",")[0].strip("'"))
        font.setPointSize(Tokens.FONT_SIZE_MONO)
        self.setFont(font)

        self.textChanged.connect(self.update_foldable_blocks)
        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self._search_highlights = []
        self._bracket_highlights = []
        self._zoom_level = 100
        self._show_whitespace = False
        self._margin_column = 80
        self._show_margin = True

        self.update_sidebar_width()
        self.update_foldable_blocks()
        self.highlight_current_line()

    def _on_cursor_moved(self):
        self.highlight_current_line()
        self._update_bracket_match()

    def highlight_current_line(self):
        extra_selections = []
        
        selection = QTextEdit.ExtraSelection()
        line_color = QColor("#A885FF")
        line_color.setAlpha(120)
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        
        extra_selections.append(selection)
        extra_selections.extend(self._search_highlights)
        extra_selections.extend(self._bracket_highlights)
        self.setExtraSelections(extra_selections)

    def set_search_highlights(self, selections):
        self._search_highlights = selections
        self.highlight_current_line()

    def clear_search_highlights(self):
        self._search_highlights = []
        self.highlight_current_line()

    def _update_bracket_match(self):
        self._bracket_highlights = []
        cursor = self.textCursor()
        pos = cursor.position()
        doc = self.document()
        text = doc.toPlainText()
        if not text or pos < 0 or pos > len(text):
            self.highlight_current_line()
            return

        char = text[pos - 1] if pos > 0 else ''
        pairs = {'(': ')', '[': ']', '{': '}'}
        match = None

        if char in pairs:
            match = self._find_matching(text, pos - 1, pairs[char], 1)
        elif char in pairs.values():
            open_for = {v: k for k, v in pairs.items()}[char]
            match = self._find_matching(text, pos - 1, open_for, -1)
        elif pos < len(text):
            char = text[pos]
            if char in pairs:
                match = self._find_matching(text, pos, pairs[char], 1)
            elif char in pairs.values():
                open_for = {v: k for k, v in pairs.items()}[char]
                match = self._find_matching(text, pos, open_for, -1)

        if match is not None:
            sels = []
            for mpos in (pos - 1 if char in pairs or char in pairs.values() else pos, match):
                if 0 <= mpos < len(text):
                    sel = QTextEdit.ExtraSelection()
                    color = QColor(Tokens.BRACKET_MATCH.name())
                    color.setAlpha(80)
                    sel.format.setBackground(color)
                    sel.cursor = QTextCursor(doc)
                    sel.cursor.setPosition(mpos)
                    sel.cursor.setPosition(mpos + 1, QTextCursor.MoveMode.KeepAnchor)
                    sels.append(sel)
            self._bracket_highlights = sels

        self.highlight_current_line()

    def _find_matching(self, text, start, target, direction):
        depth = 0
        pos = start + direction
        open_char = text[start]
        close_char = target
        while 0 <= pos < len(text):
            if text[pos] == open_char:
                depth += 1
            elif text[pos] == close_char:
                if depth == 0:
                    return pos
                depth -= 1
            pos += direction
        return None

    def set_word_wrap(self, enabled):
        mode = QPlainTextEdit.LineWrapMode.WidgetWidth if enabled else QPlainTextEdit.LineWrapMode.NoWrap
        self.setLineWrapMode(mode)
        self.update_sidebar_width()

    def set_show_whitespace(self, enabled):
        self._show_whitespace = enabled
        opt = self.document().defaultTextOption()
        if enabled:
            opt.setFlags(opt.flags() | QTextOption.Flag.ShowTabsAndSpaces | QTextOption.Flag.ShowLineAndParagraphSeparators)
        else:
            opt.setFlags(opt.flags() & ~(QTextOption.Flag.ShowTabsAndSpaces | QTextOption.Flag.ShowLineAndParagraphSeparators))
        self.document().setDefaultTextOption(opt)
        self.viewport().update()

    def set_margin_column(self, column):
        self._margin_column = column
        self.update_sidebar_area()

    def set_show_margin(self, enabled):
        self._show_margin = enabled
        self.marginLine.setVisible(enabled)

    def set_zoom_level(self, level):
        self._zoom_level = max(50, min(200, level))
        font = self.font()
        base = Tokens.FONT_SIZE_MONO
        font.setPointSize(int(base * self._zoom_level / 100))
        self.setFont(font)
        self.update_sidebar_width()

    def zoom_in(self):
        self.set_zoom_level(self._zoom_level + 10)

    def zoom_out(self):
        self.set_zoom_level(self._zoom_level - 10)

    def reset_zoom(self):
        self.set_zoom_level(100)

    def go_to_line(self, line_number):
        # line_number is 1-indexed
        block = self.document().findBlockByNumber(line_number - 1)
        if block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self.setFocus(Qt.FocusReason.OtherFocusReason)
            self.highlight_current_line()

    def line_number_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        
        font = self.font()
        metrics = QFontMetrics(font)
        space = 12 # pixels for padding and separator
        
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

        if self._show_margin:
            metrics = QFontMetrics(self.font())
            margin_x = ln_width + fold_width + metrics.horizontalAdvance('9') * self._margin_column
            self.marginLine.setGeometry(QRect(margin_x, 0, 2, self.height()))
            self.marginLine.show()
        else:
            self.marginLine.hide()

    def update_foldable_blocks(self):
        self.foldable_blocks = {}
        self.folded_blocks = set()
        
        # Scan for foldable blocks
        block = self.document().begin()
        while block.isValid():
            text = block.text()
            stripped = text.strip()
            
            # Python-style blocks
            is_python_fold = stripped.endswith(':') and any(stripped.startswith(k) for k in ['def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with '])
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

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.highlight_current_line()

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
            
            # Smart indentation based on language
            stripped = line.strip()
            if stripped:
                if self.language == "python":
                    if stripped.endswith(':'):
                        indent += "    "
                elif self.language in ["cpp", "c", "javascript", "java", "rust", "css", "html"]:
                    if stripped.endswith('{'):
                        indent += "    "
                    elif stripped == '}':
                        indent = indent[:-4] if len(indent) >= 4 else ""
            
            # Insert newline and indentation
            self.insertPlainText('\n' + indent)
            self.update_sidebar_width()
            self.lineNumberArea.update()
            return

        super().keyPressEvent(event)
        # Ensure cursor is visible after navigation
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, 
                           Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
                           Qt.Key.Key_Home, Qt.Key.Key_End):
            self.ensureCursorVisible()
            self.highlight_current_line()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_sidebar_area()

    def updateRequest(self, rect, dy):
        super().updateRequest(rect, dy)
        sidebar_width = self.line_number_width() + self.folding_area_width()
        if rect.contains(QRect(0, 0, sidebar_width, self.height())):
            self.lineNumberArea.update()
            self.foldingArea.update()
        self.marginLine.update()

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        
        # Increase font size slightly for line numbers
        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        painter.setFont(font)
        
        painter.fillRect(event.rect(), QColor("#1E1A2E"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        cursor = QTextCursor(block)
        rect = self.cursorRect(cursor)
        top = round(rect.top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#5C5478"))
                painter.drawText(0, top + 4, self.lineNumberArea.width() - 2, 
                                    bottom - top,
                                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
            
        # Draw vertical separator line on the right edge
        separator_x = self.lineNumberArea.width() - 1
        painter.setPen(QColor("#2F2A47"))
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
        self.current_theme = Theme.LILAC
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
                selection-background-color: {Tokens.BG_SURFACE.name()};
                selection-color: {Tokens.FG_PRIMARY.name()};
                font-family: {Tokens.FONT_MONO};
                font-size: {Tokens.FONT_SIZE_MONO}pt;
            }}
        """)

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return

        self.editor.blockSignals(True)
        try:
            self.editor.setPlainText(content)
        finally:
            self.editor.blockSignals(False)

        self.file_path = file_path
        self._is_modified = False

        lang = detect_language(file_path, content)
        print(f"[DEBUG] Detected language: {lang}")
        self._language = lang
        if lang:
            self.highlighter.set_language(lang)
            self.highlighter.rehighlight()
            self.editor.language = lang

    @property
    def language(self):
        return self._language

    def save_file(self, file_path=None):
        if file_path:
            self.file_path = file_path
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(self.editor.toPlainText())
        
        self._is_modified = False
        self.modified_changed.emit(self._is_modified)
        return True

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
