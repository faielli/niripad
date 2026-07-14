from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QAction
from theme_tokens import Tokens
from icon_utils import Icons

t = Tokens

class CommandPalette(QDialog):
    actionTriggered = pyqtSignal(str)

    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.all_actions = actions

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search actions...")
        self.search_input.setAccessibleName("Search actions")
        self.search_input.textChanged.connect(self.filter_actions)
        self.search_input.returnPressed.connect(self.on_enter_pressed)
        search_icon = Icons(t.ICON_STROKE).search()
        self.search_input.addAction(QAction(search_icon, "", self),
                                    QLineEdit.ActionPosition.LeadingPosition)
        layout.addWidget(self.search_input)

        self.action_list = QListWidget()
        self.action_list.setAccessibleName("Available actions")
        self.action_list.itemDoubleClicked.connect(self.on_action_selected)
        layout.addWidget(self.action_list)

        self.update_list("")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t.BG_PANEL.name()};
                border: 1px solid {t.ACCENT.name()};
                border-radius: {t.RADIUS_LG}px;
            }}
            QLineEdit {{
                background-color: transparent;
                border: none;
                font-size: 14px;
                padding: {t.SPACE[3]}px {t.SPACE[4]}px;
                color: {t.FG_PRIMARY.name()};
                border-bottom: 1px solid {t.BORDER_SUBTLE.name()};
                font-family: {t.FONT_UI};
                min-height: 44px;
            }}
            QLineEdit:focus {{
                background-color: {t.BG_SURFACE.name()};
            }}
            QListWidget {{
                background-color: transparent;
                border: none;
                padding: {t.SPACE[1]}px;
                outline: 0;
                font-family: {t.FONT_UI};
                font-size: {t.FONT_SIZE_UI}px;
            }}
            QListWidget::item {{
                padding: {t.SPACE[3]}px {t.SPACE[4]}px;
                color: {t.FG_SECONDARY.name()};
                font-size: {t.FONT_SIZE_UI}px;
                border-radius: {t.RADIUS_MD}px;
                margin: {t.SPACE[1]}px {t.SPACE[1]}px;
                min-height: 44px;
            }}
            QListWidget::item:selected {{
                background-color: {t.ACCENT_PRESS.name()};
                color: {t.FG_PRIMARY.name()};
            }}
            QListWidget::item:hover {{
                background-color: {t.BG_SURFACE.name()};
                color: {t.FG_PRIMARY.name()};
            }}
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
            if self.action_list.count() > 0:
                self.action_list.setCurrentRow((self.action_list.currentRow() + 1) % self.action_list.count())
        elif event.key() == Qt.Key.Key_Up:
            if self.action_list.count() > 0:
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


