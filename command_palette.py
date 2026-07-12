from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

class CommandPalette(QDialog):
    actionTriggered = pyqtSignal(str)

    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.all_actions = actions # Dict {id: description}
        
        # Window configuration
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search actions...")
        self.search_input.textChanged.connect(self.filter_actions)
        self.search_input.returnPressed.connect(self.on_enter_pressed)
        layout.addWidget(self.search_input)
        
        self.action_list = QListWidget()
        self.action_list.itemDoubleClicked.connect(self.on_action_selected)
        layout.addWidget(self.action_list)
        
        self.update_list("")
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2E3440;
                border: 1px solid #4C566A;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: transparent;
                border: none;
                font-size: 14px;
                padding: 10px 14px;
                color: #D8DEE9;
                border-bottom: 1px solid #3B4252;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 4px 0;
                outline: 0;
            }
            QListWidget::item {
                padding: 8px 14px;
                color: #8892a0;
                font-size: 12px;
                border-radius: 4px;
                margin: 1px 4px;
            }
            QListWidget::item:selected, QListWidget::item:hover {
                background-color: #3B4252;
                color: #D8DEE9;
            }
        """)

    def update_list(self, filter_text):
        self.action_list.clear()
        filter_text = filter_text.lower()
        for action_id, description in self.all_actions.items():
            if filter_text in description.lower() or filter_text in action_id.lower():
                item = QListWidgetItem(description)
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

    def showEvent(self, event):
        super().showEvent(event)
        if self.parentWidget():
            parent_geo = self.parentWidget().geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                (parent_geo.height() // 3) - (self.height() // 2)
            )


