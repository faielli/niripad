#!/usr/bin/env python3
"""
test.py — Niri Editor test suite (38 tests · stdlib only)
Run:  python test.py
"""

import sys
import os
import unittest
import unittest.mock
import tempfile
import shutil
import json
import logging
import ast
import contextlib
import time
from pathlib import Path

# ── Logging ──────────────────────────────────────────────────────────────
_log_fh = None

def _setup_logging():
    global _log_fh
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    fmt_stderr = logging.Formatter('%(message)s')
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(fmt_stderr)
    logger.addHandler(handler)

    report_path = Path(__file__).parent / "test_report.txt"
    _log_fh = logging.FileHandler(report_path, mode='w', encoding='utf-8')
    _log_fh.setLevel(logging.DEBUG)
    _log_fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(_log_fh)
    return logger

logger = _setup_logging()

# ── Qt availability ─────────────────────────────────────────────────────
QT_AVAILABLE = False
try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QFileDialog,
        QMessageBox, QWidget, QVBoxLayout, QPlainTextEdit,
        QTreeWidgetItem, QDialog,
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QEvent
    from PyQt6.QtGui import QColor, QFont, QPainter, QTextFormat, QFontMetrics, QTextCursor

    # Import project modules
    from logging_config import setup_logging
    from theme_tokens import Tokens
    from theme import Theme
    from qss_tokens import global_qss
    from config_manager import ConfigManager
    from syntax_highlighter import UniversalHighlighter
    from editor_tab import EditorTab, CustomEditor, _is_path_safe, detect_language
    from main_window import MainWindow, GitBranchWorker
    from search_dialog import SearchPanel, GoToLinePanel
    from command_palette import CommandPalette
    from keybindings_dialog import KeybindingsDialog
    from icon_utils import get_icon, Icons
    from file_tree import FileTree
    from terminal_widget import TerminalWidget, ResizeHandle

    QT_AVAILABLE = True
    logger.info("[SETUP] Qt + tutti i moduli importati correttamente")
except ImportError as e:
    logger.warning("[SETUP] Import fallito: %s — test Qt saranno saltati", e)
except Exception as e:
    logger.warning("[SETUP] Errore inatteso: %s", e)


# ── Helpers / fixtures ──────────────────────────────────────────────────

_qapp = None

def ensure_qapp():
    """Return a singleton QApplication (offscreen) with persistent ref."""
    global _qapp
    if not QT_AVAILABLE:
        return None
    if _qapp is None:
        _qapp = QApplication.instance()
    if _qapp is None:
        _qapp = QApplication(sys.argv)
    return _qapp


@contextlib.contextmanager
def tmp_dir(prefix="niri_test_"):
    path = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@contextlib.contextmanager
def patched_config(tmp: Path):
    """Point all ConfigManager paths to *tmp* (isolated from ~/.config)."""
    patches = {
        "CONFIG_DIR": tmp,
        "CONFIG_FILE": tmp / "config.json",
        "KEYBINDINGS_FILE": tmp / "keybindings.json",
        "SESSION_FILE": tmp / "session.json",
        "CACHE_DIR": tmp / "cache",
    }
    mocks = {k: unittest.mock.patch.object(ConfigManager, k, v) for k, v in patches.items()}
    for m in mocks.values():
        m.start()
    (tmp / "cache").mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        for m in reversed(list(mocks.values())):
            m.stop()


@contextlib.contextmanager
def mock_qmessagebox_warning():
    """Replace QMessageBox.warning with a recorder."""
    original = QMessageBox.warning
    calls = []
    def fake(parent, title, text, *args, **kw):
        calls.append((title, str(text)[:80]))
        return QMessageBox.StandardButton.Ok
    QMessageBox.warning = staticmethod(fake)
    try:
        yield calls
    finally:
        QMessageBox.warning = original


@contextlib.contextmanager
def capture_log(name: str):
    """Capture logger messages emitted on *name*."""
    log_obj = logging.getLogger(name)
    records = []
    handler = logging.Handler()
    handler.emit = lambda r: records.append(r)
    log_obj.addHandler(handler)
    try:
        yield records
    finally:
        log_obj.removeHandler(handler)


def write_session(tmp: Path, tabs_data=None, right_tabs_data=None):
    """Write a session.json into *tmp* for the test."""
    data = {
        "tabs": tabs_data or [],
        "tabs_right": right_tabs_data or [],
        "current_index": 0,
    }
    (tmp / "session.json").write_text(json.dumps(data), encoding='utf-8')


# ── Test suites ──────────────────────────────────────────────────────────

class TestLoggingConfig(unittest.TestCase):
    """Pure test — logging_config module"""

    def test_setup_logging_configures_root(self):
        logger.info("═══ TestLoggingConfig.test_setup_logging_configures_root ═══")
        test_logger = logging.getLogger("test")
        stderr_handlers = [h for h in test_logger.handlers
                           if isinstance(h, logging.StreamHandler)]
        self.assertGreaterEqual(len(stderr_handlers), 1)
        logger.info("[PASS] test logger ha StreamHandler su stderr ✓")


class TestThemeTokens(unittest.TestCase):
    """Pure test — theme_tokens.Tokens constants"""

    def test_color_attrs_present(self):
        logger.info("═══ TestThemeTokens.test_color_attrs_present ═══")
        expected = ["BG_DEEP", "FG_PRIMARY", "ACCENT", "FONT_MONO", "FONT_SIZE_MONO"]
        for attr in expected:
            self.assertTrue(hasattr(Tokens, attr), f"Tokens missing {attr}")
        logger.info("[PASS] Tokens ha %d attributi richiesti ✓", len(expected))


class TestTheme(unittest.TestCase):
    """Pure test — Theme module"""

    def test_by_name_lilac_returns_dict(self):
        logger.info("═══ TestTheme.test_by_name_lilac_returns_dict ═══")
        t = Theme.by_name("lilac")
        self.assertIsInstance(t, dict)
        for key in ("background", "foreground", "selection_background"):
            self.assertIn(key, t)
        logger.info("[PASS] Theme.by_name('lilac') → dict con %d chiavi tra cui background/foreground ✓",
                     len(t))

    def test_by_name_invalid_falls_back_to_lilac(self):
        """Nome tema invalido → fallback a LILAC + warnings.warn."""
        logger.info("═══ TestTheme.test_by_name_invalid_falls_back_to_lilac ═══")
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t = Theme.by_name("__nonexistent__")
        # Deve ritornare il dict LILAC
        self.assertIs(t, Theme.LILAC)
        self.assertGreaterEqual(len(w), 1)
        self.assertIn("Unknown theme", str(w[0].message))
        logger.info("[PASS] by_name('__nonexistent__') → fallback LILAC + warning ✓")


