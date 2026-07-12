from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QLineEdit, QHBoxLayout, QLabel
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import pyqtSignal, QDir
import os

class FileTree(QWidget):
    fileOpened = pyqtSignal(str)

    def __init__(self, initial_path=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Path Bar
        self.path_layout = QHBoxLayout()
        self.path_label = QLabel("Path:")
        self.path_input = QLineEdit()
        self.path_input.returnPressed.connect(self.on_path_enter)
        
        self.path_layout.addWidget(self.path_label)
        self.path_layout.addWidget(self.path_input)
        self.layout.addLayout(self.path_layout)

        # Tree View
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        
        # Start with the provided path or current dir
        self.current_root = os.path.abspath(initial_path or os.getcwd())
        self.model.setRootPath(self.current_root)
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.current_root))
        
        # Hide unnecessary columns
        self.tree.setColumnHidden(1, True) # Size
        self.tree.setColumnHidden(2, True) # Type
        self.tree.setColumnHidden(3, True) # Date Modified
        
        self.tree.setAnimated(True)
        self.tree.setIndentation(15)
        self.tree.setSortingEnabled(True)
        self.tree.doubleClicked.connect(self.on_double_clicked)
        
        self.layout.addWidget(self.tree)
        
        # Set initial path text
        self.path_input.setText(self.current_root)

    def on_path_enter(self):
        path = self.path_input.text()
        if os.path.isdir(path):
            self.set_root_path(path)
        else:
            print(f"Invalid directory: {path}")

    def set_root_path(self, path):
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            self.current_root = abs_path
            self.model.setRootPath(self.current_root)
            self.tree.setRootIndex(self.model.index(self.current_root))
            self.path_input.setText(self.current_root)

    def on_double_clicked(self, index):
        file_path = self.model.filePath(index)
        if self.model.isDir(index):
            self.set_root_path(file_path)
        else:
            self.fileOpened.emit(file_path)
