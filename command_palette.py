from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPalette, QColor

class CommandPalette(QDialog):
    actionTriggered = pyqtSignal(str)

    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.all_actions = actions # Dict {id: description}
        self.setWindowTitle("Command Palette")
        self.setFixedWidth(500)
        self.setMinimumHeight(300)
        
        # Removed FramelessWindowHint for better visibility and standard behavior
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search actions...")
        self.search_input.textChanged.connect(self.filter_actions)
        layout.addWidget(self.search_input)

        self.action_list = QListWidget()
        self.action_list.itemDoubleClicked.connect(self.on_action_selected)
        layout.addWidget(self.action_list)

        # Handle Enter key
        self.search_input.returnPressed.connect(self.on_enter_pressed)

        self.update_list("")

    def update_list(self, filter_text):
        self.action_list.clear()
        filter_text = filter_text.lower()
        
        for action_id, description in self.all_actions.items():
            if filter_text in description.lower() or filter_text in action_id.lower():
                item = QListWidgetItem(f"{description} ({action_id})")
                item.setData(Qt.ItemDataRole.UserRole, action_id)
                self.action_list.addItem(item)
        
        if self.action_list.count() > 0:
            self.action_list.setCurrentRow(0)

    def filter_actions(self, text):
        self.update_list(text)

    def on_enter_pressed(self):
        if self.action_list.currentItem():
            self.on_action_selected(self.action_list.currentItem())

    def on_action_selected(self, item):
        if item:
            action_id = item.data(Qt.ItemDataRole.UserRole)
            self.actionTriggered.emit(action_id)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            self.action_list.setCurrentRow((self.action_list.currentRow() + 1) % self.action_list.count())
        elif event.key() == Qt.Key.Key_Up:
            self.action_list.setCurrentRow((self.action_list.currentRow() - 1) % self.action_list.count())
        else:
            super().keyPressEvent(event)
