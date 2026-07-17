from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QInputDialog, QFileDialog
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt
from icon_utils import Icons
from theme_tokens import Tokens
import os
import shutil

class FileTree(QWidget):
    fileOpened = pyqtSignal(str)
    fileCreated = pyqtSignal(str)
    folderCreated = pyqtSignal(str)

    def __init__(self, initial_path=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # File Tree
        self.current_root = os.path.realpath(initial_path or os.getcwd())
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_custom_context_menu)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.layout.addWidget(self.tree)

        # Initialize population
        self._populate(self.current_root)

    def _file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        ico = Icons(Tokens.ICON_STROKE)
        if ext in ('.py', '.pyw'):
            return ico.file_code()
        if ext in ('.js', '.ts', '.jsx', '.tsx'):
            return ico.file_code()
        if ext in ('.c', '.cpp', '.h', '.hpp', '.rs', '.go'):
            return ico.file_code()
        return ico.file()

    def on_browse_folder(self):
        new_path = QFileDialog.getExistingDirectory(self, "Select Root Folder", self.current_root)
        if new_path:
            self.set_root_path(new_path)

    def set_root_path(self, path):
        real_path = os.path.realpath(path)
        if os.path.exists(real_path) and os.path.isdir(real_path):
            self.current_root = real_path
            self._populate(self.current_root)

    def _populate(self, path):
        self.tree.clear()
        
        # 1. Parent Directory item ".."
        parent_path = os.path.dirname(path)
        if parent_path != path:
            parent_item = QTreeWidgetItem(self.tree, [".."])
            parent_item.setIcon(0, Icons(Tokens.ICON_STROKE).folder())
            font = parent_item.font(0)
            font.setItalic(True)
            parent_item.setFont(0, font)
            parent_item.setForeground(0, QColor("#B7A8D9"))
            parent_item.setData(0, Qt.ItemDataRole.UserRole, "PARENT")
        
        # 2. Immediate contents only
        self._add_items(self.tree, path)

    def _add_items(self, parent_item, path, _visited=None):
        try:
            entries = os.listdir(path)
        except PermissionError:
            return

        if _visited is None:
            _visited = set()
        real_path = os.path.realpath(path)
        _visited.add(real_path)

        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                real = os.path.realpath(full_path)
                if os.path.islink(full_path) and real in _visited:
                    continue
                dirs.append(entry)
            else:
                files.append(entry)
        
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)
        
        # Add directories - lazy population, collapsible
        dir_items = []
        ico = Icons(Tokens.ICON_STROKE)
        for d in dirs:
            full_path = os.path.join(path, d)
            item = QTreeWidgetItem([d])
            item.setIcon(0, ico.folder())
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
            QTreeWidgetItem(item, ["..."])
            dir_items.append(item)
        self._add_batch(parent_item, dir_items)
            
        # Add files
        file_items = []
        for f in files:
            full_path = os.path.join(path, f)
            item = QTreeWidgetItem([f])
            item.setIcon(0, self._file_icon(f))
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            file_items.append(item)
        self._add_batch(parent_item, file_items)

    def _add_batch(self, parent, items):
        if isinstance(parent, QTreeWidget):
            parent.addTopLevelItems(items)
        else:
            parent.addChildren(items)

    def _on_item_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isdir(path):
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def _on_item_expanded(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or path == "PARENT":
            return
        
        if os.path.isdir(path):
            item.setIcon(0, Icons(Tokens.ICON_STROKE).folder_open())
            
            populated = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if not populated:
                while item.childCount() > 0:
                    item.removeChild(item.child(0))
                self._add_items(item, path)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, True)

    def _on_item_collapsed(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or path == "PARENT":
            return
        
        if os.path.isdir(path):
            item.setIcon(0, Icons(Tokens.ICON_STROKE).folder())
            item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
            while item.childCount() > 0:
                item.removeChild(item.child(0))
            QTreeWidgetItem(item, ["..."])

    def _on_item_double_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        
        if path == "PARENT":
            self.set_root_path(os.path.dirname(self.current_root))
        elif os.path.isdir(path):
            pass
        else:
            resolved = os.path.realpath(path)
            if not resolved.startswith(os.path.realpath(self.current_root) + os.sep) and resolved != os.path.realpath(self.current_root):
                QMessageBox.warning(self, "Security", "Cannot open file outside workspace root.")
                return
            self.fileOpened.emit(path)

    def on_custom_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu()

        # Common actions
        new_file_action = menu.addAction("New File")
        new_folder_action = menu.addAction("New Folder")
        menu.addSeparator()

        open_action = None
        rename_action = None
        delete_action = None

        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path != "PARENT":
                open_action = menu.addAction("Open")
                rename_action = menu.addAction("Rename")
                delete_action = menu.addAction("Delete")
                
                if os.path.isdir(path):
                    open_action.setText("Open Folder")
        
        action = menu.exec(self.tree.mapToGlobal(position))
        
        if action == new_file_action:
            self._create_new_item(False)
        elif action == new_folder_action:
            self._create_new_item(True)
        elif item and item.data(0, Qt.ItemDataRole.UserRole) != "PARENT":
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if action == open_action:
                self._on_item_double_clicked(item, 0)
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
            new_name = os.path.basename(new_name)
            if not new_name:
                return
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            if os.path.exists(new_path):
                res = QMessageBox.question(
                    self, "Overwrite?",
                    f"{new_name} already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if res != QMessageBox.StandardButton.Yes:
                    return
            try:
                shutil.move(old_path, new_path)
                self._populate(self.current_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename: {e}")

    def _delete_item(self, item, path):
        name = os.path.basename(path)
        msg = f"Are you sure you want to delete {name}?"
        if os.path.isdir(path):
            try:
                entries = os.listdir(path)
                if entries:
                    msg += f"\n\nThis folder is not empty ({len(entries)} items)."
            except PermissionError:
                pass
        res = QMessageBox.question(self, "Delete", msg,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            try:
                if os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._populate(self.current_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
