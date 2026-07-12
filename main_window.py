import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QMessageBox, 
    QMenu, QMenuBar, QSplitter
)
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor, QTextDocument
from PyQt6.QtCore import Qt
from editor_tab import EditorTab
from search_dialog import SearchReplaceDialog
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
        
        # Main Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # File Tree
        self.file_tree = FileTree(os.getcwd())
        self.file_tree.fileOpened.connect(self.open_file)
        self.splitter.addWidget(self.file_tree)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.splitter.addWidget(self.tabs)
        
        # Set initial splitter proportions
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)

        # Search & Command Palette
        self.search_dialog = SearchReplaceDialog(self)
        self.search_dialog.find_requested.connect(self.handle_find)
        self.search_dialog.replace_requested.connect(self.handle_replace)
        self.search_dialog.replace_all_requested.connect(self.handle_replace_all)
        self.search_dialog.hide()

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
            "command_palette": "Command Palette"
        }
        self.command_palette = CommandPalette(self.commands, self)
        self.command_palette.actionTriggered.connect(self.execute_command)
        self.command_palette.hide()

        self._create_menu()
        
        # Initial tab
        self.new_file()

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
        find_action.triggered.connect(self.show_search_dialog)
        edit_menu.addAction(find_action)

        # Replace
        replace_action = QAction("&Replace", self)
        replace_action.setShortcut(QKeySequence(self.config_manager.get_binding("replace")))
        replace_action.triggered.connect(self.show_search_dialog)
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

    def new_file(self):
        tab = EditorTab()
        index = self.tabs.addTab(tab, tab.get_title())
        self.tabs.setCurrentIndex(index)
        tab.modified_changed.connect(lambda: self.update_tab_title(index))

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        
        if file_path:
            tab = EditorTab(file_path)
            index = self.tabs.addTab(tab, tab.get_title())
            self.tabs.setCurrentIndex(index)
            tab.modified_changed.connect(lambda: self.update_tab_title(index))

    def save_file(self):
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            return

        if current_tab.file_path:
            current_tab.save_file()
        else:
            self.save_file_as()

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
        if tab:
            self.tabs.setTabText(index, tab.get_title())

    def closeEvent(self, event):
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

    def show_search_dialog(self):
        self.search_dialog.show()

    def show_command_palette(self):
        self.command_palette.show()

    def show_keybindings_dialog(self):
        dialog = KeybindingsDialog(self.config_manager, self)
        if dialog.exec():
            self._create_menu()

    def handle_find(self, text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not text:
            return False

        editor = current_tab.editor
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if not is_regex:
            if editor.find(text, flags):
                return True
            # Wrap around
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            editor.setTextCursor(cursor)
            return editor.find(text, flags)
        else:
            # Regex find implementation
            content = editor.toPlainText()
            cursor = editor.textCursor()
            start_pos = cursor.position()
            
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            match = re.search(text, content[start_pos:], flags=regex_flags)
            
            if match:
                match_start = start_pos + match.start()
                match_end = start_pos + match.end()
                cursor.setPosition(match_start)
                cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)
                editor.setTextCursor(cursor)
                return True
            else:
                # Wrap around
                match = re.search(text, content, flags=regex_flags)
                if match:
                    cursor.setPosition(match.start())
                    cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
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
            self.show_search_dialog()
        elif command_id == "replace":
            self.show_search_dialog()
        elif command_id == "undo":
            self.handle_undo()
        elif command_id == "redo":
            self.handle_redo()
        elif command_id == "command_palette":
            self.show_command_palette()
