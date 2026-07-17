from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
from theme_tokens import Tokens
from icon_utils import Icons
from qss_tokens import apply_shadow

t = Tokens

class CommandPalette(QDialog):
    actionTriggered = pyqtSignal(str)

    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.all_actions = actions

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setObjectName("command_palette")
        self.setFixedWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        apply_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("command_search_input")
        self.search_input.setPlaceholderText("Search actions...")
        self.search_input.setAccessibleName("Search actions")
        self.search_input.textChanged.connect(self.filter_actions)
        self.search_input.returnPressed.connect(self.on_enter_pressed)
        search_icon = Icons(t.ICON_ACTIVE).search()
        self.search_input.addAction(QAction(search_icon, "", self),
                                    QLineEdit.ActionPosition.LeadingPosition)
        layout.addWidget(self.search_input)

        self.action_list = QListWidget()
        self.action_list.setObjectName("command_action_list")
        self.action_list.setAccessibleName("Available actions")
        self.action_list.itemDoubleClicked.connect(self.on_action_selected)
        layout.addWidget(self.action_list)

        self.update_list("")

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
        elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if self.action_list.count() > 0:
                cur = self.action_list.currentRow()
                delta = 1 if event.key() == Qt.Key.Key_Down else -1
                self.action_list.setCurrentRow((cur + delta) % self.action_list.count())
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.on_enter_pressed()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        parent = self.parent()
        if parent and parent.isWidgetType() and parent.isVisible():
            parent_geo = parent.geometry()
            x = parent_geo.center().x() - self.width() // 2
            y = (parent_geo.height() // 3) - (self.height() // 2)
            y = max(parent_geo.top() + 20, y)
            self.move(x, y)
        else:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            if screen:
                sg = screen.availableGeometry()
                x = sg.center().x() - self.width() // 2
                y = sg.height() // 3 - self.height() // 2
                y = max(sg.top() + 20, y)
                self.move(x, y)


