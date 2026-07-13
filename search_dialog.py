from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor

class SearchPanel(QWidget):
... (existing SearchPanel code) ...

class SearchPanel(QWidget):
... (existing SearchPanel code) ...

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
        
        self.setStyleSheet("""
            #search_panel {
                border-top: 1px solid #3B4252;
            }
            QLineEdit {
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 4px;
                color: #D8DEE9;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #88C0D0;
            }
            QPushButton {
                background-color: #3B4252;
                color: #D8DEE9;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #434C5E;
            }
            QLabel {
                color: #4C566A;
            }
        """)

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

class GoToLinePanel(QWidget):
    goto_requested = pyqtSignal(int)
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("goto_line_panel")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Go to line...")
        self.input.setFixedWidth(200)
        self.input.setStyleSheet("""
            #goto_line_panel QLineEdit {
                background-color: #3B4252;
                border: 1px solid #88C0D0;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 4px;
                font-family: 'JetBrains Mono', monospace;
            }
            #goto_line_panel QLineEdit:focus {
                border: 1px solid #88C0D0;
            }
        """)
        self.input.returnPressed.connect(self._on_enter)
        self.input.installEventFilter(self)
        
        layout.addWidget(self.input)
        layout.addStretch()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close_requested.emit()
                return True
        return super().eventFilter(obj, event)

    def _on_enter(self):
        try:
            line_number = int(self.input.text())
            if line_number > 0:
                self.goto_requested.emit(line_number)
                self.close_requested.emit()
            else:
                self.set_error()
        except ValueError:
            self.set_error()

    def set_error(self):
        self.input.setStyleSheet(self.input.styleSheet() + "border: 1px solid #BF616A;")
        QTimer.singleShot(1000, self.reset_style)

    def reset_style(self):
        self.input.setStyleSheet("""
            #goto_line_panel QLineEdit {
                background-color: #3B4252;
                border: 1px solid #88C0D0;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 4px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
