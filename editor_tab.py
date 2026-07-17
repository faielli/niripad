import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QTextEdit
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize, QPoint, QTimer
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
        gutter_bg = Theme.get_color(self.editor._theme_dict, "gutter_bg")
        painter.fillRect(event.rect(), gutter_bg)
        
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(0, -self.editor.verticalScrollBar().value()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                fold_end = self.editor.foldable_blocks.get(block_number)
                if fold_end is not None:
                    is_folded = block_number in self.editor.folded_blocks
                    painter.setPen(Theme.get_color(self.editor._theme_dict, "keyword"))
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

        self._fold_timer = QTimer(self)
        self._fold_timer.setSingleShot(True)
        self._fold_timer.setInterval(300)
        self._fold_timer.timeout.connect(self.update_foldable_blocks)

        self._theme_dict = Theme.by_name("lilac")

        self.textChanged.connect(self._fold_timer.start)
        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self.textChanged.connect(self._invalidate_bracket_cache)
        self._search_highlights = []
        self._bracket_highlights = []
        self._zoom_level = 100
        self._show_whitespace = False
        self._margin_column = 80
        self._show_margin = True
        self._loading = False
        self._bracket_text = ""

        self.update_sidebar_width()
        self.update_foldable_blocks()
        self.highlight_current_line()

    def _on_cursor_moved(self):
        self.highlight_current_line()
        self._update_bracket_match()

    def highlight_current_line(self):
        extra_selections = []
        
        selection = QTextEdit.ExtraSelection()
        line_color = Theme.get_color(self._theme_dict, "current_line_bg")
        if line_color.alpha() == 255:
            line_color.setAlpha(150)
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

    def _invalidate_bracket_cache(self):
        self._bracket_text = ""

    def _update_bracket_match(self):
        self._bracket_highlights = []
        cursor = self.textCursor()
        pos = cursor.position()
        doc = self.document()
        if not self._bracket_text:
            self._bracket_text = doc.toPlainText()
        text = self._bracket_text
        if not text or pos < 0 or pos > len(text):
            self.highlight_current_line()
            return

        pairs = {'(': ')', '[': ']', '{': '}'}
        match = None
        match_positions = []

        # Check char before cursor
        if pos > 0:
            char = text[pos - 1]
            if char in pairs:
                match = self._find_matching(text, pos - 1, 1)
                if match is not None:
                    match_positions = [pos - 1, match]
            elif char in pairs.values():
                open_for = {v: k for k, v in pairs.items()}[char]
                match = self._find_matching(text, pos - 1, -1)
                if match is not None:
                    match_positions = [pos - 1, match]

        # Check char at cursor (only if no match found from left side)
        if not match_positions and pos < len(text):
            char = text[pos]
            if char in pairs:
                match = self._find_matching(text, pos, 1)
                if match is not None:
                    match_positions = [pos, match]
            elif char in pairs.values():
                open_for = {v: k for k, v in pairs.items()}[char]
                match = self._find_matching(text, pos, -1)
                if match is not None:
                    match_positions = [pos, match]

        if match_positions:
            sels = []
            for mpos in match_positions:
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

    def _find_matching(self, text, start, direction):
        open_char = text[start]
        pairs = {'(': ')', '[': ']', '{': '}'}
        if direction == 1:
            expected_close = pairs[open_char]
        else:
            reverse = {v: k for k, v in pairs.items()}
            expected_close = reverse[open_char]
            open_char, expected_close = expected_close, open_char

        depth = 0
        pos = start
        while 0 <= pos < len(text):
            if text[pos] == open_char:
                depth += 1
            elif text[pos] == expected_close:
                depth -= 1
                if depth == 0:
                    return pos
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
            max_value //= 10
            digits += 1
        
        paint_font = self.font()
        paint_font.setPointSize(paint_font.pointSize() + 1)
        metrics = QFontMetrics(paint_font)
        space = 12

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
        
        block_count = self.document().blockCount()
        if block_count > 2000:
            first_visible = self.firstVisibleBlock().blockNumber()
            start = max(0, first_visible - 50)
            end = min(block_count, first_visible + 100)
            block = self.document().findBlockByNumber(start)
        else:
            block = self.document().begin()
        
        while block.isValid():
            text = block.text()
            stripped = text.strip()
            
            is_python_fold = stripped.endswith(':') and any(stripped.startswith(k) for k in ['def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with '])
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
            
            if block_count > 2000 and block.blockNumber() >= end:
                break
            block = block.next()
        
        self.folded_blocks &= set(self.foldable_blocks.keys())
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
        if event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                pos = cursor.position()
                text = self.toPlainText()
                if 0 < pos < len(text):
                    pairs_bs = [('(', ')'), ('[', ']'), ('{', '}'), ('"', '"'), ("'", "'")]
                    if (text[pos-1], text[pos]) in pairs_bs:
                        cursor.beginEditBlock()
                        cursor.setPosition(pos - 1)
                        cursor.setPosition(pos + 1, QTextCursor.MoveMode.KeepAnchor)
                        cursor.removeSelectedText()
                        cursor.endEditBlock()
                        return

        if key in pairs:
            cursor = self.textCursor()
            cursor.beginEditBlock()
            self.insertPlainText(key + pairs[key])
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            self.textCursor().endEditBlock()
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
        self.update_sidebar_width()

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
        
        gutter_bg = Theme.get_color(self._theme_dict, "gutter_bg")
        painter.fillRect(event.rect(), gutter_bg)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(0, -self.verticalScrollBar().value()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        line_fg = Theme.get_color(self._theme_dict, "line_number_fg")
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(line_fg)
                painter.drawText(0, top + 4, self.lineNumberArea.width() - 2, 
                                    bottom - top,
                                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
            
        # Draw vertical separator line on the right edge
        separator_x = self.lineNumberArea.width() - 1
        painter.setPen(Tokens.BORDER_SUBTLE)
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
        self.current_theme = Theme.by_name("lilac")
        self.apply_theme()
        
        self.highlighter = UniversalHighlighter(self.editor.document(), self.current_theme)
        
        if file_path:
            self.load_file(file_path)

    def set_theme(self, theme_name):
        self.current_theme = Theme.by_name(theme_name)
        self.editor._theme_dict = self.current_theme
        self.apply_theme()
        if hasattr(self, 'highlighter'):
            self.highlighter.theme = self.current_theme
            for key in list(type(self.highlighter)._rules_cache):
                if key[0] == self._language:
                    del type(self.highlighter)._rules_cache[key]
            if self._language:
                self.highlighter.set_language(self._language)
            else:
                self.highlighter.rehighlight()

    def apply_theme(self):
        bg_color = Theme.get_color(self.current_theme, "background")
        fg_color = Theme.get_color(self.current_theme, "foreground")
        selection_bg = Theme.get_color(self.current_theme, "selection_background")
        selection_fg = Theme.get_color(self.current_theme, "selection_foreground")

        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg_color.name()};
                color: {fg_color.name()};
                border: none;
                selection-background-color: {selection_bg.name()};
                selection-color: {selection_fg.name()};
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

        self.editor._loading = True
        try:
            self.editor.setPlainText(content)
        finally:
            self.editor._loading = False
        self.editor.update_sidebar_width()

        self.file_path = file_path
        self._is_modified = False
        self.modified_changed.emit(self._is_modified)

        lang = detect_language(file_path, content)
        print(f"[DEBUG] Detected language: {lang}")
        self._language = lang
        self.highlighter.set_language(lang)
        if lang:
            self.editor.language = lang

    @property
    def language(self):
        return self._language

    def save_file(self, file_path=None):
        if file_path:
            self.file_path = file_path

        if not self.file_path:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
        except Exception:
            return False

        self._is_modified = False
        self.editor.document().setModified(False)
        self.modified_changed.emit(self._is_modified)
        return True

    def on_text_changed(self):
        if self.editor._loading:
            return
        new_mod = self.editor.document().isModified()
        if new_mod != self._is_modified:
            self._is_modified = new_mod
            self.modified_changed.emit(self._is_modified)

    def is_modified(self):
        return self._is_modified

    def get_title(self):
        name = self.file_path if self.file_path else "Untitled"
        if self.file_path:
            return os.path.basename(name)
        return name
