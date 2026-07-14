from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor
from theme_tokens import Tokens
from icon_utils import Icons
from qss_tokens import apply_shadow

t = Tokens
ico = Icons(t.ICON_STROKE)

class SearchPanel(QWidget):
    find_next_requested = pyqtSignal(str, bool, bool)
    find_prev_requested = pyqtSignal(str, bool, bool)
    replace_requested = pyqtSignal(str, str, bool, bool)
    replace_all_requested = pyqtSignal(str, str, bool, bool)
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("search_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SPACE[2], t.SPACE[2], t.SPACE[2], t.SPACE[2])
        layout.setSpacing(t.SPACE[2])
        
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(t.SPACE[2])
        
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.find_input.setAccessibleName("Find")
        inputs_layout.addWidget(self.find_input)
        
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")
        self.replace_input.setAccessibleName("Replace")
        inputs_layout.addWidget(self.replace_input)
        
        layout.addLayout(inputs_layout)
        
        options_layout = QHBoxLayout()
        options_layout.setSpacing(t.SPACE[2])
        
        self.case_sensitive = QPushButton("Aa")
        self.case_sensitive.setCheckable(True)
        self.case_sensitive.setFixedSize(44, 44)
        self.case_sensitive.setAccessibleName("Case sensitive")
        apply_shadow(self.case_sensitive)
        
        self.is_regex = QPushButton(".*")
        self.is_regex.setCheckable(True)
        self.is_regex.setFixedSize(44, 44)
        self.is_regex.setAccessibleName("Use regular expression")
        apply_shadow(self.is_regex)
        
        self.match_count_label = QLabel("0 of 0")
        self.match_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.is_regex)
        options_layout.addStretch()
        options_layout.addWidget(self.match_count_label)
        
        layout.addLayout(options_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(t.SPACE[2])
        
        self.find_prev_btn = QPushButton()
        self.find_prev_btn.setIcon(ico.chevron_up())
        self.find_prev_btn.setToolTip("Find Previous (Shift+Enter)")
        self.find_prev_btn.setAccessibleName("Find previous")
        self.find_prev_btn.setFixedSize(44, 44)
        
        self.find_next_btn = QPushButton()
        self.find_next_btn.setIcon(ico.chevron_down())
        self.find_next_btn.setToolTip("Find Next (Enter)")
        self.find_next_btn.setAccessibleName("Find next")
        self.find_next_btn.setFixedSize(44, 44)
        
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setAccessibleName("Replace")
        self.replace_btn.setFixedHeight(44)
        
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setAccessibleName("Replace all")
        self.replace_all_btn.setFixedHeight(44)
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(ico.close())
        self.close_btn.setFixedSize(44, 44)
        self.close_btn.setAccessibleName("Close search")
        self.close_btn.setToolTip("Close search (Escape)")
        
        self.find_prev_btn.clicked.connect(self.on_find_prev)
        self.find_next_btn.clicked.connect(self.on_find_next)
        self.replace_btn.clicked.connect(self.on_replace)
        self.replace_all_btn.clicked.connect(self.on_replace_all)
        self.close_btn.clicked.connect(lambda: self.close_requested.emit())
        
        for btn in (self.find_prev_btn, self.find_next_btn, self.replace_btn,
                    self.replace_all_btn, self.close_btn):
            apply_shadow(btn)
        
        btn_layout.addWidget(self.find_prev_btn)
        btn_layout.addWidget(self.find_next_btn)
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.replace_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setStyleSheet(f"""
            #search_panel {{
                border-top: 1px solid {t.BORDER_SUBTLE.name()};
            }}
            #search_panel QLineEdit {{
                background-color: {t.BG_APP.name()};
                border: 1px solid {t.BORDER_SUBTLE.name()};
                border-radius: {t.RADIUS_MD}px;
                color: {t.FG_PRIMARY.name()};
                padding: {t.SPACE[2]}px {t.SPACE[3]}px;
                min-height: 44px;
            }}
            #search_panel QLineEdit:focus {{
                border: 1px solid {t.BORDER_FOCUS.name()};
                background-color: {t.BG_SURFACE.name()};
            }}
            #search_panel QPushButton {{
                background-color: {t.BG_APP.name()};
                color: {t.FG_SECONDARY.name()};
                border: 1px solid {t.BORDER_SUBTLE.name()};
                border-radius: {t.RADIUS_MD}px;
                padding: {t.SPACE[2]}px {t.SPACE[3]}px;
                min-height: 44px;
            }}
            #search_panel QPushButton:hover {{
                background-color: {t.BG_SURFACE.name()};
                border-color: {t.ACCENT.name()};
                color: {t.ACCENT_HOVER.name()};
            }}
            #search_panel QPushButton:pressed {{
                background-color: {t.ACCENT_PRESS.name()};
                border-color: {t.ACCENT.name()};
            }}
            #search_panel QPushButton:checked {{
                border-color: {t.ACCENT.name()};
                color: {t.ACCENT_HOVER.name()};
                background-color: {t.ACCENT_PRESS.name()};
            }}
            #search_panel QLabel {{
                color: {t.FG_MUTED.name()};
                font-size: {t.FONT_SIZE_UI - 2}px;
            }}
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

        self._normal_style = f"""
            #goto_line_panel QLineEdit {{
                background-color: {t.BG_APP.name()};
                border: 1px solid {t.BORDER_FOCUS.name()};
                border-radius: {t.RADIUS_MD}px;
                color: {t.FG_PRIMARY.name()};
                padding: {t.SPACE[2]}px {t.SPACE[3]}px;
                font-family: {t.FONT_MONO};
                min-height: 44px;
            }}
            #goto_line_panel QLineEdit:focus {{
                border: 1px solid {t.BORDER_FOCUS.name()};
                background-color: {t.BG_SURFACE.name()};
            }}
        """

        self._error_style = f"""
            #goto_line_panel QLineEdit {{
                background-color: {t.BG_APP.name()};
                border: 1px solid {t.DANGER.name()};
                border-radius: {t.RADIUS_MD}px;
                color: {t.FG_PRIMARY.name()};
                padding: {t.SPACE[2]}px {t.SPACE[3]}px;
                font-family: {t.FONT_MONO};
                min-height: 44px;
            }}
        """

        layout = QHBoxLayout(self)
        layout.setContentsMargins(t.SPACE[2], t.SPACE[1], t.SPACE[2], t.SPACE[1])
        layout.setSpacing(t.SPACE[2])

        self.input = QLineEdit()
        self.input.setPlaceholderText("Go to line...")
        self.input.setFixedWidth(240)
        self.input.setStyleSheet(self._normal_style)
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
        self.input.setStyleSheet(self._error_style)
        QTimer.singleShot(1000, self.reset_style)

    def reset_style(self):
        self.input.setStyleSheet(self._normal_style)
