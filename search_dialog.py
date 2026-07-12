from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt

class SearchPanel(QWidget):
    # Signals to communicate with the main window
    find_next_requested = pyqtSignal(str, bool, bool)
    find_prev_requested = pyqtSignal(str, bool, bool)
    replace_requested = pyqtSignal(str, str, bool, bool)
    replace_all_requested = pyqtSignal(str, str, bool, bool)
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("search_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Search row
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(8)
        
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        inputs_layout.addWidget(self.find_input)
        
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")
        inputs_layout.addWidget(self.replace_input)
        
        layout.addLayout(inputs_layout)

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(8)
        
        self.case_sensitive = QPushButton("Aa")
        self.case_sensitive.setCheckable(True)
        self.case_sensitive.setFixedWidth(28)
        
        self.is_regex = QPushButton(".*")
        self.is_regex.setCheckable(True)
        self.is_regex.setFixedWidth(28)
        
        self.match_count_label = QLabel("0 of 0")
        self.match_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.is_regex)
        options_layout.addStretch()
        options_layout.addWidget(self.match_count_label)
        
        layout.addLayout(options_layout)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.find_prev_btn = QPushButton("Find Prev ↑")
        self.find_next_btn = QPushButton("Find Next ↓")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedWidth(28)
        
        self.find_prev_btn.clicked.connect(self.on_find_prev)
        self.find_next_btn.clicked.connect(self.on_find_next)
        self.replace_btn.clicked.connect(self.on_replace)
        self.replace_all_btn.clicked.connect(self.on_replace_all)
        self.close_btn.clicked.connect(lambda: self.close_requested.emit())
        
        btn_layout.addWidget(self.find_prev_btn)
        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def set_match_count(self, current, total):
        self.match_count_label.setText(f"{current} of {total}")

    def on_find_next(self):
        self.find_next_requested.emit(
            self.find_input.text(), 
            self.case_sensitive.isChecked(), 
            self.is_regex.isChecked()
        )

    def on_find_prev(self):
        self.find_prev_requested.emit(
            self.find_input.text(), 
            self.case_sensitive.isChecked(), 
            self.is_regex.isChecked()
        )

    def on_replace(self):
        self.replace_requested.emit(
            self.find_input.text(),
            self.replace_input.text(),
            self.case_sensitive.isChecked(),
            self.is_regex.isChecked()
        )

    def on_replace_all(self):
        self.replace_all_requested.emit(
            self.find_input.text(),
            self.replace_input.text(),
            self.case_sensitive.isChecked(),
            self.is_regex.isChecked()
        )
