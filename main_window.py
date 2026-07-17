import os
import re
import time
import subprocess
import hashlib
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QFileDialog, QMessageBox,
    QMenu, QMenuBar, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabBar, QToolButton, QSizePolicy, QTextEdit
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QTextCursor, QTextDocument, QColor,
    QIcon, QShortcut, QDrag
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QEvent, QObject, QThread, pyqtSignal, QMimeData


class GitBranchWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, workdir):
        super().__init__()
        self.workdir = workdir

    def run(self):
        try:
            result = subprocess.run(
                ["git", "-C", self.workdir, "branch", "--show-current"],
                capture_output=True, text=True, timeout=1
            )
            self.finished.emit(result.stdout.strip())
        except Exception:
            self.finished.emit("")
from editor_tab import EditorTab
from search_dialog import SearchPanel, GoToLinePanel
from file_tree import FileTree
from command_palette import CommandPalette
from config_manager import ConfigManager
from keybindings_dialog import KeybindingsDialog
from icon_utils import Icons
from qss_tokens import apply_shadow
from theme_tokens import Tokens


class DraggableTabBar(QTabBar):
    def __init__(self, parent=None, pane='left', main_window=None):
        super().__init__(parent)
        self._pane = pane
        self._main_window = main_window
        self._drag_start_pos = None
        self._drag_tab_index = -1
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_tab_index = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton and
            self._drag_tab_index >= 0 and
            (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance()):
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData("application/x-tab-move",
                         f"{self._pane},{self._drag_tab_index}".encode())
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
            self._drag_start_pos = None
            self._drag_tab_index = -1
        else:
            super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-tab-move"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-tab-move"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-tab-move"):
            data = event.mimeData().data("application/x-tab-move").data().decode()
            source_pane, source_index = data.split(",")
            source_index = int(source_index)
            target_index = self.tabAt(event.pos())
            if target_index < 0:
                target_index = self.count()
            self._main_window._move_tab(source_pane, source_index, self._pane, target_index)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Niri Editor")
        self.resize(1200, 800)

        self.config_manager = ConfigManager()

        # Status icons
        self.status_icons = self._create_file_status_icons()

        self.sidebar_visible = True
        self.sidebar_width = 250

        self._git_cache = {}
        self._git_cache_ttl = 5
        self._git_workers = []

        self.file_tree = FileTree(os.getcwd())
        self.file_tree.fileOpened.connect(self.open_file)
        self.file_tree.setMinimumWidth(200)

        # Sidebar Content (header + file tree)
        self.sidebar_content = QWidget()
        self.sidebar_content.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar_content)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)

        self.sidebar_layout.addWidget(self.file_tree)

        # Main Splitter (sidebar_content + editor_area)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        # Toggle Strip (thin strip visible only when sidebar is closed)
        self.toggle_strip = QWidget()
        self.toggle_strip.setObjectName("sidebar_strip")
        self.toggle_strip.setFixedWidth(22)
        strip_layout = QVBoxLayout(self.toggle_strip)
        strip_layout.setContentsMargins(0, 0, 0, 0)
        strip_layout.setSpacing(0)
        strip_layout.addStretch()
        self.strip_arrow = QPushButton()
        self.strip_arrow.setObjectName("sidebar_toggle")
        self.strip_arrow.setIcon(Icons(Tokens.ICON_STROKE).bars())
        self.strip_arrow.setIconSize(QSize(13, 13))
        self.strip_arrow.setFixedSize(22, 30)
        self.strip_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.strip_arrow.setToolTip("Show sidebar (Ctrl+B)")
        self.strip_arrow.clicked.connect(self.toggle_sidebar)
        strip_layout.addWidget(self.strip_arrow)
        strip_layout.addStretch()
        self.toggle_strip.hide()

        # Main container: toggle_strip + splitter
        self.main_container = QWidget()
        main_layout = QHBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.toggle_strip)
        main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.main_container)

        # Editor Tab Widgets (left and right panes)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setTabBar(DraggableTabBar(pane='left', main_window=self))
        self.tabs.setAcceptDrops(True)

        self.tabs_right = QTabWidget()
        self.tabs_right.setTabsClosable(False)
        self.tabs_right.tabCloseRequested.connect(lambda idx: self.close_tab(idx, pane='right'))
        self.tabs_right.setTabBar(DraggableTabBar(pane='right', main_window=self))
        self.tabs_right.setAcceptDrops(True)
        self.tabs_right.hide()

        self._active_pane = 'left'
        self.tabs.currentChanged.connect(lambda: setattr(self, '_active_pane', 'left'))
        self.tabs_right.currentChanged.connect(lambda: setattr(self, '_active_pane', 'right'))

        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setObjectName("editor_splitter")
        self.editor_splitter.setHandleWidth(2)
        self.editor_splitter.addWidget(self.tabs)
        self.editor_splitter.addWidget(self.tabs_right)
        self.editor_splitter.setSizes([600, 600])
        self.editor_splitter.setStretchFactor(0, 1)
        self.editor_splitter.setStretchFactor(1, 1)

        # Editor Container (Splitter + Search Panel)
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)
        self.editor_layout.addWidget(self.editor_splitter)

        corner = QWidget()
        corner_layout = QHBoxLayout(corner)
        corner_layout.setContentsMargins(2, 0, 2, 0)
        corner_layout.setSpacing(2)

        ico = Icons(Tokens.ICON_STROKE)

        self.sidebar_toggle = QToolButton()
        self.sidebar_toggle.setIcon(ico.sitemap())
        self.sidebar_toggle.setIconSize(QSize(16, 16))
        self.sidebar_toggle.setFixedSize(28, 28)
        self.sidebar_toggle.setAutoRaise(True)
        self.sidebar_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_toggle.setToolTip("Toggle sidebar (Ctrl+B)")
        self.sidebar_toggle.setAccessibleName("Toggle sidebar")
        self.sidebar_toggle.clicked.connect(self.toggle_sidebar)
        corner_layout.addWidget(self.sidebar_toggle)

        self.folder_btn = QToolButton()
        self.folder_btn.setIcon(ico.folder_open())
        self.folder_btn.setIconSize(QSize(16, 16))
        self.folder_btn.setFixedSize(28, 28)
        self.folder_btn.setAutoRaise(True)
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.setToolTip("Select root folder")
        self.folder_btn.setAccessibleName("Select root folder")
        self.folder_btn.clicked.connect(self.file_tree.on_browse_folder)
        corner_layout.addWidget(self.folder_btn)

        self.tabs.setCornerWidget(corner, Qt.Corner.TopLeftCorner)
        
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

        # Editor Area (no toggle — just the editor container)
        self.editor_area = QWidget()
        editor_hlayout = QHBoxLayout(self.editor_area)
        editor_hlayout.setContentsMargins(0, 0, 0, 0)
        editor_hlayout.setSpacing(0)
        editor_hlayout.addWidget(self.editor_container)

        # Add both widgets to splitter: sidebar content first, editor second
        self.splitter.addWidget(self.sidebar_content)
        self.splitter.addWidget(self.editor_area)
        
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
        
        # Add global shortcut for Ctrl+B (Toggle Sidebar)
        sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        sidebar_shortcut.activated.connect(self.toggle_sidebar)
        
        self._cursor_editor = None
        self._setup_statusbar()
        self._create_menu()

        # Initial tab
        self._restore_session()
        if self.tabs.count() == 0:
            self.new_file()
        self._start_autosave_timer()

    def toggle_sidebar(self):
        total = sum(self.splitter.sizes())
        ico = Icons(Tokens.ICON_STROKE)
        if self.sidebar_visible:
            self.splitter.setSizes([0, total])
            self.sidebar_content.hide()
            self.toggle_strip.show()
            self.sidebar_toggle.setIcon(ico.chevron_right())
        else:
            self.splitter.setSizes([self.sidebar_width, total - self.sidebar_width])
            self.sidebar_content.show()
            self.toggle_strip.hide()
            self.sidebar_toggle.setIcon(ico.chevron_left())
        self.sidebar_visible = not self.sidebar_visible

    def _on_splitter_moved(self, pos, index):
        if self.sidebar_visible:
            self.sidebar_width = self.splitter.sizes()[0]

    def _setup_statusbar(self):
        self.statusBar().setMinimumHeight(24)
        
        # Left side widgets
        self.lang_label = QLabel("Plain Text")
        self.lang_label.setObjectName("status_mode")
        self.statusBar().addWidget(self.lang_label)

        separator1 = QLabel(" | ")
        self.statusBar().addWidget(separator1)

        self.line_col_label = QLabel("Ln 1, Col 1")
        self.statusBar().addWidget(self.line_col_label)

        separator2 = QLabel(" | ")
        self.statusBar().addWidget(separator2)
        
        # Right side widgets
        self.git_label = QLabel("")
        self.statusBar().addWidget(self.git_label)
        
        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.statusBar().addWidget(self.encoding_label)

        separator3 = QLabel(" | ")
        self.statusBar().addWidget(separator3)
        
        self.line_ending_label = QLabel("LF")
        self.line_ending_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.statusBar().addWidget(self.line_ending_label)

        separator4 = QLabel(" | ")
        self.statusBar().addWidget(separator4)
        
        self.tabsize_label = QLabel("Spaces: 4")
        self.tabsize_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.statusBar().addWidget(self.tabsize_label)

        separator5 = QLabel(" | ")
        self.statusBar().addWidget(separator5)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.statusBar().addWidget(self.zoom_label)
        
        self.encoding_label.mousePressEvent = lambda e: self._cycle_encoding() if e.button() == Qt.MouseButton.LeftButton else super(type(self.encoding_label), self.encoding_label).mousePressEvent(e)
        self.line_ending_label.mousePressEvent = lambda e: self._cycle_line_ending() if e.button() == Qt.MouseButton.LeftButton else super(type(self.line_ending_label), self.line_ending_label).mousePressEvent(e)
        self.tabsize_label.mousePressEvent = lambda e: self._cycle_tab_width() if e.button() == Qt.MouseButton.LeftButton else super(type(self.tabsize_label), self.tabsize_label).mousePressEvent(e)
        self.zoom_label.mousePressEvent = lambda e: self._reset_zoom() if e.button() == Qt.MouseButton.LeftButton else super(type(self.zoom_label), self.zoom_label).mousePressEvent(e)
        
        # Connections
        self.tabs.currentChanged.connect(self._update_statusbar)
        self.tabs_right.currentChanged.connect(self._update_statusbar)
        
    def _update_statusbar(self):
        current_tab = self._active_tab_widget().currentWidget()
        if not current_tab:
            return
            
        # Update Language
        lang = current_tab.language or "Plain Text"
        self.lang_label.setText(lang)
        
        # Update Git Branch
        self._update_git_branch(current_tab)

        # Connect cursor change signal (only if editor changed)
        editor = current_tab.editor
        if editor != self._cursor_editor:
            if self._cursor_editor is not None:
                try:
                    self._cursor_editor.cursorPositionChanged.disconnect(self._update_cursor_pos)
                except TypeError:
                    pass
            editor.cursorPositionChanged.connect(self._update_cursor_pos)
            self._cursor_editor = editor
        self._update_cursor_pos()

        # Install zoom handler on viewport
        current_tab.editor.viewport().removeEventFilter(self) if hasattr(current_tab.editor, 'viewport') else None
        current_tab.editor.viewport().installEventFilter(self)

        # Update status items from config
        cfg = self.config_manager
        self.encoding_label.setText(cfg.get("encoding", "UTF-8"))
        self.line_ending_label.setText(cfg.get("line_ending", "LF"))
        self.tabsize_label.setText(f"Spaces: {cfg.get('tab_width', 4)}")

        zoom = current_tab.editor._zoom_level
        self.zoom_label.setText(f"{zoom}%")

    def _update_cursor_pos(self):
        current_tab = self._active_tab_widget().currentWidget()
        if not current_tab:
            return
        cursor = current_tab.editor.textCursor()
        self.line_col_label.setText(f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            tab = self._active_tab_widget().currentWidget()
            if tab:
                angle = event.angleDelta().y()
                if angle > 0:
                    tab.editor.zoom_in()
                else:
                    tab.editor.zoom_out()
                self.zoom_label.setText(f"{tab.editor._zoom_level}%")
            return True
        return super().eventFilter(obj, event)

    def _update_git_branch(self, tab):
        path = tab.file_path if tab.file_path else os.getcwd()
        workdir = os.path.dirname(os.path.abspath(path))

        cached = self._git_cache.get(workdir)
        now = time.time()
        if cached and (now - cached["time"]) < self._git_cache_ttl:
            branch = cached["branch"]
            if branch:
                self.git_label.setText(f"⎇ {branch}")
                self.git_label.show()
            else:
                self.git_label.hide()
            return

        thread = QThread()
        worker = GitBranchWorker(workdir)
        worker.moveToThread(thread)
        self._git_workers.append((thread, worker))
        thread.started.connect(worker.run)
        worker.finished.connect(lambda branch: self._on_git_branch_result(workdir, branch))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._git_workers.remove((thread, worker)))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_git_branch_result(self, workdir, branch):
        self._git_cache[workdir] = {"branch": branch, "time": time.time()}
        if branch:
            self.git_label.setText(f"⎇ {branch}")
            self.git_label.show()
        else:
            self.git_label.hide()

    def _create_file_status_icons(self):
        ico = Icons()
        return {
            "saved": ico.check_circle(),
            "modified": QIcon(),
        }

    def _active_tab_widget(self):
        if self._active_pane == 'right' and not self.tabs_right.isHidden():
            return self.tabs_right
        return self.tabs

    def split_editor(self):
        tw = self.tabs_right
        if tw.isHidden():
            total = sum(self.splitter.sizes())
            tw.show()
            self.editor_splitter.setSizes([total // 2, total // 2])
        left_tab = self.tabs.currentWidget()
        if left_tab:
            right_tab = EditorTab(left_tab.file_path)
            right_tab.set_theme(self.config_manager.get("theme", "lilac"))
            right_tab.editor.set_word_wrap(self.word_wrap_action.isChecked())
            right_tab.editor.set_show_whitespace(self.show_whitespace_action.isChecked())
            right_tab.editor.set_show_margin(self.show_margin_action.isChecked())
            if left_tab.file_path:
                right_tab.load_file(left_tab.file_path)
            else:
                right_tab.editor._loading = True
                right_tab.editor.setPlainText(left_tab.editor.toPlainText())
                right_tab.editor._loading = False
            index = tw.addTab(right_tab, right_tab.get_title())
            tw.setCurrentIndex(index)
            right_tab.modified_changed.connect(
                lambda modified, tab=right_tab: self._update_tab_title_pane('right', tw.indexOf(tab))
            )
            self.add_close_button_to('right', index)
        self._active_pane = 'right'

    def _update_tab_title_pane(self, pane, index):
        tw = self.tabs if pane == 'left' else self.tabs_right
        tab = tw.widget(index)
        if not tab:
            return
        title = tab.get_title()
        if tab.is_modified():
            tw.setTabText(index, f"● {title}")
            tw.setTabIcon(index, self.status_icons["modified"])
        else:
            tw.setTabText(index, title)
            tw.setTabIcon(index, self.status_icons["saved"])

    def _make_close_cb(self, pane, idx):
        return lambda: self.close_tab(idx, pane)

    def add_close_button_to(self, pane, index):
        tw = self.tabs if pane == 'left' else self.tabs_right
        close_btn = QPushButton()
        close_btn.setIcon(Icons(Tokens.FG_MUTED).close())
        close_btn.setIconSize(QSize(10, 10))
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setAccessibleName("Close tab")
        close_btn.setFlat(True)
        close_btn.clicked.connect(self._make_close_cb(pane, index))
        tw.tabBar().setTabButton(index, QTabBar.ButtonPosition(1), close_btn)

    def toggle_word_wrap(self):
        enabled = self.word_wrap_action.isChecked()
        for tw in [self.tabs, self.tabs_right]:
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab:
                    tab.editor.set_word_wrap(enabled)

    def toggle_show_whitespace(self):
        enabled = self.show_whitespace_action.isChecked()
        for tw in [self.tabs, self.tabs_right]:
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab:
                    tab.editor.set_show_whitespace(enabled)

    def toggle_show_margin(self):
        enabled = self.show_margin_action.isChecked()
        for tw in [self.tabs, self.tabs_right]:
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab:
                    tab.editor.set_show_margin(enabled)

    def _cycle_encoding(self):
        encodings = ["UTF-8", "UTF-16", "Latin-1", "CP1252"]
        current = self.config_manager.get("encoding", "UTF-8")
        idx = (encodings.index(current) + 1) % len(encodings) if current in encodings else 0
        self.config_manager.set("encoding", encodings[idx])
        self.encoding_label.setText(encodings[idx])

    def _cycle_line_ending(self):
        endings = ["LF", "CRLF", "CR"]
        current = self.config_manager.get("line_ending", "LF")
        idx = (endings.index(current) + 1) % len(endings) if current in endings else 0
        self.config_manager.set("line_ending", endings[idx])
        self.line_ending_label.setText(endings[idx])

    def _cycle_tab_width(self):
        widths = [2, 4, 8]
        current = self.config_manager.get("tab_width", 4)
        idx = (widths.index(current) + 1) % len(widths) if current in widths else 1
        self.config_manager.set("tab_width", widths[idx])
        self.tabsize_label.setText(f"Spaces: {widths[idx]}")

    def _reset_zoom(self):
        tab = self._active_tab_widget().currentWidget()
        if tab:
            tab.editor.reset_zoom()
            self.zoom_label.setText("100%")

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recent = self.config_manager.get_recent_files()
        if not recent:
            empty = QAction("(No recent files)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)
            return
        for path in recent:
            action = QAction(path, self)
            action.triggered.connect(lambda checked, p=path: self.open_file(p))
            self.recent_menu.addAction(action)
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent)
        self.recent_menu.addAction(clear_action)

    def _clear_recent(self):
        self.config_manager.clear_recent_files()
        self._update_recent_menu()

    def _create_menu(self):
        menubar = self.menuBar()
        
        ico = Icons(Tokens.ICON_STROKE)
        
        # Clear existing menus if any (for reloading)
        for action in menubar.actions():
            menubar.removeAction(action)
            
        file_menu = menubar.addMenu("&File")

        # New
        new_action = QAction("&New", self)
        new_action.setIcon(ico.file_alt())
        new_action.setShortcut(QKeySequence(self.config_manager.get_binding("new_file")))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open
        open_action = QAction("&Open", self)
        open_action.setIcon(ico.folder_open())
        open_action.setShortcut(QKeySequence(self.config_manager.get_binding("open_file")))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Save
        save_action = QAction("&Save", self)
        save_action.setIcon(ico.save())
        save_action.setShortcut(QKeySequence(self.config_manager.get_binding("save_file")))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setIcon(ico.copy())
        save_as_action.setShortcut(QKeySequence(self.config_manager.get_binding("save_as")))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Close
        close_action = QAction("&Close Tab", self)
        close_action.setIcon(ico.close())
        close_action.setShortcut(QKeySequence(self.config_manager.get_binding("close_tab")))
        close_action.triggered.connect(self.close_tab_action)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        # Recent Files
        self.recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_menu()

        edit_menu = menubar.addMenu("&Edit")

        # Undo
        undo_action = QAction("&Undo", self)
        undo_action.setIcon(ico.undo())
        undo_action.setShortcut(QKeySequence(self.config_manager.get_binding("undo")))
        undo_action.triggered.connect(self.handle_undo)
        edit_menu.addAction(undo_action)

        # Redo
        redo_action = QAction("&Redo", self)
        redo_action.setIcon(ico.redo())
        redo_action.setShortcut(QKeySequence(self.config_manager.get_binding("redo")))
        redo_action.triggered.connect(self.handle_redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Find
        find_action = QAction("&Find", self)
        find_action.setIcon(ico.search())
        find_action.setShortcut(QKeySequence(self.config_manager.get_binding("find")))
        find_action.triggered.connect(self.toggle_search_panel)
        edit_menu.addAction(find_action)

        # Replace
        replace_action = QAction("&Replace", self)
        replace_action.setIcon(ico.exchange_alt())
        replace_action.setShortcut(QKeySequence(self.config_manager.get_binding("replace")))
        replace_action.triggered.connect(self.toggle_search_panel)
        edit_menu.addAction(replace_action)

        # Go to Line
        goto_line_action = QAction("Go to Line", self)
        goto_line_action.setIcon(ico.crosshairs())
        goto_line_action.setShortcut(QKeySequence(self.config_manager.get_binding("goto_line")))
        goto_line_action.triggered.connect(self.show_goto_line)
        edit_menu.addAction(goto_line_action)

        edit_menu.addSeparator()

        # Command Palette
        palette_action = QAction("&Command Palette", self)
        palette_action.setIcon(ico.terminal())
        palette_action.setShortcut(QKeySequence(self.config_manager.get_binding("command_palette")))
        palette_action.triggered.connect(self.show_command_palette)
        edit_menu.addAction(palette_action)

        # Settings
        settings_menu = menubar.addMenu("&Settings")
        keybindings_action = QAction("&Keybindings...", self)
        keybindings_action.setIcon(ico.cog())
        keybindings_action.triggered.connect(self.show_keybindings_dialog)
        settings_menu.addAction(keybindings_action)

        # View
        view_menu = menubar.addMenu("&View")

        self.word_wrap_action = QAction("Word Wrap", self)
        self.word_wrap_action.setCheckable(True)
        self.word_wrap_action.setChecked(False)
        self.word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(self.word_wrap_action)

        self.show_whitespace_action = QAction("Show Whitespace", self)
        self.show_whitespace_action.setCheckable(True)
        self.show_whitespace_action.setChecked(False)
        self.show_whitespace_action.triggered.connect(self.toggle_show_whitespace)
        view_menu.addAction(self.show_whitespace_action)

        self.show_margin_action = QAction("Show Margin Line", self)
        self.show_margin_action.setCheckable(True)
        self.show_margin_action.setChecked(True)
        self.show_margin_action.triggered.connect(self.toggle_show_margin)
        view_menu.addAction(self.show_margin_action)

        view_menu.addSeparator()

        split_action = QAction("Split Editor", self)
        split_action.setIcon(ico.columns())
        split_action.setShortcut(QKeySequence("Ctrl+\\"))
        split_action.triggered.connect(self.split_editor)
        view_menu.addAction(split_action)

        # Restore View settings from session
        session_data = self.config_manager.load_session()
        view_settings = session_data.get("view_settings", {}) if session_data else {}

        self.word_wrap_action.setChecked(view_settings.get("word_wrap", False))
        self.show_whitespace_action.setChecked(view_settings.get("show_whitespace", False))
        self.show_margin_action.setChecked(view_settings.get("show_margin", True))

    def _start_autosave_timer(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._do_autosave)
        self.autosave_timer.start(30000)  # 30 seconds

    def _do_autosave(self):
        for tw, prefix in [(self.tabs, ''), (self.tabs_right, 'right_')]:
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab and tab.is_modified():
                    try:
                        if tab.file_path:
                            tab.save_file()
                        else:
                            cache_dir = self.config_manager.get_cache_dir()
                            temp_path = os.path.join(cache_dir, f"Untitled_{prefix}{i}.txt")
                            tab.save_file(temp_path)
                    except Exception as e:
                        print(f"Autosave failed for tab {i}: {e}")

        # Cleanup old autosave files (keep max 50, or younger than 7 days)
        try:
            cache_dir = self.config_manager.get_cache_dir()
            files = sorted(cache_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[50:]:
                f.unlink(missing_ok=True)
            now = time.time()
            for f in files[:50]:
                if now - f.stat().st_mtime > 7 * 86400:
                    f.unlink(missing_ok=True)
        except Exception:
            pass

    def _save_session(self):
        session_data = {
            "tabs": [],
            "tabs_right": [],
            "current_index": self.tabs.currentIndex(),
            "geometry": {
                "pos": (self.x(), self.y()),
                "size": (self.width(), self.height())
            },
            "splitter_sizes": self.splitter.sizes(),
            "view_settings": {
                "word_wrap": self.word_wrap_action.isChecked(),
                "show_whitespace": self.show_whitespace_action.isChecked(),
                "show_margin": self.show_margin_action.isChecked(),
            }
        }

        def _collect_tab_info(tw, target):
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab:
                    tab_info = {
                        "path": tab.file_path,
                        "unsaved_content": None
                    }
                    if not tab.file_path:
                        tab_info["unsaved_content"] = tab.editor.toPlainText()
                    target.append(tab_info)

        _collect_tab_info(self.tabs, session_data["tabs"])
        _collect_tab_info(self.tabs_right, session_data["tabs_right"])
        session_data["editor_splitter_sizes"] = self.editor_splitter.sizes()

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
            seen = set()
            seen_unsaved = set()
            for tab_info in tabs:
                path = tab_info.get("path")
                unsaved_content = tab_info.get("unsaved_content")

                if path:
                    resolved = str(Path(path).resolve())
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    self.open_file(path)
                elif unsaved_content is not None:
                    content_hash = hashlib.sha256(unsaved_content.encode()[:8192]).hexdigest()
                    if content_hash in seen_unsaved:
                        continue
                    seen_unsaved.add(content_hash)
                    tab = EditorTab()
                    tab.set_theme(self.config_manager.get("theme", "lilac"))
                    index = self.tabs.addTab(tab, tab.get_title())
                    tab.editor._loading = True
                    tab.editor.setPlainText(unsaved_content)
                    tab.editor._loading = False
                    tab._is_modified = True
                    tab.editor.document().setModified(True)
                    tab.modified_changed.connect(lambda modified, tab=tab: self._update_tab_title_pane('left', self.tabs.indexOf(tab)))
                    self._update_tab_title_pane('left', index)
                    self.add_close_button_to('left', index)
        
        # Apply view settings to all restored tabs
        view_settings = session_data.get("view_settings", {}) if session_data else {}
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab:
                tab.editor.set_word_wrap(view_settings.get("word_wrap", False))
                tab.editor.set_show_whitespace(view_settings.get("show_whitespace", False))
                tab.editor.set_show_margin(view_settings.get("show_margin", True))

        current_index = session_data.get("current_index", 0)
        if current_index < self.tabs.count():
            self.tabs.setCurrentIndex(current_index)


    def new_file(self):
        tw = self._active_tab_widget()
        pane = self._active_pane
        tab = EditorTab()
        tab.set_theme(self.config_manager.get("theme", "lilac"))
        index = tw.addTab(tab, tab.get_title())
        tw.setCurrentIndex(index)
        tab.editor.set_word_wrap(self.word_wrap_action.isChecked())
        tab.editor.set_show_whitespace(self.show_whitespace_action.isChecked())
        tab.editor.set_show_margin(self.show_margin_action.isChecked())
        tab.modified_changed.connect(lambda modified, tab=tab: self._update_tab_title_pane(pane, tw.indexOf(tab)))
        self.add_close_button_to(pane, index)

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File")

        if file_path:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return

            tw = self._active_tab_widget()
            pane = self._active_pane
            resolved = Path(file_path).resolve()
            # Check if a tab with the same file path is already open
            for i in range(tw.count()):
                tab = tw.widget(i)
                if tab.file_path and Path(tab.file_path).resolve() == resolved:
                    tw.setCurrentIndex(i)
                    self.config_manager.add_recent_file(str(resolved))
                    self._update_recent_menu()
                    return

            tab = EditorTab(file_path)
            tab.set_theme(self.config_manager.get("theme", "lilac"))
            index = tw.addTab(tab, tab.get_title())
            tw.setCurrentIndex(index)
            tab.editor.set_word_wrap(self.word_wrap_action.isChecked())
            tab.editor.set_show_whitespace(self.show_whitespace_action.isChecked())
            tab.editor.set_show_margin(self.show_margin_action.isChecked())
            tab.modified_changed.connect(lambda modified, tab=tab: self._update_tab_title_pane(pane, tw.indexOf(tab)))
            self.add_close_button_to(pane, index)
            self.config_manager.add_recent_file(str(resolved))
            self._update_recent_menu()

    def make_close_handler(self, idx):
        return lambda: self.close_tab(idx, 'left')

    def add_close_button(self, index):
        self.add_close_button_to('left', index)

    def _close_tab_by_widget(self, tab):
        index = self.tabs.indexOf(tab)
        if index >= 0:
            self.close_tab(index)

    def show_save_error(self, exception, file_path):
        import errno
        error_msg = str(exception)
        
        if isinstance(exception, PermissionError):
            user_msg = f"Permission denied: You don't have rights to write to {file_path}"
        elif isinstance(exception, OSError) and exception.errno == errno.ENOSPC:
            user_msg = "Disk full: There is no space left on the device to save the file."
        elif isinstance(exception, FileNotFoundError):
            user_msg = f"File not found: The path {file_path} is invalid."
        else:
            user_msg = f"An unexpected error occurred while saving {file_path}:\n{error_msg}"
            
        QMessageBox.critical(self, "Save Error", user_msg)

    def save_file(self):

        tw = self._active_tab_widget()
        index = tw.currentIndex()
        if index < 0:
            return
        self.save_tab_by_index(index, self._active_pane)

    def save_file_as(self):
        tw = self._active_tab_widget()
        pane = self._active_pane
        current_tab = tw.currentWidget()
        if not current_tab:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As")
        if file_path:
            try:
                current_tab.save_file(file_path)
                self._update_tab_title_pane(pane, tw.currentIndex())
            except Exception as e:
                self.show_save_error(e, file_path)

    def close_tab(self, index, pane='left'):
        tw = self.tabs if pane == 'left' else self.tabs_right
        tab = tw.widget(index)
        if tab and tab.is_modified():
            ret = QMessageBox.question(
                self, "Save Changes?", 
                f"The file {tab.get_title()} has been modified. Do you want to save it?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if ret == QMessageBox.StandardButton.Save:
                if not self.save_tab_by_index(index, pane):
                    return
            elif ret == QMessageBox.StandardButton.Cancel:
                return

        tw.removeTab(index)

        if pane == 'right':
            if self.tabs_right.count() == 0:
                self.tabs_right.hide()
                ep_sizes = self.editor_splitter.sizes()
                self.editor_splitter.setSizes([ep_sizes[0] + ep_sizes[1], 0])
                self._active_pane = 'left'
        elif self.tabs.count() == 0:
            self.new_file()

    def close_tab_action(self):
        tw = self._active_tab_widget()
        self.close_tab(tw.currentIndex(), self._active_pane)

    def _move_tab(self, source_pane, source_index, target_pane, target_index):
        source_tw = self.tabs if source_pane == 'left' else self.tabs_right
        target_tw = self.tabs if target_pane == 'left' else self.tabs_right

        if source_tw is target_tw and source_index == target_index:
            return

        tab = source_tw.widget(source_index)
        if not tab:
            return

        source_tw.removeTab(source_index)

        if source_tw is target_tw and source_index < target_index:
            target_index -= 1

        target_tw.insertTab(target_index, tab, tab.get_title())
        target_tw.setCurrentIndex(target_index)

        try:
            tab.modified_changed.disconnect()
        except TypeError:
            pass
        tab.modified_changed.connect(
            lambda modified, t=tab: self._update_tab_title_pane(target_pane, target_tw.indexOf(t))
        )

        self.add_close_button_to(target_pane, target_index)

        if target_tw.count() == 1:
            self._active_pane = target_pane

        if target_pane == 'right' and self.tabs_right.isHidden():
            ep_total = sum(self.editor_splitter.sizes())
            self.tabs_right.show()
            self.editor_splitter.setSizes([ep_total // 2, ep_total // 2])

        if source_pane == 'right' and self.tabs_right.count() == 0:
            self.tabs_right.hide()
            ep_sizes = self.editor_splitter.sizes()
            self.editor_splitter.setSizes([ep_sizes[0] + ep_sizes[1], 0])
            self._active_pane = 'left'
        elif source_pane == 'left' and self.tabs.count() == 0:
            self.new_file()

    def save_tab_by_index(self, index, pane='left'):
        tw = self.tabs if pane == 'left' else self.tabs_right
        tab = tw.widget(index)
        if not tab:
            return False
        
        try:
            if tab.file_path:
                return tab.save_file()
            else:
                # Save As
                file_path, _ = QFileDialog.getSaveFileName(self, "Save File As")
                if file_path:
                    return tab.save_file(file_path)
                return False
        except Exception as e:
            self.show_save_error(e, tab.file_path or "Unknown Path")
            return False

    def update_tab_title(self, index):
        tab = self.tabs.widget(index)
        if not tab:
            return
        
        title = tab.get_title()
        
        if tab.is_modified():
            self.tabs.setTabText(index, f"● {title}")
            self.tabs.setTabIcon(index, self.status_icons["modified"])
        else:
            self.tabs.setTabText(index, title)
            self.tabs.setTabIcon(index, self.status_icons["saved"])

    def closeEvent(self, event):
        # Final autosave
        self._do_autosave()
        # Save session
        self._save_session()

        for tw, pane in [(self.tabs, 'left'), (self.tabs_right, 'right')]:
            for i in range(tw.count() - 1, -1, -1):

                tab = tw.widget(i)
                if tab and tab.is_modified():
                    ret = QMessageBox.question(
                        self, "Save Changes?", 
                        f"The file {tab.get_title()} has been modified. Do you want to save it?",
                        QMessageBox.StandardButton.Save | 
                        QMessageBox.StandardButton.Discard | 
                        QMessageBox.StandardButton.Cancel
                    )
                    if ret == QMessageBox.StandardButton.Save:
                        if not self.save_tab_by_index(i, pane):
                            event.ignore()
                            return
                    elif ret == QMessageBox.StandardButton.Cancel:
                        event.ignore()
                        return
        event.accept()

    def handle_undo(self):
        tab = self._active_tab_widget().currentWidget()
        if tab:
            tab.editor.undo()

    def handle_redo(self):
        tab = self._active_tab_widget().currentWidget()
        if tab:
            tab.editor.redo()

    def toggle_search_panel(self):
        if self.search_panel.maximumHeight() > 0:
            current_tab = self._active_tab_widget().currentWidget()
            if current_tab:
                current_tab.editor.clear_search_highlights()
        if not hasattr(self, '_search_anim') or self._search_anim is None:
            self._search_anim = QPropertyAnimation(self.search_panel, b"maximumHeight")
            self._search_anim.setDuration(200)
            self._search_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._search_anim.stop()
        if self.search_panel.maximumHeight() > 0:
            self._search_anim.setStartValue(self.search_panel.maximumHeight())
            self._search_anim.setEndValue(0)
        else:
            self._search_anim.setStartValue(0)
            self._search_anim.setEndValue(150)
        self._search_anim.start()

    def show_command_palette(self):
        self.command_palette.show()

    def show_keybindings_dialog(self):
        dialog = KeybindingsDialog(self.config_manager, self)
        if dialog.exec():
            self._create_menu()

    def handle_find(self, text, case_sensitive, is_regex, forward=True):
        current_tab = self._active_tab_widget().currentWidget()
        if not current_tab or not text:
            return False

        editor = current_tab.editor
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        # Update match count
        content = editor.toPlainText()
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        try:
            if is_regex:
                matches = list(re.finditer(text, content, flags=regex_flags))[:1000]
            else:
                matches = list(re.finditer(re.escape(text), content, flags=regex_flags))[:1000]
        except re.error:
            self.search_panel.set_error()
            return False

        total = len(matches)
        current = 0
        cursor_pos = editor.textCursor().selectionStart()
        for m in matches:
            if m.end() <= cursor_pos:
                current += 1

        self.search_panel.set_match_count(current + 1 if total > 0 else 0, total)

        # Highlight all matches
        match_color = QColor("#A885FF")
        match_color.setAlpha(60)
        match_selections = []
        for m in matches:
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(match_color)
            sel.cursor = editor.textCursor()
            sel.cursor.setPosition(m.start())
            sel.cursor.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            match_selections.append(sel)
        editor.set_search_highlights(match_selections)

        if not is_regex:
            if forward:
                if editor.find(text, flags):
                    return True
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                editor.setTextCursor(cursor)
                return editor.find(text, flags)
            else:
                flags |= QTextDocument.FindFlag.FindBackward
                if editor.find(text, flags):
                    return True
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                editor.setTextCursor(cursor)
                return editor.find(text, flags)
        else:
            # Regex find implementation
            if forward:
                cursor = editor.textCursor()
                search_start = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
                match = re.search(text, content[search_start:], flags=regex_flags)
                if match:
                    match_start = search_start + match.start()
                    match_end = search_start + match.end()
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
        current_tab = self._active_tab_widget().currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        cursor = editor.textCursor()

        if cursor.hasSelection():
            sel = cursor.selectedText()
            if is_regex:
                regex_flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    match = bool(re.fullmatch(search_text, sel, flags=regex_flags))
                except re.error:
                    match = False
            else:
                match = sel == search_text if case_sensitive else sel.lower() == search_text.lower()
            if match:
                cursor.insertText(replace_text)
                self.handle_find(search_text, case_sensitive, is_regex)
                return

        if self.handle_find(search_text, case_sensitive, is_regex):
            cursor = editor.textCursor()
            cursor.insertText(replace_text)
            editor.setTextCursor(cursor)

    def handle_replace_all(self, search_text, replace_text, case_sensitive, is_regex):
        current_tab = self._active_tab_widget().currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        content = editor.toPlainText()

        regex_flags = 0 if case_sensitive else re.IGNORECASE
        try:
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
        except re.error:
            self.search_panel.set_error()
            return

        if new_content != content:
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(new_content)
            cursor.endEditBlock()
            editor.clear_search_highlights()

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
        if self.goto_panel.isVisible():
            self.hide_goto_line()
            self.setFocus()
            return
        self.goto_panel.show()
        self.goto_panel.input.setFocus()
        self.goto_panel.input.clear()

    def hide_goto_line(self):
        self.goto_panel.hide()

    def handle_goto_line(self, line_number):
        current_tab = self._active_tab_widget().currentWidget()
        if current_tab:
            max_lines = current_tab.editor.document().blockCount()
            if 1 <= line_number <= max_lines:
                current_tab.editor.go_to_line(line_number)
            else:
                self.goto_panel.set_error()
