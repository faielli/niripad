import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QLineEdit, QPushButton, QLabel,
    QApplication
)
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QPoint
from PyQt6.QtGui import QFont, QTextCursor
from theme_tokens import Tokens
from icon_utils import Icons

logger = logging.getLogger(__name__)


class ResizeHandle(QWidget):
    def __init__(self, terminal):
        super().__init__(terminal)
        self.setObjectName("terminal_resize_handle")
        self.setFixedHeight(4)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self._terminal = terminal
        self._press_y = None

    def mousePressEvent(self, event):
        self._press_y = event.globalPosition().y()

    def mouseMoveEvent(self, event):
        if self._press_y is None:
            return
        delta = event.globalPosition().y() - self._press_y
        new_h = max(80, min(600, self._terminal.height() + delta))
        self._terminal.setFixedHeight(new_h)
        self._press_y = event.globalPosition().y()

    def mouseReleaseEvent(self, event):
        self._press_y = None


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminal_widget")
        self._process = None
        self._cwd = os.getcwd()
        self._history = []
        self._history_index = -1
        self.setFixedHeight(200)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Resize handle
        self._resize_handle = ResizeHandle(self)
        layout.addWidget(self._resize_handle)

        # Header bar
        header = QWidget()
        header.setObjectName("terminal_header")
        header.setFixedHeight(28)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 4, 0)
        header_layout.setSpacing(4)

        self._cwd_label = QLabel(self._cwd)
        self._cwd_label.setObjectName("terminal_cwd")
        header_layout.addWidget(self._cwd_label)
        header_layout.addStretch()

        icons = Icons(Tokens.ICON_ACTIVE)
        clear_btn = QPushButton()
        clear_btn.setIcon(icons.file_alt())
        clear_btn.setToolTip("Clear output")
        clear_btn.setFlat(True)
        clear_btn.setFixedSize(24, 24)
        clear_btn.clicked.connect(self.clear_output)
        header_layout.addWidget(clear_btn)

        kill_btn = QPushButton()
        kill_btn.setIcon(icons.close())
        kill_btn.setToolTip("Kill process")
        kill_btn.setFlat(True)
        kill_btn.setFixedSize(24, 24)
        kill_btn.clicked.connect(self.kill_process)
        header_layout.addWidget(kill_btn)

        layout.addWidget(header)

        # Output area
        mono_size = Tokens.FONT_SIZE_MONO - 1
        font = QFont(Tokens.FONT_MONO.split(",")[0].strip("'"))
        font.setPointSize(mono_size)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumBlockCount(2000)
        self._output.setFont(font)
        self._output.setStyleSheet(
            f"background-color: {Tokens.BG_DEEP.name()}; color: {Tokens.FG_PRIMARY.name()}; border: none;"
        )
        self._output.installEventFilter(self)
        layout.addWidget(self._output)

        # Input bar
        input_bar = QWidget()
        input_bar.setObjectName("terminal_input_bar")
        input_bar.setFixedHeight(32)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(8, 0, 8, 0)
        input_layout.setSpacing(4)

        prompt = QLabel("$")
        prompt.setObjectName("terminal_prompt")
        prompt.setFixedWidth(12)
        prompt.setFont(font)
        input_layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setObjectName("terminal_input")
        self._input.setFont(font)
        self._input.returnPressed.connect(self._run_command)
        self._input.installEventFilter(self)
        input_layout.addWidget(self._input)

        layout.addWidget(input_bar)

    def set_cwd(self, path):
        if os.path.isdir(path):
            self._cwd = path
        elif os.path.isfile(path):
            self._cwd = os.path.dirname(path)
        else:
            return
        self._cwd_label.setText(self._cwd)

    def focus_input(self):
        self._input.setFocus()

    def clear_output(self):
        self._output.clear()

    def kill_process(self):
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._append("\n[Process killed]\n")

    def _append(self, text):
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _run_command(self):
        cmd = self._input.text().strip()
        if not cmd:
            return
        self._history.append(cmd)
        self._history_index = len(self._history)
        self._input.clear()

        if cmd.startswith("cd"):
            parts = cmd.split(None, 1)
            target = parts[1].strip() if len(parts) > 1 else os.path.expanduser("~")
            target = os.path.realpath(
                os.path.join(self._cwd, os.path.expandvars(os.path.expanduser(target))))
            if os.path.isdir(target):
                self._cwd = target
                self._cwd_label.setText(self._cwd)
                self._append(f"$ {cmd}\n")
            else:
                self._append(f"$ {cmd}\ncd: {target}: No such directory\n")
            return

        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._append("[A process is already running. Kill it first.]\n")
            return

        self._append(f"$ {cmd}\n")
        self._process = QProcess(self)
        self._process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self._process.setWorkingDirectory(self._cwd)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        self._process.start("/bin/bash", ["-c", cmd])

    def _on_stdout(self):
        data = self._process.readAllStandardOutput().data()
        self._append(data.decode("utf-8", errors="replace"))

    def _on_stderr(self):
        data = self._process.readAllStandardError().data()
        self._append(data.decode("utf-8", errors="replace"))

    def _on_finished(self, exit_code, exit_status):
        self._append(f"[exited with code {exit_code}]\n")

    def _on_error(self, error):
        self._append(f"[QProcess error: {error}]\n")

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier

            if obj is self._input and ctrl and not shift and event.key() == Qt.Key.Key_C:
                if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
                    self._process.kill()
                    self._append("^C\n")
                return True

            if obj is self._input and not event.modifiers():
                if event.key() == Qt.Key.Key_Up:
                    if self._history:
                        self._history_index = max(0, self._history_index - 1)
                        self._input.setText(self._history[self._history_index])
                    return True
                if event.key() == Qt.Key.Key_Down:
                    if self._history:
                        self._history_index = min(len(self._history), self._history_index + 1)
                        if self._history_index == len(self._history):
                            self._input.clear()
                        else:
                            self._input.setText(self._history[self._history_index])
                    return True

            if obj is self._input and ctrl and shift and event.key() == Qt.Key.Key_V:
                text = QApplication.clipboard().text()
                if text:
                    self._input.insert(text)
                return True

            if obj is self._output:
                if ctrl and not shift and event.key() == Qt.Key.Key_C:
                    if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
                        self._process.kill()
                        self._append("^C\n")
                        return True
                    cursor = self._output.textCursor()
                    if cursor.hasSelection():
                        QApplication.clipboard().setText(cursor.selectedText())
                    return True
                if ctrl and shift and event.key() == Qt.Key.Key_C:
                    cursor = self._output.textCursor()
                    if cursor.hasSelection():
                        QApplication.clipboard().setText(cursor.selectedText())
                    return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.kill_process()
        super().closeEvent(event)
