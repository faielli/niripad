from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QInputDialog, QFileDialog, QStyle
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt
import os
import shutil

FILETREE_QSS = """
QTreeWidget {
    background-color: #252A33;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QTreeWidget::item {
    padding: 4px 8px;
    color: #8892a0;
    border-radius: 4px;
}
QTreeWidget::item:hover {
    background-color: #2E3440;
    color: #D8DEE9;
}
QTreeWidget::item:selected {
    background-color: #3B4252;
    color: #ECEFF4;
}
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url(none);
    border-image: none;
}
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url(none);
    border-image: none;
}
QTreeView::branch {
    background: #2E3440;
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

        # File Tree
        self.current_root = os.path.abspath(initial_path or os.getcwd())
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)
        self.tree.setStyleSheet(FILETREE_QSS)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_custom_context_menu)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.layout.addWidget(self.tree)

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
        self.tree.clear()
        
        # 1. Parent Directory item ".."
        parent_path = os.path.dirname(path)
        if parent_path != path:
            parent_item = QTreeWidgetItem(self.tree, [".."])
            parent_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent))
            font = parent_item.font(0)
            font.setItalic(True)
            parent_item.setFont(0, font)
            parent_item.setForeground(0, QColor("#4C566A"))
            parent_item.setData(0, Qt.ItemDataRole.UserRole, "PARENT")
        
        # 2. Immediate contents only
        self._add_items(self.tree, path)

    def _add_items(self, parent_item, path):
        try:
            entries = os.listdir(path)
        except PermissionError:
            return
        
        # Separate and sort
        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)
        
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)
        
        # Add directories - lazy population, collapsible
        for d in dirs:
            full_path = os.path.join(path, d)
            item = QTreeWidgetItem(parent_item, [d])
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirClosedIcon))
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, False)  # not yet populated
            QTreeWidgetItem(item, ["..."])  # placeholder to show expand arrow
            
        # Add files
        for f in files:
            full_path = os.path.join(path, f)
            item = QTreeWidgetItem(parent_item, [f])
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)

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
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
            
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
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirClosedIcon))

    def _on_item_double_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if path == "PARENT":
            self.set_root_path(os.path.dirname(self.current_root))
        elif os.path.isdir(path):
            # Let the single-click expand, double-click could also open in a new root if desired
            # but requested behavior is just double-click open file
            pass
        else:
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
            if path != "PARENT":
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