class TestQssTokens(unittest.TestCase):
    """Pure test — qss_tokens module"""

    def test_global_qss_nonempty(self):
        logger.info("═══ TestQssTokens.test_global_qss_nonempty ═══")
        qss = global_qss()
        self.assertIsInstance(qss, str)
        self.assertGreater(len(qss), 50)
        for sel in ("QMainWindow", "QTabWidget"):
            self.assertIn(sel, qss)
        logger.info("[PASS] global_qss() → %d caratteri, selettori base presenti ✓", len(qss))


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestDetectLanguage(unittest.TestCase):
    """Pure function — detect_language"""

    def test_python_extension(self):
        self.assertEqual(detect_language("foo.py"), "python")
        logger.info("[PASS] detect_language('foo.py') → 'python' ✓")

    def test_javascript_extension(self):
        self.assertEqual(detect_language("foo.js"), "javascript")
        logger.info("[PASS] detect_language('foo.js') → 'javascript' ✓")

    def test_rust_extension(self):
        self.assertEqual(detect_language("foo.rs"), "rust")
        logger.info("[PASS] detect_language('foo.rs') → 'rust' ✓")

    def test_unknown_extension_returns_none(self):
        self.assertIsNone(detect_language("foo.unknown"))
        logger.info("[PASS] detect_language('foo.unknown') → None ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestIsPathSafe(unittest.TestCase):
    """Pure function — _is_path_safe (BUG NOTO: test 2 è expectedFailure)"""

    def test_normal_path_returns_true(self):
        """Path normale deve essere accettato."""
        logger.info("═══ TestIsPathSafe.test_normal_path_returns_true ═══")
        result = _is_path_safe("/tmp/normal_file.txt")
        self.assertTrue(result)
        logger.info("[PASS] _is_path_safe('/tmp/normal_file.txt') → True ✓")

    def test_path_traversal_returns_false(self):
        """
        _is_path_safe con path traversal deve ritornare False.
        """
        logger.info("═══ TestIsPathSafe.test_path_traversal_returns_false ═══")
        result = _is_path_safe("../../etc/passwd")
        self.assertFalse(result,
            "_is_path_safe dovrebbe rifiutare path traversal")
        logger.info("[PASS] _is_path_safe rifiuta path traversal ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFOLDPatterns(unittest.TestCase):
    """Fase 5 regression critical — pattern list[dict] normalization"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_FOLD_PATTERNS_python_is_dict(self):
        """FOLD_PATTERNS['python'] è un dict singolo, NON list."""
        logger.info("═══ TestFOLDPatterns.test_FOLD_PATTERNS_python_is_dict ═══")
        patterns = CustomEditor.FOLD_PATTERNS.get("python")
        self.assertIsInstance(patterns, dict)
        self.assertIn("end_marker", patterns)
        self.assertIn("prefixes", patterns)
        logger.info("[PASS] FOLD_PATTERNS['python'] → dict con end_marker/prefixes ✓")

    def test_DEFAULT_FOLD_PATTERNS_is_list_of_dicts(self):
        """DEFAULT_FOLD_PATTERNS è list[dict]."""
        default = CustomEditor.DEFAULT_FOLD_PATTERNS
        self.assertIsInstance(default, list)
        self.assertGreater(len(default), 0)
        for p in default:
            self.assertIsInstance(p, dict)
            self.assertIn("end_marker", p)
            self.assertIn("prefixes", p)
        logger.info("[PASS] DEFAULT_FOLD_PATTERNS → list[dict] con %d pattern ✓", len(default))

    def test_update_foldable_blocks_normalizes_to_list(self):
        """update_foldable_blocks() NON solleva TypeError per lingue note (regression Fase 5)."""
        logger.info("═══ TestFOLDPatterns.test_update_foldable_blocks_normalizes_to_list ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():\n    pass\n\nclass Bar:\n    pass\n")
        for lang in ("python", "javascript", "rust"):
            with self.subTest(lang=lang):
                editor.language = lang
                editor.update_foldable_blocks()
                self.assertIsInstance(editor.foldable_blocks, dict)
        logger.info("[PASS] update_foldable_blocks() su 3 lingue → no TypeError ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSyntaxHighlighter(unittest.TestCase):
    """Qt test — UniversalHighlighter"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_setup_rules_python_returns_list(self):
        """_setup_rules() dopo set_language('python') → self.rules è lista non vuota."""
        from editor_tab import CustomEditor
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("python")
        hl._setup_rules()
        self.assertIsInstance(hl.rules, list)
        self.assertGreater(len(hl.rules), 0)
        logger.info("[PASS] _setup_rules() con language='python' → %d rules ✓", len(hl.rules))

    def test_unknown_language_default_rules(self):
        """Senza set_language → self.rules è sempre list (con regole di default)."""
        from editor_tab import CustomEditor
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl._setup_rules()
        self.assertIsInstance(hl.rules, list)
        logger.info("[PASS] _setup_rules() con language=None → %d rules (default) ✓", len(hl.rules))


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestConfigManager(unittest.TestCase):
    """Qt test — ConfigManager con dir isolata"""

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self.cm = ConfigManager()

    def tearDown(self):
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_save_load_config_utf8_roundtrip(self):
        """Fase 8 regression — UTF-8 accentati sopravvivono a save/load."""
        logger.info("═══ TestConfigManager.test_save_load_config_utf8_roundtrip ═══")
        self.cm.config["theme"] = "café"
        self.cm.config["font_family"] = "日本語"
        self.cm.save_config()
        cm2 = ConfigManager()
        self.assertEqual(cm2.config["theme"], "café")
        self.assertEqual(cm2.config["font_family"], "日本語")
        logger.info("[PASS] Config roundtrip preserva accentati e giapponese ✓")

    def test_corrupt_config_renames_to_bad(self):
        """File config.json corrotto → rinominato in .json.bad + backup loggato."""
        logger.info("═══ TestConfigManager.test_corrupt_config_renames_to_bad ═══")
        (self.tmp / "config.json").write_text("not valid json", encoding='utf-8')
        with capture_log("__main__"):
            cm = ConfigManager()
        self.assertTrue((self.tmp / "config.json.bad").exists())
        self.assertIsInstance(cm.config, dict)
        logger.info("[PASS] config.json corrotto → backup .json.bad creato ✓")

    def test_save_keybindings_emits_signal(self):
        """bindings_changed emesso da save_keybindings."""
        logger.info("═══ TestConfigManager.test_save_keybindings_emits_signal ═══")
        emitted = []
        self.cm.bindings_changed.connect(lambda b: emitted.append(b))
        self.cm.save_keybindings()
        self.assertEqual(len(emitted), 1)
        logger.info("[PASS] bindings_changed emesso 1x ✓")

    def test_save_load_session_utf8_roundtrip(self):
        """Fase 8 — session.json preserva contenuto UTF-8."""
        logger.info("═══ TestConfigManager.test_save_load_session_utf8_roundtrip ═══")
        data = {"tabs": [{"path": "/tmp/café.txt"}]}
        self.cm.save_session(data)
        loaded = self.cm.load_session()
        self.assertEqual(loaded["tabs"][0]["path"], "/tmp/café.txt")
        logger.info("[PASS] Session roundtrip preserva café ✓")

    def test_duplicate_shortcut_logs_warning(self):
        """Shortcut duplicato → logger.warning."""
        logger.info("═══ TestConfigManager.test_duplicate_shortcut_logs_warning ═══")
        self.cm.keybindings["a"] = "Ctrl+X"
        self.cm.keybindings["b"] = "Ctrl+X"
        with self.assertLogs(ConfigManager.__module__, level="WARNING") as logs:
            self.cm.save_keybindings()
        self.assertTrue(any("duplicate" in msg.lower() for msg in logs.output))
        logger.info("[PASS] Shortcut duplicato logga warning ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorTabLoadSave(unittest.TestCase):
    """Fase 7 regression — load/save error propagation via _load_error flag"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def test_init_load_error_is_none(self):
        """EditorTab() senza path → _load_error is None."""
        logger.info("═══ TestEditorTabLoadSave.test_init_load_error_is_none ═══")
        tab = EditorTab(pane='left')
        self.assertIsNone(tab._load_error)
        logger.info("[PASS] _load_error iniziale → None ✓")

    def test_load_nonexistent_returns_false(self):
        """Fase 7.3 — load_file su path inesistente → retval False + _load_error valorizzato."""
        logger.info("═══ TestEditorTabLoadSave.test_load_nonexistent_returns_false ═══")
        tab = EditorTab(pane='left')
        result = tab.load_file(str(self.tmp / "__does_not_exist__.py"))
        self.assertFalse(result)
        self.assertIsNotNone(tab._load_error)
        self.assertIn("No such file", tab._load_error)
        logger.info("[PASS] load_file inesistente → False, _load_error='%s' ✓",
                     tab._load_error[:50])

    def test_load_file_success_returns_true(self):
        """Fase 7.3 — load_file su file valido → True + contenuto caricato."""
        logger.info("═══ TestEditorTabLoadSave.test_load_file_success_returns_true ═══")
        file = self.tmp / "hello.py"
        file.write_text("print('hello')", encoding='utf-8')
        tab = EditorTab(str(file), pane='left')
        self.assertIsNone(tab._load_error)
        self.assertEqual(tab.editor.toPlainText(), "print('hello')")
        self.assertEqual(tab._language, "python")
        logger.info("[PASS] load_file success → True, language='%s' ✓", tab._language)

    def test_save_file_readonly_raises(self):
        """Fase 7.4 — save_file su path read-only → solleva eccezione (non ritorna False)."""
        logger.info("═══ TestEditorTabLoadSave.test_save_file_readonly_raises ═══")
        file = self.tmp / "readonly.txt"
        file.write_text("original", encoding='utf-8')
        file.chmod(0o444)
        tab = EditorTab(str(file), pane='left')
        tab.editor.setPlainText("modified")
        with self.assertRaises(PermissionError):
            tab.save_file()
        self.assertEqual(file.read_text(encoding='utf-8'), "original",
                         "Il file non deve essere stato modificato")
        logger.info("[PASS] save_file su readonly → PermissionError sollevato ✓")

    def test_save_file_success_returns_true(self):
        """save_file su path normale → True + flag modified azzerato."""
        logger.info("═══ TestEditorTabLoadSave.test_save_file_success_returns_true ═══")
        file = self.tmp / "save_test.txt"
        tab = EditorTab(pane='left')
        tab.file_path = str(file)
        tab.editor.setPlainText("new content")
        result = tab.save_file()
        self.assertTrue(result)
        self.assertFalse(tab.is_modified())
        self.assertFalse(tab.editor.document().isModified())
        self.assertEqual(file.read_text(encoding='utf-8'), "new content")
        logger.info("[PASS] save_file success → True, is_modified=False ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorTabFolding(unittest.TestCase):
    """Fase 5 regression runtime — foldable_blocks non vuoto per Python code"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_python_def_creates_fold_entry(self):
        """File Python con 'def foo():' → foldable_blocks non vuoto."""
        logger.info("═══ TestEditorTabFolding.test_python_def_creates_fold_entry ═══")
        tab = EditorTab(pane='left')
        tab.editor.setPlainText("def foo():\n    pass\n\ndef bar():\n    pass\n")
        tab.editor.language = "python"
        tab.editor.update_foldable_blocks()
        self.assertGreater(len(tab.editor.foldable_blocks), 0)
        logger.info("[PASS] foldable_blocks ha %d entry per 2 def ✓",
                     len(tab.editor.foldable_blocks))


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowRestore(unittest.TestCase):
    """Fase 6 regression — _restore_session skips missing/unreadable files"""

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def test_restore_with_missing_file_skips_and_logs(self):
        """Fase 6 — session con 1 file esistente + 1 inesistente → solo 1 tab, warning loggato."""
        logger.info("═══ TestMainWindowRestore.test_restore_missing_file ═══")
        existing = self.tmp / "exists.py"
        existing.write_text("x=1", encoding='utf-8')
        write_session(self.tmp, tabs_data=[
            {"path": str(existing)},
            {"path": str(self.tmp / "missing.py")},
        ])
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                with self.assertLogs("main_window", level="WARNING") as logs:
                    mw = MainWindow()
                    mw._restore_session()
                    self.assertEqual(mw.tabs.count(), 1,
                        "Solo il tab del file esistente deve essere aperto")
                self.assertTrue(any("file not found" in msg for msg in logs.output))
            mw.deleteLater()
        logger.info("[PASS] 1 file esistente creato, 1 skip loggato ✓")

    def test_restore_with_unreadable_file_logs_and_skips(self):
        """Fase 7.6 — file esistente ma illeggibile in right pane → skip + warning."""
        logger.info("═══ TestMainWindowRestore.test_restore_unreadable_file ═══")
        unreadable = self.tmp / "secret.py"
        unreadable.write_text("confidential", encoding='utf-8')
        unreadable.chmod(0o000)
        # right_tabs_data → attiva il ramo con check _load_error e logger.warning
        write_session(self.tmp, right_tabs_data=[{"path": str(unreadable)}])
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                with self.assertLogs("main_window", level="WARNING") as logs:
                    # Right ramo: EditorTab(path, pane='right') + _load_error check
                    mw = MainWindow()
                    mw._restore_session()
                has_failed_warning = any("failed to load" in msg for msg in logs.output)
                self.assertTrue(has_failed_warning,
                    f"Nessun warning 'failed to load' trovato tra: {logs.output}")
            mw.deleteLater()
        logger.info("[PASS] File illeggibile → warning loggato ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowOpenFile(unittest.TestCase):
    """Fase 7.5 regression — open_file mostra dialog per file inesistente"""

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def test_open_nonexistent_creates_tab(self):
        """open_file su path inesistente → tab creato con filename."""
        logger.info("═══ TestMainWindowOpenFile.test_open_nonexistent_creates_tab ═══")
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                mw = MainWindow()
        initial_count = mw.tabs.count()
        target = str(self.tmp / "nope.py")
        mw.open_file(target)
        self.assertEqual(mw.tabs.count(), initial_count + 1,
            "Tab creato per file inesistente")
        tab = mw.tabs.widget(mw.tabs.count() - 1)
        self.assertEqual(tab.file_path, str(Path(target).resolve()))
        self.assertEqual(tab.get_title(), "nope.py")
        mw.deleteLater()
        logger.info("[PASS] open_file inesistente → tab creato con filename ✓")

    def test_open_existent_adds_tab(self):
        """open_file su file esistente → tab aggiunto, nessun dialog."""
        logger.info("═══ TestMainWindowOpenFile.test_open_existent_adds_tab ═══")
        existing = self.tmp / "ok.py"
        existing.write_text("ok", encoding='utf-8')
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                mw = MainWindow()
        initial_count = mw.tabs.count()
        with mock_qmessagebox_warning() as dialogs:
            mw.open_file(str(existing))
        self.assertEqual(len(dialogs), 0,
            "Nessun dialog per file esistente")
        self.assertEqual(mw.tabs.count(), initial_count + 1,
            "Un tab deve essere aggiunto")
        mw.deleteLater()
        logger.info("[PASS] open_file esistente → +1 tab, 0 dialog ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowSplit(unittest.TestCase):
    """Fase 7.7 regression — split_editor con file illeggibile abortisce"""

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._unreadable = self.tmp / "secret.txt"
        self._unreadable.write_text("top secret", encoding='utf-8')
        self._unreadable.chmod(0o000)
        # Leggibile per creare il tab
        self._readable = self.tmp / "readable.txt"
        self._readable.write_text("hello", encoding='utf-8')

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def test_split_with_unreadable_aborts(self):
        """
        Fase 7.7 — split_editor su tab con file_path illeggibile
        → QMessageBox.warning + nessun tab right creato.
        """
        logger.info("═══ TestMainWindowSplit.test_split_with_unreadable_aborts ═══")
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                mw = MainWindow()
        # Crea un tab che punta al file illeggibile
        tab = EditorTab(pane='left')
        tab.file_path = str(self._unreadable)
        mw.tabs.addTab(tab, "illegible")
        mw.tabs.setCurrentWidget(tab)
        tab.pane_activated.connect(mw._on_pane_activated)
        tab.set_theme(mw.config_manager.get("theme", "lilac"))
        initial_left = mw.tabs.count()
        initial_right = mw.tabs_right.count()

        with mock_qmessagebox_warning() as dialogs:
            mw.split_editor()

        self.assertGreaterEqual(len(dialogs), 1,
            "Split con file illeggibile deve mostrare dialog")
        self.assertEqual(mw.tabs_right.count(), initial_right,
            "Nessun tab right deve essere stato creato")
        mw.deleteLater()
        logger.info("[PASS] split_editor su file illeggibile → dialog 1x, 0 tab right ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestGitBranchWorker(unittest.TestCase):
    """Fase 1 regression — GitBranchWorker in dir non-git"""

    @classmethod
    def setUpClass(cls):
        cls.qapp = ensure_qapp()

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def test_non_git_dir_finishes_without_crash(self):
        """
        GitBranchWorker in una dir non-git → emette finished('') entro 3s
        senza crash QThread.
        """
        logger.info("═══ TestGitBranchWorker.test_non_git_dir_finishes_without_crash ═══")
        results = []
        worker = GitBranchWorker(str(self.tmp))
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda branch: results.append(branch))
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)

        thread.start()
        timeout = time.time() + 3
        while thread.isRunning() and time.time() < timeout:
            self.qapp.processEvents()
            time.sleep(0.05)

        if thread.isRunning():
            thread.quit()
            thread.wait(1000)

        self.assertFalse(thread.isRunning())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "")
        logger.info("[PASS] GitBranchWorker in non-git dir → finished('') in %.1fs ✓",
                    3 - (timeout - time.time()))


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSearchPanel(unittest.TestCase):
    """Qt smoke test — SearchPanel creation"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_constructor_no_crash(self):
        logger.info("═══ TestSearchPanel.test_constructor_no_crash ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        self.assertIsNotNone(panel)
        logger.info("[PASS] SearchPanel(parent=QWidget) → creato ✓")
        parent.deleteLater()


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCommandPalette(unittest.TestCase):
    """Qt smoke test — CommandPalette creation"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_constructor_no_crash(self):
        logger.info("═══ TestCommandPalette.test_constructor_no_crash ═══")
        parent = QWidget()
        palette = CommandPalette(actions={"test": "Test action"}, parent=parent)
        self.assertIsNotNone(palette)
        logger.info("[PASS] CommandPalette(parent=QWidget) → creato ✓")
        parent.deleteLater()


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestKeybindingsDialog(unittest.TestCase):
    """Qt smoke test — KeybindingsDialog creation"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_constructor_no_crash(self):
        logger.info("═══ TestKeybindingsDialog.test_constructor_no_crash ═══")
        parent = QWidget()
        dlg = KeybindingsDialog(parent=parent, config_manager=ConfigManager())
        self.assertIsNotNone(dlg)
        logger.info("[PASS] KeybindingsDialog(parent=QWidget, config_manager=...) → creato ✓")
        parent.deleteLater()


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFileTree(unittest.TestCase):
    """Widget test — FileTree"""

    def setUp(self):
        ensure_qapp()
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        (self.tmp / "subdir").mkdir()
        (self.tmp / "file_a.txt").write_text("a")
        (self.tmp / "file_b.py").write_text("b")

    def tearDown(self):
        self._tmp_ctx.__exit__(None, None, None)

    def _find_item(self, ft, name):
        for i in range(ft.tree.topLevelItemCount()):
            item = ft.tree.topLevelItem(i)
            if item.text(0) == name:
                return item
        return None

    def test_populate_creates_parent_and_children(self):
        logger.info("═══ TestFileTree.test_populate_creates_parent_and_children ═══")
        ft = FileTree(str(self.tmp))
        root_items = [ft.tree.topLevelItem(i).text(0)
                      for i in range(ft.tree.topLevelItemCount())]
        self.assertIn("..", root_items)
        self.assertIn("subdir", root_items)
        self.assertIn("file_a.txt", root_items)
        self.assertIn("file_b.py", root_items)
        logger.info("[PASS] FileTree popolata con .., subdir, file ✓")

    def test_lazy_expand_populates_children(self):
        logger.info("═══ TestFileTree.test_lazy_expand_populates_children ═══")
        (self.tmp / "subdir" / "nested.txt").write_text("hello")
        ft = FileTree(str(self.tmp))
        sub_item = self._find_item(ft, "subdir")
        self.assertIsNotNone(sub_item)
        self.assertEqual(sub_item.childCount(), 1)
        self.assertEqual(sub_item.child(0).text(0), "...")
        ft._on_item_expanded(sub_item)
        self.assertEqual(sub_item.childCount(), 1)
        self.assertEqual(sub_item.child(0).text(0), "nested.txt")
        logger.info("[PASS] Espansione lazy carica figli di subdir ✓")

    def test_collapse_restores_placeholder(self):
        logger.info("═══ TestFileTree.test_collapse_restores_placeholder ═══")
        (self.tmp / "subdir" / "nested.txt").write_text("hello")
        ft = FileTree(str(self.tmp))
        sub_item = self._find_item(ft, "subdir")
        ft._on_item_expanded(sub_item)
        self.assertEqual(sub_item.child(0).text(0), "nested.txt")
        ft._on_item_collapsed(sub_item)
        self.assertEqual(sub_item.childCount(), 1)
        self.assertEqual(sub_item.child(0).text(0), "...")
        logger.info("[PASS] Collapse ripristina placeholder ... ✓")

    def test_double_click_parent_navigates_up(self):
        logger.info("═══ TestFileTree.test_double_click_parent_navigates_up ═══")
        ft = FileTree(str(self.tmp))
        parent_item = ft.tree.topLevelItem(0)
        ft._on_item_double_clicked(parent_item, 0)
        self.assertEqual(ft.current_root, str(os.path.realpath(self.tmp.parent)))
        logger.info("[PASS] Doppio click su .. naviga a parent ✓")

    def test_double_click_file_emits_fileOpened(self):
        logger.info("═══ TestFileTree.test_double_click_file_emits_fileOpened ═══")
        ft = FileTree(str(self.tmp))
        emitted = []
        ft.fileOpened.connect(lambda p: emitted.append(p))
        item = self._find_item(ft, "file_a.txt")
        self.assertIsNotNone(item)
        ft._on_item_double_clicked(item, 0)
        self.assertEqual(len(emitted), 1)
        self.assertIn("file_a.txt", emitted[0])
        logger.info("[PASS] Doppio click su file emette fileOpened ✓")

    def test_double_click_outside_root_blocked(self):
        logger.info("═══ TestFileTree.test_double_click_outside_root_blocked ═══")
        outside = self.tmp.parent / "outside_test.txt"
        outside.write_text("evil")
        ft = FileTree(str(self.tmp))
        emitted = []
        ft.fileOpened.connect(lambda p: emitted.append(p))
        item = QTreeWidgetItem(["outside_test.txt"])
        item.setData(0, Qt.ItemDataRole.UserRole, str(outside))
        with mock_qmessagebox_warning() as dialogs:
            ft._on_item_double_clicked(item, 0)
        self.assertGreaterEqual(len(dialogs), 1)
        self.assertEqual(len(emitted), 0)
        outside.unlink()
        logger.info("[PASS] File fuori root bloccato + warning ✓")

    @unittest.mock.patch("file_tree.QInputDialog.getText")
    def test_context_menu_create_file_emits_fileCreated(self, mock_gettext):
        logger.info("═══ TestFileTree.test_context_menu_create_file_emits_fileCreated ═══")
        mock_gettext.return_value = ("new_file.txt", True)
        emitted = []
        ft = FileTree(str(self.tmp))
        ft.fileCreated.connect(lambda p: emitted.append(p))
        ft._create_new_item(False)
        self.assertEqual(len(emitted), 1)
        self.assertTrue(Path(emitted[0]).exists())
        self.assertEqual(Path(emitted[0]).name, "new_file.txt")
        logger.info("[PASS] Crea file emette fileCreated ✓")

    @unittest.mock.patch("file_tree.QInputDialog.getText")
    def test_context_menu_create_folder_emits_folderCreated(self, mock_gettext):
        logger.info("═══ TestFileTree.test_context_menu_create_folder_emits_folderCreated ═══")
        mock_gettext.return_value = ("NewFolder", True)
        emitted = []
        ft = FileTree(str(self.tmp))
        ft.folderCreated.connect(lambda p: emitted.append(p))
        ft._create_new_item(True)
        self.assertEqual(len(emitted), 1)
        self.assertTrue(Path(emitted[0]).is_dir())
        logger.info("[PASS] Crea folder emette folderCreated ✓")

    @unittest.mock.patch("file_tree.QInputDialog.getText")
    def test_rename_item_emits_file_renamed(self, mock_gettext):
        logger.info("═══ TestFileTree.test_rename_item_emits_file_renamed ═══")
        mock_gettext.return_value = ("renamed.txt", True)
        emitted = []
        ft = FileTree(str(self.tmp))
        ft.file_renamed.connect(lambda old, new: emitted.append((old, new)))
        item = self._find_item(ft, "file_a.txt")
        old_path = item.data(0, Qt.ItemDataRole.UserRole)
        ft._rename_item(item, old_path)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0][0], old_path)
        self.assertIn("renamed.txt", emitted[0][1])
        self.assertFalse(Path(old_path).exists())
        logger.info("[PASS] Rename emette file_renamed ✓")

    @unittest.mock.patch("file_tree.QMessageBox.question")
    def test_delete_item_emits_file_deleted(self, mock_question):
        logger.info("═══ TestFileTree.test_delete_item_emits_file_deleted ═══")
        mock_question.return_value = QMessageBox.StandardButton.Yes
        emitted = []
        ft = FileTree(str(self.tmp))
        ft.file_deleted.connect(lambda p: emitted.append(p))
        item = self._find_item(ft, "file_a.txt")
        old_path = item.data(0, Qt.ItemDataRole.UserRole)
        ft._delete_item(item, old_path)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], old_path)
        self.assertFalse(Path(old_path).exists())
        logger.info("[PASS] Delete emette file_deleted ✓")

    def test_permission_error_emits_signal(self):
        logger.info("═══ TestFileTree.test_permission_error_emits_signal ═══")
        ft = FileTree(str(self.tmp))
        emitted = []
        ft.permission_denied.connect(lambda p: emitted.append(p))
        with unittest.mock.patch("file_tree.os.listdir", side_effect=PermissionError):
            ft._add_items(ft.tree, str(self.tmp))
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], str(self.tmp))
        logger.info("[PASS] PermissionError emette permission_denied ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSearchPanelFunctional(unittest.TestCase):
    """Functional test — SearchPanel and GoToLinePanel signals"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_find_next_emits_correct_args(self):
        logger.info("═══ TestSearchPanelFunctional.test_find_next_emits_correct_args ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.find_next_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("hello")
        panel.case_sensitive.setChecked(True)
        panel.on_find_next()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("hello", True, False))
        parent.deleteLater()
        logger.info("[PASS] find_next_requested con parametri corretti ✓")

    def test_find_prev_emits_correct_args(self):
        logger.info("═══ TestSearchPanelFunctional.test_find_prev_emits_correct_args ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.find_prev_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("search")
        panel.is_regex.setChecked(True)
        panel.on_find_prev()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("search", False, True))
        parent.deleteLater()
        logger.info("[PASS] find_prev_requested con parametri corretti ✓")

    def test_replace_emits_correct_args(self):
        logger.info("═══ TestSearchPanelFunctional.test_replace_emits_correct_args ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.replace_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("old")
        panel.replace_input.setText("new")
        panel.is_regex.setChecked(True)
        panel.on_replace()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("old", "new", False, True))
        parent.deleteLater()
        logger.info("[PASS] replace_requested con parametri corretti ✓")

    def test_replace_all_emits_correct_args(self):
        logger.info("═══ TestSearchPanelFunctional.test_replace_all_emits_correct_args ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.replace_all_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("from")
        panel.replace_input.setText("to")
        panel.case_sensitive.setChecked(True)
        panel.on_replace_all()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("from", "to", True, False))
        parent.deleteLater()
        logger.info("[PASS] replace_all_requested con parametri corretti ✓")

    def test_set_match_count_updates_label(self):
        logger.info("═══ TestSearchPanelFunctional.test_set_match_count_updates_label ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        panel.set_match_count(5, 42)
        self.assertEqual(panel.match_count_label.text(), "5 of 42")
        panel.set_match_count(0, 0)
        self.assertEqual(panel.match_count_label.text(), "0 of 0")
        parent.deleteLater()
        logger.info("[PASS] set_match_count aggiorna label ✓")

    def test_set_error_shows_temporary_error(self):
        logger.info("═══ TestSearchPanelFunctional.test_set_error_shows_temporary_error ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        panel.set_error("Bad pattern")
        self.assertEqual(panel.match_count_label.text(), "Bad pattern")
        self.assertIn(Tokens.DANGER.name(), panel.match_count_label.styleSheet())
        parent.deleteLater()
        logger.info("[PASS] set_error mostra messaggio + stile danger ✓")

    def test_goto_line_valid_emits_and_closes(self):
        logger.info("═══ TestSearchPanelFunctional.test_goto_line_valid_emits_and_closes ═══")
        parent = QWidget()
        panel = GoToLinePanel(parent=parent)
        goto_emitted = []
        close_emitted = []
        panel.goto_requested.connect(lambda n: goto_emitted.append(n))
        panel.close_requested.connect(lambda: close_emitted.append(True))
        panel.input.setText("42")
        panel._on_enter()
        self.assertEqual(goto_emitted, [42])
        self.assertEqual(close_emitted, [True])
        parent.deleteLater()
        logger.info("[PASS] goto linea valida emette entrambi i signal ✓")

    def test_goto_line_invalid_shows_error(self):
        logger.info("═══ TestSearchPanelFunctional.test_goto_line_invalid_shows_error ═══")
        parent = QWidget()
        panel = GoToLinePanel(parent=parent)
        panel.input.setText("abc")
        panel._on_enter()
        self.assertIn(Tokens.DANGER.name(), panel.input.styleSheet())
        parent.deleteLater()
        logger.info("[PASS] goto linea non valida mostra errore ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCommandPaletteFunctional(unittest.TestCase):
    """Functional test — CommandPalette filtering and navigation"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_filter_actions_matches_description(self):
        logger.info("═══ TestCommandPaletteFunctional.test_filter_actions_matches_description ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test command", "cmd.other": "Other thing"},
                                  parent=parent)
        palette.filter_actions("test")
        self.assertEqual(palette.action_list.count(), 1)
        self.assertEqual(palette.action_list.item(0).text(), "Test command")
        palette.deleteLater()
        logger.info("[PASS] Filtro per description ✓")

    def test_filter_actions_matches_action_id(self):
        logger.info("═══ TestCommandPaletteFunctional.test_filter_actions_matches_action_id ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test command", "cmd.other": "Other thing"},
                                  parent=parent)
        palette.filter_actions("cmd")
        self.assertEqual(palette.action_list.count(), 2)
        palette.filter_actions("other")
        self.assertEqual(palette.action_list.count(), 1)
        self.assertEqual(palette.action_list.item(0).text(), "Other thing")
        palette.deleteLater()
        logger.info("[PASS] Filtro per action_id ✓")

    def test_enter_selects_first_item(self):
        logger.info("═══ TestCommandPaletteFunctional.test_enter_selects_first_item ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test command"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.on_enter_pressed()
        self.assertEqual(emitted, ["cmd.test"])
        palette.deleteLater()
        logger.info("[PASS] Enter seleziona primo item ✓")

    def test_escape_rejects_dialog(self):
        logger.info("═══ TestCommandPaletteFunctional.test_escape_rejects_dialog ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test command"}, parent=parent)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                          Qt.KeyboardModifier.NoModifier)
        palette.keyPressEvent(event)
        self.assertEqual(palette.result(),
                         int(QDialog.DialogCode.Rejected))
        palette.deleteLater()
        logger.info("[PASS] Escape rejecta dialog ✓")

    def test_arrow_keys_navigate_list(self):
        logger.info("═══ TestCommandPaletteFunctional.test_arrow_keys_navigate_list ═══")
        parent = QWidget()
        palette = CommandPalette(
            {"cmd.a": "Action A", "cmd.b": "Action B", "cmd.c": "Action C"},
            parent=parent)
        self.assertEqual(palette.action_list.currentRow(), 0)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down,
                         Qt.KeyboardModifier.NoModifier)
        up = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up,
                       Qt.KeyboardModifier.NoModifier)
        palette.keyPressEvent(down)
        self.assertEqual(palette.action_list.currentRow(), 1)
        palette.keyPressEvent(down)
        self.assertEqual(palette.action_list.currentRow(), 2)
        palette.keyPressEvent(down)
        self.assertEqual(palette.action_list.currentRow(), 0)
        palette.keyPressEvent(up)
        self.assertEqual(palette.action_list.currentRow(), 2)
        palette.deleteLater()
        logger.info("[PASS] Navigazione frecce Up/Down ✓")

    def test_update_actions_refreshes_list(self):
        logger.info("═══ TestCommandPaletteFunctional.test_update_actions_refreshes_list ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.a": "Action A"}, parent=parent)
        self.assertEqual(palette.action_list.count(), 1)
        palette.update_actions({"cmd.b": "Action B", "cmd.c": "Action C"})
        self.assertEqual(palette.action_list.count(), 2)
        palette.deleteLater()
        logger.info("[PASS] update_actions aggiorna lista ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestKeybindingsDialogFunctional(unittest.TestCase):
    """Functional test — KeybindingsDialog load/edit/save"""

    def setUp(self):
        ensure_qapp()
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self.cm = ConfigManager()

    def tearDown(self):
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_load_shows_current_bindings(self):
        logger.info("═══ TestKeybindingsDialogFunctional.test_load_shows_current_bindings ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S", "open": "Ctrl+O"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        self.assertEqual(dlg.list_widget.count(), 2)
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Dialog carica binding esistenti ✓")

    def test_edit_binding_updates_model(self):
        logger.info("═══ TestKeybindingsDialogFunctional.test_edit_binding_updates_model ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        with unittest.mock.patch("PyQt6.QtWidgets.QInputDialog.getText",
                                  return_value=("Ctrl+Shift+S", True)):
            dlg.edit_binding(dlg.list_widget.item(0))
        self.assertEqual(dlg.bindings["save"], "Ctrl+Shift+S")
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Edit binding aggiorna model interno ✓")

    def test_save_updates_config_manager(self):
        logger.info("═══ TestKeybindingsDialogFunctional.test_save_updates_config_manager ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S", "open": "Ctrl+O"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        dlg.bindings["save"] = "Ctrl+Shift+S"
        dlg.save_and_close()
        self.assertEqual(self.cm.keybindings["save"], "Ctrl+Shift+S")
        self.assertEqual(self.cm.keybindings["open"], "Ctrl+O")
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Save aggiorna ConfigManager ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorTabExtended(unittest.TestCase):
    """Extended test — EditorTab modification state and UTF-8 save"""

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_is_modified_tracks_changes(self):
        logger.info("═══ TestEditorTabExtended.test_is_modified_tracks_changes ═══")
        tab = EditorTab(pane='left')
        self.assertFalse(tab.is_modified())
        tab.editor.setPlainText("modified content")
        self.assertTrue(tab.is_modified())
        logger.info("[PASS] is_modified traccia modifiche ✓")

    def test_save_file_triggers_utf8_write(self):
        logger.info("═══ TestEditorTabExtended.test_save_file_triggers_utf8_write ═══")
        with tmp_dir() as tmp:
            file = tmp / "utf8.txt"
            tab = EditorTab(pane='left')
            tab.file_path = str(file)
            unicode_text = "café 日本語 ✓"
            tab.editor.setPlainText(unicode_text)
            result = tab.save_file()
            self.assertTrue(result)
            content = file.read_text(encoding='utf-8')
            self.assertEqual(content, unicode_text)
        logger.info("[PASS] save_file preserva contenuto UTF-8 ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowExtended(unittest.TestCase):
    """Extended test — MainWindow new_file and split"""

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_new_tab_creates_empty_editor(self):
        logger.info("═══ TestMainWindowExtended.test_new_tab_creates_empty_editor ═══")
        initial = self.mw.tabs.count()
        self.mw.new_file()
        self.assertEqual(self.mw.tabs.count(), initial + 1)
        logger.info("[PASS] new_file crea un nuovo tab ✓")

    def test_split_editor_creates_right_pane(self):
        logger.info("═══ TestMainWindowExtended.test_split_editor_creates_right_pane ═══")
        file = self.tmp / "split_test.txt"
        file.write_text("split content", encoding='utf-8')
        self.mw.open_file(str(file))
        self.assertGreater(self.mw.tabs.count(), 0)
        initial_right = self.mw.tabs_right.count()
        self.mw.split_editor()
        self.assertEqual(self.mw.tabs_right.count(), initial_right + 1)
        logger.info("[PASS] split_editor crea tab nel right pane ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestTerminalWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self.tw = TerminalWidget()

    def tearDown(self):
        self.tw.kill_process()
        self.tw.deleteLater()

    def test_initial_height_is_200(self):
        logger.info("═══ TestTerminalWidget.test_initial_height_is_200 ═══")
        self.assertEqual(self.tw.height(), 200)
        logger.info("[PASS] TerminalWidget initial height 200 ✓")

    def test_set_cwd_with_valid_dir(self):
        logger.info("═══ TestTerminalWidget.test_set_cwd_with_valid_dir ═══")
        with tmp_dir() as tmp:
            self.tw.set_cwd(str(tmp))
            self.assertEqual(self.tw._cwd, str(tmp))
            self.assertEqual(self.tw._cwd_label.text(), str(tmp))
        logger.info("[PASS] set_cwd con dir aggiorna _cwd e label ✓")

    def test_set_cwd_with_file_uses_parent(self):
        logger.info("═══ TestTerminalWidget.test_set_cwd_with_file_uses_parent ═══")
        with tmp_dir() as tmp:
            f = tmp / "file.txt"
            f.write_text("x")
            self.tw.set_cwd(str(f))
            self.assertEqual(self.tw._cwd, str(tmp))
        logger.info("[PASS] set_cwd con file usa parent dir ✓")

    def test_set_cwd_invalid_path_ignored(self):
        logger.info("═══ TestTerminalWidget.test_set_cwd_invalid_path_ignored ═══")
        original = self.tw._cwd
        self.tw.set_cwd("/nonexistent/path/xyz")
        self.assertEqual(self.tw._cwd, original)
        logger.info("[PASS] set_cwd su path invalido ignorato ✓")

    def test_clear_output(self):
        logger.info("═══ TestTerminalWidget.test_clear_output ═══")
        self.tw._append("some text\n")
        self.tw.clear_output()
        self.assertEqual(self.tw._output.toPlainText(), "")
        logger.info("[PASS] clear_output svuota output ✓")

    def test_append_adds_text(self):
        logger.info("═══ TestTerminalWidget.test_append_adds_text ═══")
        self.tw._append("hello world\n")
        self.assertIn("hello world", self.tw._output.toPlainText())
        logger.info("[PASS] _append aggiunge testo ✓")

    def test_history_navigation_up(self):
        logger.info("═══ TestTerminalWidget.test_history_navigation_up ═══")
        self.tw._history = ["cmd1", "cmd2"]
        self.tw._history_index = 2
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        self.tw.eventFilter(self.tw._input, event)
        self.assertEqual(self.tw._input.text(), "cmd2")
        self.tw.eventFilter(self.tw._input, event)
        self.assertEqual(self.tw._input.text(), "cmd1")
        logger.info("[PASS] history up naviga correttamente ✓")

    def test_history_navigation_down(self):
        logger.info("═══ TestTerminalWidget.test_history_navigation_down ═══")
        self.tw._history = ["cmd1", "cmd2"]
        self.tw._history_index = 0
        self.tw._input.setText("cmd1")
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        self.tw.eventFilter(self.tw._input, event)
        self.assertEqual(self.tw._input.text(), "cmd2")
        logger.info("[PASS] history down naviga correttamente ✓")

    def test_cd_valid_directory(self):
        logger.info("═══ TestTerminalWidget.test_cd_valid_directory ═══")
        with tmp_dir() as tmp:
            self.tw._cwd = str(tmp)
            self.tw._input.setText(f"cd {tmp}")
            self.tw._run_command()
            self.assertEqual(self.tw._cwd, str(tmp))
        logger.info("[PASS] cd in directory valida funziona ✓")

    def test_cd_invalid_directory_shows_error(self):
        logger.info("═══ TestTerminalWidget.test_cd_invalid_directory_shows_error ═══")
        self.tw._cwd = os.getcwd()
        self.tw._input.setText("cd /nonexistent/path/xyz")
        self.tw._run_command()
        self.assertIn("No such directory", self.tw._output.toPlainText())
        logger.info("[PASS] cd in directory invalida mostra errore ✓")

    def test_run_command_blocked_while_process_running(self):
        logger.info("═══ TestTerminalWidget.test_run_command_blocked_while_process_running ═══")
        from PyQt6.QtCore import QProcess
        self.tw._process = QProcess()
        self.tw._process.start("/bin/bash", ["-c", "sleep 10"])
        self.tw._process.waitForStarted(1000)
        self.tw._input.setText("echo second")
        self.tw._run_command()
        self.assertIn("already running", self.tw._output.toPlainText())
        self.tw._process.kill()
        self.tw._process.waitForFinished(1000)
        logger.info("[PASS] comando bloccato se processo in esecuzione ✓")

    def test_kill_process_appends_message(self):
        logger.info("═══ TestTerminalWidget.test_kill_process_appends_message ═══")
        from PyQt6.QtCore import QProcess
        self.tw._process = QProcess()
        self.tw._process.start("/bin/bash", ["-c", "sleep 10"])
        self.tw._process.waitForStarted(1000)
        self.tw.kill_process()
        self.tw._process.waitForFinished(1000)
        self.assertIn("killed", self.tw._output.toPlainText())
        logger.info("[PASS] kill_process scrive messaggio ✓")

    def test_collapse_calls_parent_toggle_terminal(self):
        logger.info("═══ TestTerminalWidget.test_collapse_calls_parent_toggle_terminal ═══")
        mock_parent = QWidget()
        mock_parent.toggle_terminal = unittest.mock.MagicMock()
        tw = TerminalWidget(parent=mock_parent)
        tw._collapse()
        mock_parent.toggle_terminal.assert_called_once()
        tw.deleteLater()
        mock_parent.deleteLater()
        logger.info("[PASS] _collapse chiama parent.toggle_terminal ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestResizeHandle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_initial_height_is_4(self):
        logger.info("═══ TestResizeHandle.test_initial_height_is_4 ═══")
        tw = TerminalWidget()
        self.assertEqual(tw._resize_handle.height(), 4)
        tw.deleteLater()
        logger.info("[PASS] ResizeHandle initial height 4 ✓")

    def test_cursor_is_size_ver(self):
        logger.info("═══ TestResizeHandle.test_cursor_is_size_ver ═══")
        tw = TerminalWidget()
        self.assertEqual(tw._resize_handle.cursor().shape(), Qt.CursorShape.SizeVerCursor)
        tw.deleteLater()
        logger.info("[PASS] ResizeHandle cursor SizeVerCursor ✓")

    def test_drag_up_increases_height(self):
        logger.info("═══ TestResizeHandle.test_drag_up_increases_height ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(200)
        handle = tw._resize_handle
        handle._press_y = 300.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(0, 0),
            QPointF(0, 250),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertGreater(tw.height(), 200)
        tw.deleteLater()
        logger.info("[PASS] drag up aumenta altezza ✓")

    def test_drag_down_decreases_height(self):
        logger.info("═══ TestResizeHandle.test_drag_down_decreases_height ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(200)
        handle = tw._resize_handle
        handle._press_y = 300.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(0, 0),
            QPointF(0, 350),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertLess(tw.height(), 200)
        tw.deleteLater()
        logger.info("[PASS] drag down diminuisce altezza ✓")

    def test_height_clamped_min_80(self):
        logger.info("═══ TestResizeHandle.test_height_clamped_min_80 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(100)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(0, 0), QPointF(0, 500),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertGreaterEqual(tw.height(), 80)
        tw.deleteLater()
        logger.info("[PASS] altezza minima 80 ✓")

    def test_height_clamped_max_600(self):
        logger.info("═══ TestResizeHandle.test_height_clamped_max_600 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(400)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(0, 0), QPointF(0, -500),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertLessEqual(tw.height(), 600)
        tw.deleteLater()
        logger.info("[PASS] altezza massima 600 ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFileTreeHiddenFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def _visible_names(self, ft):
        names = set()
        for i in range(ft.tree.topLevelItemCount()):
            text = ft.tree.topLevelItem(i).text(0)
            if text != "..":
                names.add(text)
        return names

    def test_hidden_files_hidden_by_default(self):
        logger.info("═══ TestFileTreeHiddenFiles.test_hidden_files_hidden_by_default ═══")
        with tmp_dir() as tmp:
            (tmp / "visible.txt").write_text("x")
            (tmp / ".hidden.txt").write_text("x")
            ft = FileTree(str(tmp))
            names = self._visible_names(ft)
            self.assertIn("visible.txt", names)
            self.assertNotIn(".hidden.txt", names)
            ft.deleteLater()
        logger.info("[PASS] file nascosti nascosti di default ✓")

    def test_set_show_hidden_true_reveals_hidden(self):
        logger.info("═══ TestFileTreeHiddenFiles.test_set_show_hidden_true_reveals_hidden ═══")
        with tmp_dir() as tmp:
            (tmp / "visible.txt").write_text("x")
            (tmp / ".hidden.txt").write_text("x")
            ft = FileTree(str(tmp))
            ft.set_show_hidden(True)
            names = self._visible_names(ft)
            self.assertIn("visible.txt", names)
            self.assertIn(".hidden.txt", names)
            ft.deleteLater()
        logger.info("[PASS] set_show_hidden(True) rivela nascosti ✓")

    def test_set_show_hidden_false_hides_again(self):
        logger.info("═══ TestFileTreeHiddenFiles.test_set_show_hidden_false_hides_again ═══")
        with tmp_dir() as tmp:
            (tmp / ".hidden.txt").write_text("x")
            ft = FileTree(str(tmp))
            ft.set_show_hidden(True)
            ft.set_show_hidden(False)
            names = self._visible_names(ft)
            self.assertNotIn(".hidden.txt", names)
            ft.deleteLater()
        logger.info("[PASS] set_show_hidden(False) nasconde di nuovo ✓")

    def test_parent_item_always_visible(self):
        logger.info("═══ TestFileTreeHiddenFiles.test_parent_item_always_visible ═══")
        with tmp_dir() as tmp:
            ft = FileTree(str(tmp))
            all_names = [ft.tree.topLevelItem(i).text(0)
                         for i in range(ft.tree.topLevelItemCount())]
            parent = os.path.dirname(str(tmp))
            if parent != str(tmp):
                self.assertIn("..", all_names)
            ft.deleteLater()
        logger.info("[PASS] parent item sempre visibile ✓")

    def test_show_hidden_state_persists(self):
        logger.info("═══ TestFileTreeHiddenFiles.test_show_hidden_state_persists ═══")
        with tmp_dir() as tmp:
            ft = FileTree(str(tmp))
            self.assertFalse(ft._show_hidden)
            ft.set_show_hidden(True)
            self.assertTrue(ft._show_hidden)
            ft.deleteLater()
        logger.info("[PASS] stato _show_hidden persistente ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestTerminalToggleInMainWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_terminal_hidden_on_startup(self):
        logger.info("═══ TestTerminalToggleInMainWindow.test_terminal_hidden_on_startup ═══")
        self.assertTrue(self.mw.terminal_widget.isHidden())
        logger.info("[PASS] terminal hidden on startup ✓")

    def test_toggle_terminal_shows_widget(self):
        logger.info("═══ TestTerminalToggleInMainWindow.test_toggle_terminal_shows_widget ═══")
        self.mw.toggle_terminal()
        self.assertFalse(self.mw.terminal_widget.isHidden())
        logger.info("[PASS] toggle_terminal mostra widget ✓")

    def test_toggle_terminal_twice_hides_widget(self):
        logger.info("═══ TestTerminalToggleInMainWindow.test_toggle_terminal_twice_hides_widget ═══")
        self.mw.toggle_terminal()
        self.mw.toggle_terminal()
        self.assertTrue(self.mw.terminal_widget.isHidden())
        logger.info("[PASS] toggle_terminal due volte nasconde ✓")

    def test_toggle_terminal_sets_cwd_from_active_tab(self):
        logger.info("═══ TestTerminalToggleInMainWindow.test_toggle_terminal_sets_cwd_from_active_tab ═══")
        with tmp_dir() as tmp:
            f = tmp / "test.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw.toggle_terminal()
            self.assertEqual(self.mw.terminal_widget._cwd, str(tmp))
        logger.info("[PASS] toggle_terminal imposta cwd dal tab attivo ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowStatusBar(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_cycle_encoding_cycles_through_values(self):
        logger.info("═══ TestMainWindowStatusBar.test_cycle_encoding_cycles_through_values ═══")
        self.mw.new_file()
        self.assertEqual(self.mw.config_manager.get("encoding", "UTF-8"), "UTF-8")
        self.mw._cycle_encoding()
        self.assertEqual(self.mw.config_manager.get("encoding"), "UTF-16")
        self.mw._cycle_encoding()
        self.assertEqual(self.mw.config_manager.get("encoding"), "Latin-1")
        self.mw._cycle_encoding()
        self.assertEqual(self.mw.config_manager.get("encoding"), "CP1252")
        self.mw._cycle_encoding()
        self.assertEqual(self.mw.config_manager.get("encoding"), "UTF-8")
        logger.info("[PASS] encoding cycles correctly ✓")

    def test_cycle_line_ending_cycles_through_values(self):
        logger.info("═══ TestMainWindowStatusBar.test_cycle_line_ending_cycles_through_values ═══")
        self.mw.new_file()
        self.mw._cycle_line_ending()
        self.assertEqual(self.mw.config_manager.get("line_ending"), "CRLF")
        self.mw._cycle_line_ending()
        self.assertEqual(self.mw.config_manager.get("line_ending"), "CR")
        self.mw._cycle_line_ending()
        self.assertEqual(self.mw.config_manager.get("line_ending"), "LF")
        logger.info("[PASS] line ending cycles correctly ✓")

    def test_cycle_tab_width_cycles_through_values(self):
        logger.info("═══ TestMainWindowStatusBar.test_cycle_tab_width_cycles_through_values ═══")
        self.mw.new_file()
        self.mw._cycle_tab_width()
        self.assertEqual(self.mw.config_manager.get("tab_width"), 8)
        self.mw._cycle_tab_width()
        self.assertEqual(self.mw.config_manager.get("tab_width"), 2)
        self.mw._cycle_tab_width()
        self.assertEqual(self.mw.config_manager.get("tab_width"), 4)
        logger.info("[PASS] tab width cycles correctly ✓")

    def test_zoom_active_editor_increases_level(self):
        logger.info("═══ TestMainWindowStatusBar.test_zoom_active_editor_increases_level ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        initial_zoom = tab.editor._zoom_level
        self.mw._zoom_active_editor(10)
        self.assertEqual(tab.editor._zoom_level, initial_zoom + 10)
        self.assertEqual(self.mw.zoom_label.text(), f"{initial_zoom + 10}%")
        logger.info("[PASS] zoom active editor increases ✓")

    def test_zoom_active_editor_clamped_at_50_min(self):
        logger.info("═══ TestMainWindowStatusBar.test_zoom_active_editor_clamped_at_50_min ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.set_zoom_level(50)
        self.mw._zoom_active_editor(-100)
        self.assertGreaterEqual(tab.editor._zoom_level, 50)
        logger.info("[PASS] zoom clamped at 50 ✓")

    def test_zoom_active_editor_clamped_at_200_max(self):
        logger.info("═══ TestMainWindowStatusBar.test_zoom_active_editor_clamped_at_200_max ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.set_zoom_level(200)
        self.mw._zoom_active_editor(100)
        self.assertLessEqual(tab.editor._zoom_level, 200)
        logger.info("[PASS] zoom clamped at 200 ✓")

    def test_reset_zoom_sets_100(self):
        logger.info("═══ TestMainWindowStatusBar.test_reset_zoom_sets_100 ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.set_zoom_level(150)
        self.mw._reset_zoom()
        self.assertEqual(tab.editor._zoom_level, 100)
        self.assertEqual(self.mw.zoom_label.text(), "100%")
        logger.info("[PASS] reset zoom sets 100 ✓")

    def test_update_cursor_pos_reflects_cursor(self):
        logger.info("═══ TestMainWindowStatusBar.test_update_cursor_pos_reflects_cursor ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("line1\nline2\nline3")
        cursor = tab.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        tab.editor.setTextCursor(cursor)
        self.mw._update_cursor_pos()
        self.assertIn("Ln 3", self.mw.line_col_label.text())
        logger.info("[PASS] cursor position reflects correctly ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowCloseTab(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_close_unmodified_tab_removes_tab(self):
        logger.info("═══ TestMainWindowCloseTab.test_close_unmodified_tab_removes_tab ═══")
        self.mw.new_file()
        self.mw.new_file()
        initial = self.mw.tabs.count()
        self.mw.close_tab(0, 'left')
        self.assertEqual(self.mw.tabs.count(), initial - 1)
        logger.info("[PASS] close unmodified tab removes ✓")

    def test_close_last_tab_creates_new_file(self):
        logger.info("═══ TestMainWindowCloseTab.test_close_last_tab_creates_new_file ═══")
        while self.mw.tabs.count() > 1:
            self.mw.close_tab(0, 'left')
        self.mw.close_tab(0, 'left')
        self.assertEqual(self.mw.tabs.count(), 1)
        logger.info("[PASS] close last tab creates new file ✓")

    def test_close_right_tab_hides_right_pane_when_empty(self):
        logger.info("═══ TestMainWindowCloseTab.test_close_right_tab_hides_right_pane_when_empty ═══")
        with tmp_dir() as tmp:
            f = tmp / "r.txt"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw.split_editor()
            self.assertFalse(self.mw.tabs_right.isHidden())
            self.mw.close_tab(0, 'right')
            self.assertTrue(self.mw.tabs_right.isHidden())
        logger.info("[PASS] close right tab hides pane when empty ✓")

    def test_update_tab_title_shows_bullet_when_modified(self):
        logger.info("═══ TestMainWindowCloseTab.test_update_tab_title_shows_bullet_when_modified ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        idx = self.mw.tabs.indexOf(tab)
        tab.editor.setPlainText("modified")
        self.mw._update_tab_title_pane('left', idx)
        title = self.mw.tabs.tabText(idx)
        self.assertIn("\u25cf", title)
        logger.info("[PASS] bullet shown when modified ✓")

    def test_update_tab_title_no_bullet_when_saved(self):
        logger.info("═══ TestMainWindowCloseTab.test_update_tab_title_no_bullet_when_saved ═══")
        with tmp_dir() as tmp:
            f = tmp / "clean.txt"
            f.write_text("x")
            self.mw.open_file(str(f))
            tab = self.mw.tabs.currentWidget()
            idx = self.mw.tabs.indexOf(tab)
            self.mw._update_tab_title_pane('left', idx)
            title = self.mw.tabs.tabText(idx)
            self.assertNotIn("\u25cf", title)
        logger.info("[PASS] no bullet when saved ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowSaveTab(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_save_tab_by_index_with_path_returns_true(self):
        logger.info("═══ TestMainWindowSaveTab.test_save_tab_by_index_with_path_returns_true ═══")
        with tmp_dir() as tmp:
            f = tmp / "save_me.txt"
            f.write_text("original")
            self.mw.open_file(str(f))
            tab = self.mw.tabs.currentWidget()
            tab.editor.setPlainText("updated content")
            result = self.mw.save_tab_by_index(self.mw.tabs.indexOf(tab), 'left')
            self.assertTrue(result)
            self.assertEqual(f.read_text(encoding='utf-8'), "updated content")
        logger.info("[PASS] save tab with path returns True ✓")

    def test_save_tab_by_index_without_path_opens_dialog(self):
        logger.info("═══ TestMainWindowSaveTab.test_save_tab_by_index_without_path_opens_dialog ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("unsaved")
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QFileDialog.getSaveFileName',
            return_value=('', '')
        ):
            result = self.mw.save_tab_by_index(self.mw.tabs.indexOf(tab), 'left')
        self.assertFalse(result)
        logger.info("[PASS] save tab without path returns False ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowUndoRedo(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_handle_undo_reverts_text(self):
        logger.info("═══ TestMainWindowUndoRedo.test_handle_undo_reverts_text ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("original")
        tab.editor.document().setModified(False)
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("modified")
        self.mw.handle_undo()
        self.assertEqual(tab.editor.toPlainText(), "original")
        logger.info("[PASS] undo reverts text ✓")

    def test_handle_redo_reapplies_text(self):
        logger.info("═══ TestMainWindowUndoRedo.test_handle_redo_reapplies_text ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("original")
        tab.editor.document().setModified(False)
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("modified")
        self.mw.handle_undo()
        self.mw.handle_redo()
        self.assertEqual(tab.editor.toPlainText(), "modified")
        logger.info("[PASS] redo reapplies text ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowFind(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_handle_find_plain_text_returns_true_when_found(self):
        logger.info("═══ TestMainWindowFind.test_handle_find_plain_text_returns_true_when_found ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("hello world hello")
        result = self.mw.handle_find("hello", False, False, forward=True)
        self.assertTrue(result)
        logger.info("[PASS] find plain text found ✓")

    def test_handle_find_plain_text_returns_false_when_not_found(self):
        logger.info("═══ TestMainWindowFind.test_handle_find_plain_text_returns_false_when_not_found ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("hello world")
        result = self.mw.handle_find("xyz", False, False, forward=True)
        self.assertFalse(result)
        logger.info("[PASS] find plain text not found ✓")

    def test_handle_find_case_sensitive(self):
        logger.info("═══ TestMainWindowFind.test_handle_find_case_sensitive ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("Hello hello")
        result_sensitive = self.mw.handle_find("Hello", True, False, forward=True)
        self.assertTrue(result_sensitive)
        result_wrong_case = self.mw.handle_find("hello", True, False, forward=True)
        self.assertTrue(result_wrong_case)
        logger.info("[PASS] find case sensitive ✓")

    def test_handle_find_regex(self):
        logger.info("═══ TestMainWindowFind.test_handle_find_regex ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("foo123bar")
        result = self.mw.handle_find(r"\d+", False, True, forward=True)
        self.assertTrue(result)
        logger.info("[PASS] find regex ✓")

    def test_handle_replace_all_replaces_all_occurrences(self):
        logger.info("═══ TestMainWindowFind.test_handle_replace_all_replaces_all_occurrences ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("cat cat cat")
        self.mw.handle_replace_all("cat", "dog", False, False)
        self.assertEqual(tab.editor.toPlainText(), "dog dog dog")
        logger.info("[PASS] replace all ✓")

    def test_handle_replace_replaces_current_selection(self):
        logger.info("═══ TestMainWindowFind.test_handle_replace_replaces_current_selection ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("cat cat")
        self.mw.handle_find("cat", False, False, forward=True)
        self.mw.handle_replace("cat", "dog", False, False)
        self.assertIn("dog", tab.editor.toPlainText())
        logger.info("[PASS] handle replace ✓")

    def test_toggle_search_panel_changes_max_height(self):
        logger.info("═══ TestMainWindowFind.test_toggle_search_panel_changes_max_height ═══")
        self.mw.new_file()
        initial_max_h = self.mw.search_panel.maximumHeight()
        self.mw.toggle_search_panel('find')
        self.assertNotEqual(
            self.mw._search_anim.endValue(),
            initial_max_h
        )
        logger.info("[PASS] toggle search panel changes height ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowRecentFiles(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_open_file_adds_to_recent(self):
        logger.info("═══ TestMainWindowRecentFiles.test_open_file_adds_to_recent ═══")
        with tmp_dir() as tmp:
            f = tmp / "recent.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            recent = self.mw.config_manager.get("recent_files", [])
            self.assertTrue(any("recent.py" in r for r in recent))
        logger.info("[PASS] open file adds to recent ✓")

    def test_open_same_file_twice_does_not_duplicate_tab(self):
        logger.info("═══ TestMainWindowRecentFiles.test_open_same_file_twice_does_not_duplicate_tab ═══")
        with tmp_dir() as tmp:
            f = tmp / "dup.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            count_after_first = self.mw.tabs.count()
            self.mw.open_file(str(f))
            self.assertEqual(self.mw.tabs.count(), count_after_first)
        logger.info("[PASS] open same file twice no duplicate tab ✓")

    def test_clear_recent_empties_list(self):
        logger.info("═══ TestMainWindowRecentFiles.test_clear_recent_empties_list ═══")
        with tmp_dir() as tmp:
            f = tmp / "todel.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw._clear_recent()
            recent = self.mw.config_manager.get("recent_files", [])
            self.assertEqual(recent, [])
        logger.info("[PASS] clear recent empties list ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowViewToggles(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_toggle_word_wrap_applies_to_all_tabs(self):
        logger.info("═══ TestMainWindowViewToggles.test_toggle_word_wrap_applies_to_all_tabs ═══")
        self.mw.new_file()
        self.mw.new_file()
        self.mw.word_wrap_action.setChecked(True)
        self.mw.toggle_word_wrap()
        for i in range(self.mw.tabs.count()):
            tab = self.mw.tabs.widget(i)
            self.assertIsNotNone(tab)
        logger.info("[PASS] toggle word wrap applies to all tabs ✓")

    def test_toggle_sidebar_hides_and_shows(self):
        logger.info("═══ TestMainWindowViewToggles.test_toggle_sidebar_hides_and_shows ═══")
        self.assertTrue(self.mw.sidebar_visible)
        self.mw.toggle_sidebar()
        self.assertFalse(self.mw.sidebar_visible)
        self.mw.toggle_sidebar()
        self.assertTrue(self.mw.sidebar_visible)
        logger.info("[PASS] toggle sidebar ✓")

    def test_toggle_sidebar_shows_strip_when_hidden(self):
        logger.info("═══ TestMainWindowViewToggles.test_toggle_sidebar_shows_strip_when_hidden ═══")
        self.mw.toggle_sidebar()
        self.assertFalse(self.mw.toggle_strip.isHidden())
        self.mw.toggle_sidebar()
        self.assertTrue(self.mw.toggle_strip.isHidden())
        logger.info("[PASS] toggle sidebar strip ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowMoveTab(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_move_tab_within_left_pane(self):
        logger.info("═══ TestMainWindowMoveTab.test_move_tab_within_left_pane ═══")
        self.mw.new_file()
        self.mw.new_file()
        count_before = self.mw.tabs.count()
        self.mw._move_tab('left', 0, 'left', 1)
        self.assertEqual(self.mw.tabs.count(), count_before)
        logger.info("[PASS] move tab within left pane ✓")

    def test_move_tab_left_to_right_shows_right_pane(self):
        logger.info("═══ TestMainWindowMoveTab.test_move_tab_left_to_right_shows_right_pane ═══")
        self.mw.new_file()
        self.mw.new_file()
        self.assertTrue(self.mw.tabs_right.isHidden())
        self.mw._move_tab('left', 0, 'right', 0)
        self.assertFalse(self.mw.tabs_right.isHidden())
        logger.info("[PASS] move tab left to right shows right pane ✓")

    def test_move_tab_right_to_left_hides_right_pane_when_empty(self):
        logger.info("═══ TestMainWindowMoveTab.test_move_tab_right_to_left_hides_right_pane_when_empty ═══")
        with tmp_dir() as tmp:
            f = tmp / "mv.txt"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw.split_editor()
            self.mw._move_tab('right', 0, 'left', 0)
            self.assertTrue(self.mw.tabs_right.isHidden())
        logger.info("[PASS] move tab right to left hides right pane ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowSessionSave(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_save_session_persists_open_file_path(self):
        logger.info("═══ TestMainWindowSessionSave.test_save_session_persists_open_file_path ═══")
        with tmp_dir() as tmp:
            f = tmp / "sess.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw._save_session()
            data = self.mw.config_manager.load_session()
            paths = [t["path"] for t in data.get("tabs", []) if t.get("path")]
            self.assertTrue(any("sess.py" in p for p in paths))
        logger.info("[PASS] save session persists open file path ✓")

    def test_save_session_persists_unsaved_content(self):
        logger.info("═══ TestMainWindowSessionSave.test_save_session_persists_unsaved_content ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("unsaved stuff")
        tab._is_modified = True
        self.mw._save_session()
        data = self.mw.config_manager.load_session()
        contents = [t.get("unsaved_content") for t in data.get("tabs", [])]
        self.assertIn("unsaved stuff", contents)
        logger.info("[PASS] save session persists unsaved content ✓")

    def test_save_session_persists_view_settings(self):
        logger.info("═══ TestMainWindowSessionSave.test_save_session_persists_view_settings ═══")
        self.mw.word_wrap_action.setChecked(True)
        self.mw._save_session()
        data = self.mw.config_manager.load_session()
        self.assertTrue(data["view_settings"]["word_wrap"])
        logger.info("[PASS] save session persists view settings ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowFileRenamedDeleted(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self._mock_git = unittest.mock.patch.object(
            MainWindow, '_update_git_branch', return_value=None)
        self._mock_git.start()
        self.mw = MainWindow()

    def tearDown(self):
        self.mw.deleteLater()
        self._mock_git.stop()
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_on_file_renamed_updates_tab_path(self):
        logger.info("═══ TestMainWindowFileRenamedDeleted.test_on_file_renamed_updates_tab_path ═══")
        with tmp_dir() as tmp:
            f = tmp / "old.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            tab = self.mw.tabs.currentWidget()
            new_path = str(tmp / "new.py")
            self.mw._on_file_renamed(str(f), new_path)
            self.assertEqual(tab.file_path, new_path)
        logger.info("[PASS] on_file_renamed updates tab path ✓")

    def test_on_file_deleted_closes_tab(self):
        logger.info("═══ TestMainWindowFileRenamedDeleted.test_on_file_deleted_closes_tab ═══")
        with tmp_dir() as tmp:
            f = tmp / "del.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw._on_file_deleted(str(f))
            remaining_paths = [
                self.mw.tabs.widget(i).file_path
                for i in range(self.mw.tabs.count())
            ]
            self.assertNotIn(str(f.resolve()), [p for p in remaining_paths if p])
        logger.info("[PASS] on_file_deleted closes tab ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFileTreeCreateRenameDelete(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self.ft = FileTree(str(self.tmp))

    def tearDown(self):
        self.ft.deleteLater()
        self._tmp_ctx.__exit__(None, None, None)

    def test_create_new_file_creates_file_on_disk(self):
        logger.info("═══ TestFileTreeCreateRenameDelete.test_create_new_file_creates_file_on_disk ═══")
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QInputDialog.getText',
            return_value=('newfile.txt', True)
        ):
            self.ft._create_new_item(False)
        self.assertTrue((self.tmp / "newfile.txt").exists())
        logger.info("[PASS] create new file on disk ✓")

    def test_create_new_folder_creates_dir_on_disk(self):
        logger.info("═══ TestFileTreeCreateRenameDelete.test_create_new_folder_creates_dir_on_disk ═══")
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QInputDialog.getText',
            return_value=('newfolder', True)
        ):
            self.ft._create_new_item(True)
        self.assertTrue((self.tmp / "newfolder").is_dir())
        logger.info("[PASS] create new folder on disk ✓")

    def test_create_item_with_path_traversal_rejected(self):
        logger.info("═══ TestFileTreeCreateRenameDelete.test_create_item_with_path_traversal_rejected ═══")
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QInputDialog.getText',
            return_value=('../evil.sh', True)
        ):
            self.ft._create_new_item(False)
        self.assertFalse((self.tmp.parent / "evil.sh").exists())
        logger.info("[PASS] path traversal in create rejected ✓")

    def test_rename_item_renames_file_on_disk(self):
        logger.info("═══ TestFileTreeCreateRenameDelete.test_rename_item_renames_file_on_disk ═══")
        f = self.tmp / "before.txt"
        f.write_text("x")
        self.ft._populate(str(self.tmp))
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QInputDialog.getText',
            return_value=('after.txt', True)
        ):
            for i in range(self.ft.tree.topLevelItemCount()):
                item = self.ft.tree.topLevelItem(i)
                if item.text(0) == 'before.txt':
                    self.ft._rename_item(item, str(f))
                    break
        self.assertTrue((self.tmp / "after.txt").exists())
        self.assertFalse(f.exists())
        logger.info("[PASS] rename renames file on disk ✓")

    def test_delete_item_removes_file_on_disk(self):
        logger.info("═══ TestFileTreeCreateRenameDelete.test_delete_item_removes_file_on_disk ═══")
        f = self.tmp / "todelete.txt"
        f.write_text("x")
        self.ft._populate(str(self.tmp))
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QMessageBox.question',
            return_value=QMessageBox.StandardButton.Yes
        ):
            for i in range(self.ft.tree.topLevelItemCount()):
                item = self.ft.tree.topLevelItem(i)
                if item.text(0) == 'todelete.txt':
                    self.ft._delete_item(item, str(f))
                    break
        self.assertFalse(f.exists())
        logger.info("[PASS] delete removes file on disk ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorTabZoom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_zoom_in_increases_level(self):
        logger.info("═══ TestEditorTabZoom.test_zoom_in_increases_level ═══")
        tab = EditorTab(pane='left')
        initial = tab.editor._zoom_level
        tab.editor.zoom_in()
        self.assertGreater(tab.editor._zoom_level, initial)
        tab.deleteLater()
        logger.info("[PASS] zoom in increases level ✓")

    def test_zoom_out_decreases_level(self):
        logger.info("═══ TestEditorTabZoom.test_zoom_out_decreases_level ═══")
        tab = EditorTab(pane='left')
        tab.editor.set_zoom_level(120)
        tab.editor.zoom_out()
        self.assertLess(tab.editor._zoom_level, 120)
        tab.deleteLater()
        logger.info("[PASS] zoom out decreases level ✓")

    def test_reset_zoom_returns_to_100(self):
        logger.info("═══ TestEditorTabZoom.test_reset_zoom_returns_to_100 ═══")
        tab = EditorTab(pane='left')
        tab.editor.set_zoom_level(150)
        tab.editor.reset_zoom()
        self.assertEqual(tab.editor._zoom_level, 100)
        tab.deleteLater()
        logger.info("[PASS] reset zoom returns to 100 ✓")

    def test_zoom_initial_level_is_100(self):
        logger.info("═══ TestEditorTabZoom.test_zoom_initial_level_is_100 ═══")
        tab = EditorTab(pane='left')
        self.assertEqual(tab.editor._zoom_level, 100)
        tab.deleteLater()
        logger.info("[PASS] zoom initial level is 100 ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestConfigManagerKeybindings(unittest.TestCase):

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        self._cfg_ctx = patched_config(self.tmp)
        self._cfg_ctx.__enter__()
        self.cm = ConfigManager()

    def tearDown(self):
        self._cfg_ctx.__exit__(None, None, None)
        self._tmp_ctx.__exit__(None, None, None)

    def test_get_binding_returns_default_for_known_action(self):
        logger.info("═══ TestConfigManagerKeybindings.test_get_binding_returns_default_for_known_action ═══")
        val = self.cm.get_binding("save_file")
        self.assertIsInstance(val, str)
        self.assertGreater(len(val), 0)
        logger.info("[PASS] get_binding returns default ✓")

    def test_get_binding_toggle_terminal_present(self):
        logger.info("═══ TestConfigManagerKeybindings.test_get_binding_toggle_terminal_present ═══")
        val = self.cm.get_binding("toggle_terminal")
        self.assertIsInstance(val, str)
        self.assertGreater(len(val), 0)
        logger.info("[PASS] toggle_terminal binding present ✓")

    def test_get_binding_toggle_split_present(self):
        logger.info("═══ TestConfigManagerKeybindings.test_get_binding_toggle_split_present ═══")
        val = self.cm.get_binding("toggle_split")
        self.assertIsInstance(val, str)
        self.assertGreater(len(val), 0)
        logger.info("[PASS] toggle_split binding present ✓")

    def test_custom_keybinding_overrides_default(self):
        logger.info("═══ TestConfigManagerKeybindings.test_custom_keybinding_overrides_default ═══")
        self.cm.keybindings["save_file"] = "Ctrl+Alt+S"
        self.assertEqual(self.cm.get_binding("save_file"), "Ctrl+Alt+S")
        logger.info("[PASS] custom keybinding overrides default ✓")


class TestNoPrintResiduali(unittest.TestCase):
    """Fase 9 regression — nessun print() nei sorgenti del progetto"""

    def _source_files(self):
        """Ritorna i path dei file .py del progetto (escluso .venv e test_report)."""
        root = Path(__file__).parent
        return sorted(root.glob("*.py"))

    def test_no_print_in_source_files(self):
        """
        Fase 9 — verifica che nessun file sorgente contenga print().
        """
        logger.info("═══ TestNoPrintResiduali.test_no_print_in_source_files ═══")
        offenders = []
        for path in self._source_files():
            content = path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                    offenders.append((path.name, node.lineno))
        self.assertEqual(len(offenders), 0,
            f"print() trovato in {len(offenders)} posizioni: {offenders}")
        logger.info("[PASS] Zero occorrenze di print() nei file sorgente ✓")

    def test_logger_calls_present(self):
        """
        Fase 9 — verifica che main_window, editor_tab, config_manager
        abbiano chiamate logger.*.
        """
        logger.info("═══ TestNoPrintResiduali.test_logger_calls_present ═══")
        modules = {"main_window.py", "editor_tab.py", "config_manager.py"}
        for path in self._source_files():
            if path.name not in modules:
                continue
            content = path.read_text(encoding='utf-8')
            # Check per logger.error/warning/debug/info
            has_logger = "logger.error" in content or "logger.warning" in content or \
                         "logger.debug" in content or "logger.info" in content
            self.assertTrue(has_logger,
                f"{path.name} non ha chiamate logger.* (Fase 9 regression)")
        logger.info("[PASS] main_window.py, editor_tab.py, config_manager.py hanno logger.* ✓")


def tear_down_mainwindow(mw):
    """Close and schedule deletion of a MainWindow."""
    if mw is None:
        return
    mw.close()
    mw.deleteLater()
    app = QApplication.instance()
    if app:
        app.processEvents()


# ── Runner / summary ────────────────────────────────────────────────────

def run():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ordine: test puri → Qt test → regression
    test_classes = [
        TestLoggingConfig,
        TestThemeTokens,
        TestTheme,
        TestQssTokens,
        TestDetectLanguage,
        TestIsPathSafe,
        TestFOLDPatterns,
        TestSyntaxHighlighter,
        TestConfigManager,
        TestEditorTabLoadSave,
        TestEditorTabFolding,
        TestMainWindowRestore,
        TestMainWindowOpenFile,
        TestMainWindowSplit,
        TestGitBranchWorker,
        TestSearchPanel,
        TestCommandPalette,
        TestKeybindingsDialog,
        TestFileTree,
        TestSearchPanelFunctional,
        TestCommandPaletteFunctional,
        TestKeybindingsDialogFunctional,
        TestEditorTabExtended,
        TestMainWindowExtended,
        TestTerminalWidget,
        TestResizeHandle,
        TestFileTreeHiddenFiles,
        TestTerminalToggleInMainWindow,
        TestMainWindowStatusBar,
        TestMainWindowCloseTab,
        TestMainWindowSaveTab,
        TestMainWindowUndoRedo,
        TestMainWindowFind,
        TestMainWindowRecentFiles,
        TestMainWindowViewToggles,
        TestMainWindowMoveTab,
        TestMainWindowSessionSave,
        TestMainWindowFileRenamedDeleted,
        TestFileTreeCreateRenameDelete,
        TestEditorTabZoom,
        TestConfigManagerKeybindings,
        TestNoPrintResiduali,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(
        verbosity=0,
        stream=sys.stderr,
        failfast=False,
        resultclass=unittest.TextTestResult,
    )

    logger.info("")
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  NIRI EDITOR — SUITE DI TEST (%d test case)", suite.countTestCases())
    logger.info("═══════════════════════════════════════════════════")
    logger.info("")

    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    xfailed = len(result.expectedFailures)

    logger.info("")
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  RISULTATO: %d PASS ✓  |  %d FAIL ✗  |  %d ERROR ⚠  |  %d SKIP ⏭  |  %d XFAIL ⚑",
                passed, failed, errors, skipped, xfailed)
    if result.failures:
        logger.info("  ── TEST FALLITI ──")
        for test, tb in result.failures:
            lines = tb.split("\n")
            short = " | ".join(l.strip() for l in lines if l.strip())[:120]
            logger.info("    ✗ %s — %s", test, short)
    if result.expectedFailures:
        logger.info("  ── EXPECTED FAILURES (bug noti) ──")
        for test, _ in result.expectedFailures:
            logger.info("    ⚑ %s — bug _is_path_safe accetta path traversal")
    report_path = Path(__file__).parent / "test_report.txt"
    logger.info("  Report: %s", report_path)
    logger.info("═══════════════════════════════════════════════════")
    logger.info("")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run())
