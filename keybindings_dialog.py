from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from config_manager import ConfigManager
from theme_tokens import Tokens
from qss_tokens import apply_shadow

t = Tokens

class KeybindingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setObjectName("keybindings_dialog")
        self.setWindowTitle("Keybindings Configuration")
        self.setMinimumWidth(420)
        self.setMinimumHeight(400)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(t.SPACE[3])
        self.layout.setContentsMargins(t.SPACE[4], t.SPACE[4], t.SPACE[4], t.SPACE[4])

        self.label = QLabel("Double click an item to change its shortcut (e.g., 'Ctrl+O', 'Ctrl+S').")
        self.layout.addWidget(self.label)

        self.list_widget = QListWidget()
        self.list_widget.setAccessibleName("Keyboard shortcuts list")
        self.list_widget.itemDoubleClicked.connect(self.edit_binding)
        self.layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(t.SPACE[2])
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        apply_shadow(self.save_btn)
        apply_shadow(self.cancel_btn)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        # QSS applied globally from qss_tokens.keybindings_dialog_qss()

        self.load_bindings_into_list()

    def load_bindings_into_list(self):
        self.list_widget.clear()
        self.bindings = self.config_manager.keybindings.copy()
        for action_id, shortcut in self.bindings.items():
            item = QListWidgetItem(f"{action_id}: {shortcut}")
            item.setData(Qt.ItemDataRole.UserRole, action_id)
            self.list_widget.addItem(item)

    def edit_binding(self, item):
        action_id = item.data(Qt.ItemDataRole.UserRole)
        current_shortcut = self.bindings[action_id]

        # Simple input dialog for the new shortcut
        from PyQt6.QtWidgets import QInputDialog
        new_shortcut, ok = QInputDialog.getText(self, "Change Shortcut", f"New shortcut for {action_id}:", text=current_shortcut)

        if ok and new_shortcut:
            self.bindings[action_id] = new_shortcut
            item.setText(f"{action_id}: {new_shortcut}")

    def save_and_close(self):
        # Save back to config manager
        self.config_manager.keybindings = self.bindings.copy()
        self.config_manager.save_keybindings()
        
        # We need to signal the main window to reload shortcuts
        # We can use a custom signal or just emit a signal if we pass it
        self.accept()

    def reject(self):
        super().reject()
