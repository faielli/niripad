from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QLineEdit, QHBoxLayout, QLabel, QMenu, QMessageBox, 
    QInputDialog, QApplication, QPushButton, QFileDialog, QStyle
)
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import pyqtSignal, QDir, Qt
import os
import shutil

FILETREE_QSS = """
QListWidget {
    background-color: #252A33;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 4px 16px;
    color: #8892a0;
    border-left: 2px solid transparent;
    border-radius: 0px;
}
QListWidget::item:hover {
    background-color: #3B4252;
    color: #D8DEE9;
    border-left-color: #88C0D0;
}
QListWidget::item:selected {
    background-color: #434C5E;
    color: #D8DEE9;
    border-left-color: #88C0D0;
}
"""

class FileTree(QWidget):
    fileOpened = pyqtSignal(str)
    fileCreated = pyqtSignal(str)
    folderCreated = pyqtSignal(str)

    def __init__(self, initial_path=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Path Bar - Folder Selection Button
        self.path_layout = QHBoxLayout()
        self.folder_btn = QPushButton()
        self.folder_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.folder_btn.setFixedWidth(32)
        self.folder_btn.clicked.connect(self.on_browse_folder)
        
        self.path_layout.addWidget(self.folder_btn)
        self.path_layout.addStretch()
        self.layout.addLayout(self.path_layout)

        # File List
        self.current_root = os.path.abspath(initial_path or os.getcwd())
        self.list = QListWidget()
        self.list.setStyleSheet(FILETREE_QSS)
        self.list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.on_custom_context_menu)
        self.layout.addWidget(self.list)

        # Initialize population
        self._populate(self.current_root)

    def on_browse_folder(self):
        new_path = QFileDialog.getExistingDirectory(self, "Select Root Folder", self.current_root)
        if new_path:
            self.set_root_path(new_path)

    def set_root_path(self, path):
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            self.current_root = abs_path
            self._populate(self.current_root)

    def _populate(self, path):
        self.list.clear()
        
        # 1. Parent Directory item ".."
        parent_path = os.path.dirname(path)
        if parent_path != path: # Avoid infinite loop at root
            parent_item = QListWidgetItem("..")
            parent_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent))
            font = parent_item.font()
            font.setItalic(True)
            parent_item.setFont(font)
            parent_item.setForeground(QColor("#4C566A"))
            parent_item.setData(Qt.ItemDataRole.UserRole, "PARENT")
            self.list.addItem(parent_item)

        try:
            entries = os.listdir(path)
        except PermissionError:
            # Handle directories we can't read
            return

        # 2. Separate directories and files
        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)

        # Sort case-insensitive
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        # Add directories
        for d in dirs:
            item = QListWidgetItem(d)
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            item.setData(Qt.ItemDataRole.UserRole, os.path.join(path, d))
            self.list.addItem(item)

        # Add files
        for f in files:
            item = QListWidgetItem(f)
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            item.setData(Qt.ItemDataRole.UserRole, os.path.join(path, f))
            self.list.addItem(item)

    def _on_item_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        
        if path == "PARENT":
            self.set_root_path(os.path.dirname(self.current_root))
        elif os.path.isdir(path):
            self.set_root_path(path)
        else:
            self.fileOpened.emit(path)

    def on_custom_context_menu(self, position):
        item = self.list.itemAt(position)
        menu = QMenu()

        # Common actions
        new_file_action = menu.addAction("New File")
        new_folder_action = menu.addAction("New Folder")
        menu.addSeparator()

        open_action = None
        rename_action = None
        delete_action = None

        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path != "PARENT":
                open_action = menu.addAction("Open")
                rename_action = menu.addAction("Rename")
                delete_action = menu.addAction("Delete")
                
                if os.path.isdir(path):
                    open_action.setText("Open Folder")
        
        action = menu.exec(self.list.mapToGlobal(position))
        
        if action == new_file_action:
            self._create_new_item(False)
        elif action == new_folder_action:
            self._create_new_item(True)
        elif item and item.data(Qt.ItemDataRole.UserRole) != "PARENT":
            path = item.data(Qt.ItemDataRole.UserRole)
            if action == open_action:
                self._on_item_double_clicked(item)
            elif action == rename_action:
                self._rename_item(item, path)
            elif action == delete_action:
                self._delete_item(item, path)

    def _create_new_item(self, is_folder):
        name, ok = QInputDialog.getText(self, "New " + ("Folder" if is_folder else "File"), "Name:")
        if ok and name:
            full_path = os.path.join(self.current_root, name)
            try:
                if is_folder:
                    os.makedirs(full_path, exist_ok=True)
                    self.folderCreated.emit(full_path)
                else:
                    with open(full_path, 'w') as f:
                        pass
                    self.fileCreated.emit(full_path)
                self._populate(self.current_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create item: {e}")

    def _rename_item(self, item, old_path):
        current_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=current_name)
        if ok and new_name and new_name != current_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self._populate(self.current_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename: {e}")

    def _delete_item(self, item, path):
        name = os.path.basename(path)
        res = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {name}?", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._populate(self.current_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")

# Note: Import QColor in the top if used. Correcting imports now.
