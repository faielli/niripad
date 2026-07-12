from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QCheckBox, QLabel, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal, Qt

class SearchReplaceDialog(QDialog):
    # Signals to communicate with the main window
    find_requested = pyqtSignal(str, bool, bool)  # text, case_sensitive, is_regex
    replace_requested = pyqtSignal(str, str, bool, bool) # search_text, replace_text, case_sensitive, is_regex
    replace_all_requested = pyqtSignal(str, str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search & Replace")
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)

        # Search row
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Find:"))
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Replace row
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)

        # Options row
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Case Sensitive")
        self.is_regex = QCheckBox("Use Regular Expressions")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.is_regex)
        layout.addLayout(options_layout)

        # Buttons row
        btn_layout = QHBoxLayout()
        self.find_btn = QPushButton("Find Next")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")
        
        self.find_btn.clicked.connect(self.on_find)
        self.replace_btn.clicked.connect(self.on_replace)
        self.replace_all_btn.clicked.connect(self.on_replace_all)
        
        btn_layout.addWidget(self.find_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        layout.addLayout(btn_layout)

        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)

    def on_find(self):
        self.find_requested.emit(
            self.search_input.text(), 
            self.case_sensitive.isChecked(), 
            self.is_regex.isChecked()
        )

    def on_replace(self):
        self.replace_requested.emit(
            self.search_input.text(),
            self.replace_input.text(),
            self.case_sensitive.isChecked(),
            self.is_regex.isChecked()
        )

    def on_replace_all(self):
        self.replace_all_requested.emit(
            self.search_input.text(),
            self.replace_input.text(),
            self.case_sensitive.isChecked(),
            self.is_regex.isChecked()
        )
