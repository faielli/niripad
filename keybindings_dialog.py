from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from config_manager import ConfigManager

class KeybindingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Keybindings Configuration")
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Double click an item to change its shortcut (e.g., 'Ctrl+O', 'Ctrl+S').")
        self.layout.addWidget(self.label)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.edit_binding)
        self.layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        # Apply Nord styling to the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF7FE;
                color: #3C2E56;
                font-family: 'Quicksand', 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #3C2E56;
                font-size: 13px;
                margin-bottom: 10px;
            }
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #E1D3F5;
                border-radius: 10px;
                color: #3C2E56;
                font-size: 13px;
                outline: 0;
                padding: 4px;
            }
            QListWidget::item {
                padding: 7px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #E4D4F7;
                color: #7C4DEF;
            }
            QPushButton {
                background-color: #F2EAFC;
                color: #3C2E56;
                border: 1px solid #E1D3F5;
                border-radius: 10px;
                padding: 6px 15px;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F1E6FC;
                border-color: #8B5CF6;
            }
            QPushButton:pressed {
                background-color: #E4D4F7;
            }
        """)

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
