import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QMessageBox, 
    QMenu, QMenuBar
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt
from editor_tab import EditorTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Niri Editor")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self._create_menu()
        
        # Initial tab
        self.new_file()

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        # New
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Save
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Close
        close_action = QAction("&Close Tab", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close_tab_action)
        file_menu.addAction(close_action)

    def new_file(self):
        tab = EditorTab()
        index = self.tabs.addTab(tab, tab.get_title())
        self.tabs.setCurrentIndex(index)
        tab.modified_changed.connect(lambda: self.update_tab_title(index))

    def open_file(self):
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
