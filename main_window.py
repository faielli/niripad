import os
import re
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QMessageBox, 
    QMenu, QMenuBar, QSplitter, QWidget, QVBoxLayout, QLabel,
    QPushButton, QTabBar, QStyle
)



from PyQt6.QtGui import QAction, QKeySequence, QTextCursor, QTextDocument, QColor, QPixmap, QPainter, QIcon, QShortcut
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer
from editor_tab import EditorTab
from search_dialog import SearchPanel, GoToLinePanel
from file_tree import FileTree
from command_palette import CommandPalette
from config_manager import ConfigManager
from keybindings_dialog import KeybindingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Niri Editor")
        self.resize(1200, 800)

        self.config_manager = ConfigManager()
        
        # Status icons
        self.status_icons = self._create_file_status_icons()
        
        # Main Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #3B4252; width: 1px; }")
        self.setCentralWidget(self.splitter)

        # File Tree
        self.file_tree = FileTree(os.getcwd())
        self.file_tree.fileOpened.connect(self.open_file)
        self.splitter.addWidget(self.file_tree)

        # Editor Container (Tabs + Search Panel)
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.editor_layout.addWidget(self.tabs)
        
        # Search Panel
        self.search_panel = SearchPanel()
        self.search_panel.setMaximumHeight(0)
        self.search_panel.find_next_requested.connect(lambda t, c, r: self.handle_find(t, c, r, forward=True))
        self.search_panel.find_prev_requested.connect(lambda t, c, r: self.handle_find(t, c, r, forward=False))
        self.search_panel.replace_requested.connect(self.handle_replace)
        self.search_panel.replace_all_requested.connect(self.handle_replace_all)
        self.search_panel.close_requested.connect(self.toggle_search_panel)
        self.editor_layout.addWidget(self.search_panel)

        # Go to Line Panel
        self.goto_panel = GoToLinePanel()
        self.goto_panel.goto_requested.connect(self.handle_goto_line)
        self.goto_panel.close_requested.connect(self.hide_goto_line)
        self.goto_panel.hide()
        self.editor_layout.addWidget(self.goto_panel)

        self.splitter.addWidget(self.editor_container)
        
        # Set initial splitter proportions
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([250, 950])
        
        self.commands = {
            "new_file": "New File",
            "open_file": "Open File",
            "save_file": "Save",
            "save_as": "Save As...",
            "close_tab": "Close Tab",
            "find": "Find",
            "replace": "Replace",
            "undo": "Undo",
            "redo": "Redo",
            "command_palette": "Command Palette",
            "goto_line": "Go to Line"
        }
        # Command Palette
        self.command_palette = CommandPalette(self.commands, self)
        self.command_palette.actionTriggered.connect(self.execute_command)
        self.command_palette.hide()
        
        # Add global shortcut for Ctrl+G
        goto_shortcut = QShortcut(QKeySequence(self.config_manager.get_binding("goto_line")), self)
        goto_shortcut.activated.connect(self.show_goto_line)

        self._setup_statusbar()
        self._create_menu()
        
        # Initial tab
        self.new_file()
        self._restore_session()
        self._start_autosave_timer()

    def _setup_statusbar(self):
        self.statusBar().setMinimumHeight(24)
        
        # Left side widgets
        self.lang_label = QLabel("Plain Text")
        self.lang_label.setStyleSheet("color: #88C0D0;")
        self.statusBar().addWidget(self.lang_label)
        
        separator = QLabel(" | ")
        separator.setStyleSheet("color: #4C566A;")
        self.statusBar().addWidget(separator)
        
        self.line_col_label = QLabel("Ln 1, Col 1")
        self.line_col_label.setStyleSheet("color: #8892a0;")
        self.statusBar().addWidget(self.line_col_label)
        
        # Right side widgets (Permanent)
        self.git_label = QLabel("")
        self.git_label.setStyleSheet("color: #A3BE8C;")
        self.statusBar().addPermanentWidget(self.git_label)
        
        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setStyleSheet("color: #4C566A;")
        self.statusBar().addPermanentWidget(self.encoding_label)
        
        self.tabsize_label = QLabel("Spaces: 4")
        self.tabsize_label.setStyleSheet("color: #4C566A;")
        self.statusBar().addPermanentWidget(self.tabsize_label)
        
        # Connections
        self.tabs.currentChanged.connect(self._update_statusbar)
        
    def _update_statusbar(self):
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            return
            
        # Update Language
        lang = current_tab.language or "Plain Text"
        self.lang_label.setText(lang)
        
        # Update Git Branch
        self._update_git_branch(current_tab)
        
        # Connect cursor change signal
        try:
            current_tab.editor.cursorPositionChanged.disconnect()
        except (TypeError, RuntimeError):
            pass
        current_tab.editor.cursorPositionChanged.connect(self._update_cursor_pos)
        self._update_cursor_pos()

    def _update_cursor_pos(self):
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            return
        cursor = current_tab.editor.textCursor()
        self.line_col_label.setText(f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}")

    def _update_git_branch(self, tab):
        path = tab.file_path if tab.file_path else os.getcwd()
        workdir = os.path.dirname(os.path.abspath(path))
        
        try:
            # Run git branch --show-current in the file's directory
            result = subprocess.run(
                ["git", "-C", workdir, "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=1
            )
            branch = result.stdout.strip()
            if branch:
                self.git_label.setText(f"⎇ {branch}")
                self.git_label.show()
            else:
                self.git_label.hide()
        except Exception:
            self.git_label.hide()

    def _create_file_status_icons(self):
        icons = {}
        for state, color in [("saved", "#A3BE8C"), ("modified", "#EBCB8B")]:
            pixmap = QPixmap(12, 12)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, 8, 8)
            painter.end()
            icons[state] = QIcon(pixmap)
        return icons

    def _create_menu(self):
        menubar = self.menuBar()
        
        # Clear existing menus if any (for reloading)
        for action in menubar.actions():
            menubar.removeAction(action)
            
        file_menu = menubar.addMenu("&File")

        # New
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence(self.config_manager.get_binding("new_file")))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence(self.config_manager.get_binding("open_file")))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Save
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence(self.config_manager.get_binding("save_file")))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence(self.config_manager.get_binding("save_as")))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Close
        close_action = QAction("&Close Tab", self)
        close_action.setShortcut(QKeySequence(self.config_manager.get_binding("close_tab")))
        close_action.triggered.connect(self.close_tab_action)
        file_menu.addAction(close_action)

        edit_menu = menubar.addMenu("&Edit")

        # Find
        find_action = QAction("&Find", self)
        find_action.setShortcut(QKeySequence(self.config_manager.get_binding("find")))
        find_action.triggered.connect(self.toggle_search_panel)
        edit_menu.addAction(find_action)

        # Replace
        replace_action = QAction("&Replace", self)
        replace_action.setShortcut(QKeySequence(self.config_manager.get_binding("replace")))
        replace_action.triggered.connect(self.toggle_search_panel)
        edit_menu.addAction(replace_action)

        edit_menu.addSeparator()

        # Undo
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence(self.config_manager.get_binding("undo")))
        undo_action.triggered.connect(self.handle_undo)
        edit_menu.addAction(undo_action)

        # Redo
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence(self.config_manager.get_binding("redo")))
        redo_action.triggered.connect(self.handle_redo)
        edit_menu.addAction(redo_action)

        # Go to Line
        goto_line_action = QAction("Go to Line", self)
        goto_line_action.setShortcut(QKeySequence(self.config_manager.get_binding("goto_line")))
        goto_line_action.triggered.connect(self.show_goto_line)
        edit_menu.addAction(goto_line_action)

        # Command Palette
        palette_action = QAction("&Command Palette", self)
        palette_action.setShortcut(QKeySequence(self.config_manager.get_binding("command_palette")))
        palette_action.triggered.connect(self.show_command_palette)
        edit_menu.addAction(palette_action)

        # Settings
        settings_menu = menubar.addMenu("&Settings")
        keybindings_action = QAction("&Keybindings...", self)
        keybindings_action.triggered.connect(self.show_keybindings_dialog)
        settings_menu.addAction(keybindings_action)

    def _start_autosave_timer(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._do_autosave)
        self.autosave_timer.start(30000)  # 30 seconds

    def _do_autosave(self):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.is_modified():
                if tab.file_path:
                    tab.save_file()
                else:
                    cache_dir = self.config_manager.get_cache_dir()
                    temp_path = os.path.join(cache_dir, f"Untitled_{i}.txt")
                    tab.save_file(temp_path)
                    # Reset modified flag so we don't save constantly if nothing changed
                    # Since save_file does this, it's actually OK.

    def _save_session(self):
        session_data = {
            "tabs": [],
            "current_index": self.tabs.currentIndex(),
            "geometry": {
                "pos": (self.x(), self.y()),
                "size": (self.width(), self.height())
            },
            "splitter_sizes": self.splitter.sizes()
        }
        
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab:
                session_data["tabs"].append({
                    "path": tab.file_path,
                    "content": tab.editor.toPlainText() if not tab.file_path else None
                })
        
        self.config_manager.save_session(session_data)

    def _restore_session(self):
        session_data = self.config_manager.load_session()
        if not session_data:
            return

        # Restore geometry
        geo = session_data.get("geometry")
        if geo:
            self.move(geo["pos"][0], geo["pos"][1])
            self.resize(geo["size"][0], geo["size"][1])

        # Restore splitter sizes
        sizes = session_data.get("splitter_sizes")
        if sizes:
            self.splitter.setSizes(sizes)

        # Restore tabs
        tabs = session_data.get("tabs")
        if tabs:
            # Remove the initial tab created in __init__
            if self.tabs.count() > 0:
                self.tabs.removeTab(0)
                
            for tab_info in tabs:
                path = tab_info.get("path")
                content = tab_info.get("content")
                
                if path:
                    self.open_file(path)
                else:
                    # Manually create a tab for untitled content
                    tab = EditorTab()
                    index = self.tabs.addTab(tab, tab.get_title())
                    tab.editor.setPlainText(content or "")
                    tab.modified_changed.connect(lambda i=index: self.update_tab_title(i))
                    self.add_close_button(index)
        
        current_index = session_data.get("current_index", 0)
        if current_index < self.tabs.count():
            self.tabs.setCurrentIndex(current_index)


    def new_file(self):
        tab = EditorTab()
        index = self.tabs.addTab(tab, tab.get_title())
        self.tabs.setCurrentIndex(index)
        tab.modified_changed.connect(lambda i=index: self.update_tab_title(i))
        self.add_close_button(index)

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        
        if file_path:
            # Check if a tab with the same file path is already open
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if tab.file_path == file_path:
                    self.tabs.setCurrentIndex(i)
                    return
            
            tab = EditorTab(file_path)
            index = self.tabs.addTab(tab, tab.get_title())
            self.tabs.setCurrentIndex(index)
            tab.modified_changed.connect(lambda i=index: self.update_tab_title(i))
            self.add_close_button(index)

    def add_close_button(self, index):
        close_btn = QPushButton()
        close_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        close_btn.setIconSize(QSize(12, 12))
        close_btn.setFixedSize(16, 16)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #3B4252;
            }
        """)
        close_btn.clicked.connect(lambda checked, i=index: self.close_tab(i))
        # Use QTabBar.ButtonPosition(1) to explicitly create the 'Right' enum member
        # This avoids the AttributeError with .Right and the TypeError with raw int
        self.tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition(1), close_btn)

    def save_file(self):

        index = self.tabs.currentIndex()
        if index < 0:
            return
        self.save_tab_by_index(index)

    def save_file_as(self):
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As")
        if file_path:
            current_tab.save_file(file_path)
            self.update_tab_title(self.tabs.currentIndex())

    def close_tab(self, index):
        tab = self.tabs.widget(index)
        if tab and tab.is_modified():
            ret = QMessageBox.question(
                self, "Save Changes?", 
                f"The file {tab.get_title()} has been modified. Do you want to save it?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if ret == QMessageBox.StandardButton.Save:
                if not self.save_tab_by_index(index):
                    return
            elif ret == QMessageBox.StandardButton.Cancel:
                return

        self.tabs.removeTab(index)
        
        # If no tabs left, create a new one to ensure editor is never empty
        if self.tabs.count() == 0:
            self.new_file()

    def close_tab_action(self):
        self.close_tab(self.tabs.currentIndex())

    def save_tab_by_index(self, index):
        tab = self.tabs.widget(index)
        if not tab:
            return False
        if tab.file_path:
            return tab.save_file()
        else:
            # Save As
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File As")
            if file_path:
                return tab.save_file(file_path)
            return False

    def update_tab_title(self, index):
        tab = self.tabs.widget(index)
        if not tab:
            return
        
        title = tab.get_title()
        tab_bar = self.tabs.tabBar()
        
        if tab.is_modified():
            # Color the entire tab text yellow to indicate modification
            tab_bar.setTabTextColor(index, QColor("#EBCB8B"))
            self.tabs.setTabIcon(index, self.status_icons["modified"])
        else:
            # Restore default colors based on selection state
            if self.tabs.currentIndex() == index:
                tab_bar.setTabTextColor(index, QColor("#D8DEE9"))  # fg0
            else:
                tab_bar.setTabTextColor(index, QColor("#8892a0"))  # fg1
            self.tabs.setTabIcon(index, self.status_icons["saved"])
        
        self.tabs.setTabText(index, title)

    def closeEvent(self, event):
        # Final autosave
        self._do_autosave()
        # Save session
        self._save_session()
        
        # Basic loop to check all tabs before closing
        for i in range(self.tabs.count() - 1, -1, -1):

            tab = self.tabs.widget(i)
            if tab and tab.is_modified():
                ret = QMessageBox.question(
                    self, "Save Changes?", 
                    f"The file {tab.get_title()} has been modified. Do you want to save it?",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                if ret == QMessageBox.StandardButton.Save:
                    if not self.save_tab_by_index(i):
                        event.ignore()
                        return
                elif ret == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
        event.accept()

    def handle_undo(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.editor.undo()

    def handle_redo(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.editor.redo()

    def toggle_search_panel(self):
        if self.search_panel.maximumHeight() > 0:
            # Animate to hidden
            self.anim = QPropertyAnimation(self.search_panel, b"maximumHeight")
            self.anim.setDuration(200)
            self.anim.setStartValue(self.search_panel.maximumHeight())
            self.anim.setEndValue(0)
            self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim.start()
        else:
            # Animate to visible
            self.anim = QPropertyAnimation(self.search_panel, b"maximumHeight")
            self.anim.setDuration(200)
            self.anim.setStartValue(0)
            self.anim.setEndValue(150)
            self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim.start()

    def show_command_palette(self):
        self.command_palette.show()

    def show_keybindings_dialog(self):
        dialog = KeybindingsDialog(self.config_manager, self)
        if dialog.exec():
            self._create_menu()

    def handle_find(self, text, case_sensitive, is_regex, forward=True):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not text:
            return False

        editor = current_tab.editor
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        # Update match count
        content = editor.toPlainText()
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        if is_regex:
            matches = list(re.finditer(text, content, flags=regex_flags))
        else:
            # Basic count for plain text
            import collections
            matches = [m.start() for m in re.finditer(re.escape(text), content, flags=regex_flags)]
        
        total = len(matches)
        current = 0
        cursor_pos = editor.textCursor().position()
        for m in matches:
            if m.start() < cursor_pos:
                current += 1
        
        self.search_panel.set_match_count(current, total)

        if not is_regex:
            if forward:
                if editor.find(text, flags):
                    return True
                # Wrap around
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                editor.setTextCursor(cursor)
                return editor.find(text, flags)
            else:
                # Find previous (basic implementation)
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                editor.setTextCursor(cursor)
                found_pos = -1
                while editor.find(text, flags):
                    found_pos = editor.textCursor().position()
                if found_pos != -1:
                    return True
                return False
        else:
            # Regex find implementation
            if forward:
                match = re.search(text, content[cursor_pos:], flags=regex_flags)
                if match:
                    match_start = cursor_pos + match.start()
                    match_end = cursor_pos + match.end()
                    cursor = editor.textCursor()
                    cursor.setPosition(match_start)
                    cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)
                    editor.setTextCursor(cursor)
                    return True
                else:
                    match = re.search(text, content, flags=regex_flags)
                    if match:
                        cursor = editor.textCursor()
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                        editor.setTextCursor(cursor)
                        return True
            else:
                matches_objs = list(re.finditer(text, content, flags=regex_flags))
                if not matches_objs:
                    return False
                prev_match = None
                for m in matches_objs:
                    if m.start() < cursor_pos:
                        prev_match = m
                if prev_match:
                    cursor = editor.textCursor()
                    cursor.setPosition(prev_match.start())
                    cursor.setPosition(prev_match.end(), QTextCursor.MoveMode.KeepAnchor)
                    editor.setTextCursor(cursor)
                    return True
                elif matches_objs:
                    last_match = matches_objs[-1]
                    cursor = editor.textCursor()
                    cursor.setPosition(last_match.start())
                    cursor.setPosition(last_match.end(), QTextCursor.MoveMode.KeepAnchor)
                    editor.setTextCursor(cursor)
                    return True
            return False

    def handle_replace(self, search_text, replace_text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        cursor = editor.textCursor()
        
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(replace_text)
        else:
            # Find next and replace
            if self.handle_find(search_text, case_sensitive, is_regex):
                cursor = editor.textCursor()
                cursor.insertText(replace_text)
                editor.setTextCursor(cursor)

    def handle_replace_all(self, search_text, replace_text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        content = editor.toPlainText()
        
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        if is_regex:
            new_content = re.sub(search_text, replace_text, content, flags=regex_flags)
        else:
            # Plain text replace all
            if case_sensitive:
                new_content = content.replace(search_text, replace_text)
            else:
                # Case insensitive replace
                pattern = re.compile(re.escape(search_text), regex_flags)
                new_content = pattern.sub(replace_text, content)
        
        if new_content != content:
            editor.setPlainText(new_content)
            current_tab.on_text_changed() # Mark as modified

    def execute_command(self, command_id):
        if command_id == "new_file":
            self.new_file()
        elif command_id == "open_file":
            self.open_file()
        elif command_id == "save_file":
            self.save_file()
        elif command_id == "save_as":
            self.save_file_as()
        elif command_id == "close_tab":
            self.close_tab_action()
        elif command_id == "find":
            self.toggle_search_panel()
        elif command_id == "replace":
            self.toggle_search_panel()
        elif command_id == "undo":
            self.handle_undo()
        elif command_id == "redo":
            self.handle_redo()
        elif command_id == "command_palette":
            self.show_command_palette()
        elif command_id == "goto_line":
            self.show_goto_line()

    def show_goto_line(self):
        self.goto_panel.show()
        self.goto_panel.input.setFocus()
        self.goto_panel.input.clear()

    def hide_goto_line(self):
        self.goto_panel.hide()

    def handle_goto_line(self, line_number):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            max_lines = current_tab.editor.document().blockCount()
            if 1 <= line_number <= max_lines:
                current_tab.editor.go_to_line(line_number)
            else:
                self.goto_panel.set_error()
