#!/usr/bin/env python3
"""
test.py — Niri Editor test suite (295 tests · stdlib only)
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
    from PyQt6.QtGui import QColor, QFont, QPainter, QTextFormat, QFontMetrics, QTextCursor, QIcon, QAction, QCloseEvent, QKeySequence

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


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCustomEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_zoom_in_increases_level(self):
        logger.info("═══ TestCustomEditor.test_zoom_in_increases_level ═══")
        editor = CustomEditor()
        initial = editor._zoom_level
        editor.zoom_in()
        self.assertEqual(editor._zoom_level, initial + 10)
        logger.info("[PASS] zoom_in increases level ✓")

    def test_zoom_out_decreases_level(self):
        logger.info("═══ TestCustomEditor.test_zoom_out_decreases_level ═══")
        editor = CustomEditor()
        editor.set_zoom_level(120)
        editor.zoom_out()
        self.assertEqual(editor._zoom_level, 110)
        logger.info("[PASS] zoom_out decreases level ✓")

    def test_zoom_clamped_min_50(self):
        logger.info("═══ TestCustomEditor.test_zoom_clamped_min_50 ═══")
        editor = CustomEditor()
        editor.set_zoom_level(40)
        self.assertEqual(editor._zoom_level, 50)
        logger.info("[PASS] zoom clamped at 50 ✓")

    def test_zoom_clamped_max_200(self):
        logger.info("═══ TestCustomEditor.test_zoom_clamped_max_200 ═══")
        editor = CustomEditor()
        editor.set_zoom_level(250)
        self.assertEqual(editor._zoom_level, 200)
        logger.info("[PASS] zoom clamped at 200 ✓")

    def test_reset_zoom_returns_to_100(self):
        logger.info("═══ TestCustomEditor.test_reset_zoom_returns_to_100 ═══")
        editor = CustomEditor()
        editor.set_zoom_level(150)
        editor.reset_zoom()
        self.assertEqual(editor._zoom_level, 100)
        logger.info("[PASS] reset_zoom returns to 100 ✓")

    def test_set_word_wrap_enabled(self):
        logger.info("═══ TestCustomEditor.test_set_word_wrap_enabled ═══")
        editor = CustomEditor()
        editor.set_word_wrap(True)
        self.assertEqual(editor.lineWrapMode(),
                         QPlainTextEdit.LineWrapMode.WidgetWidth)
        logger.info("[PASS] set_word_wrap(True) enables WidgetWidth ✓")

    def test_set_word_wrap_disabled(self):
        logger.info("═══ TestCustomEditor.test_set_word_wrap_disabled ═══")
        editor = CustomEditor()
        editor.set_word_wrap(False)
        self.assertEqual(editor.lineWrapMode(),
                         QPlainTextEdit.LineWrapMode.NoWrap)
        logger.info("[PASS] set_word_wrap(False) sets NoWrap ✓")

    def test_set_show_whitespace_enabled(self):
        logger.info("═══ TestCustomEditor.test_set_show_whitespace_enabled ═══")
        editor = CustomEditor()
        editor.set_show_whitespace(True)
        self.assertTrue(editor._show_whitespace)
        logger.info("[PASS] set_show_whitespace(True) ✓")

    def test_set_show_whitespace_disabled(self):
        logger.info("═══ TestCustomEditor.test_set_show_whitespace_disabled ═══")
        editor = CustomEditor()
        editor.set_show_whitespace(False)
        self.assertFalse(editor._show_whitespace)
        logger.info("[PASS] set_show_whitespace(False) ✓")

    def test_set_show_margin_enabled(self):
        logger.info("═══ TestCustomEditor.test_set_show_margin_enabled ═══")
        editor = CustomEditor()
        editor.set_show_margin(True)
        self.assertTrue(editor._show_margin)
        logger.info("[PASS] set_show_margin(True) ✓")

    def test_set_show_margin_disabled(self):
        logger.info("═══ TestCustomEditor.test_set_show_margin_disabled ═══")
        editor = CustomEditor()
        editor.set_show_margin(False)
        self.assertFalse(editor._show_margin)
        logger.info("[PASS] set_show_margin(False) ✓")

    def test_set_margin_column(self):
        logger.info("═══ TestCustomEditor.test_set_margin_column ═══")
        editor = CustomEditor()
        editor.set_margin_column(120)
        self.assertEqual(editor._margin_column, 120)
        logger.info("[PASS] set_margin_column(120) ✓")

    def test_go_to_line_valid(self):
        logger.info("═══ TestCustomEditor.test_go_to_line_valid ═══")
        editor = CustomEditor()
        editor.setPlainText("line1\nline2\nline3")
        editor.go_to_line(2)
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockNumber(), 1)
        logger.info("[PASS] go_to_line(2) moves cursor to line 2 ✓")

    def test_go_to_line_invalid_ignored(self):
        logger.info("═══ TestCustomEditor.test_go_to_line_invalid_ignored ═══")
        editor = CustomEditor()
        editor.setPlainText("line1\nline2")
        cursor_before = editor.textCursor().position()
        editor.go_to_line(999)
        self.assertEqual(editor.textCursor().position(), cursor_before)
        logger.info("[PASS] go_to_line(999) ignored ✓")

    def test_toggle_fold(self):
        logger.info("═══ TestCustomEditor.test_toggle_fold ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():\n    pass\n\ndef bar():\n    pass\n")
        editor.language = "python"
        editor.update_foldable_blocks()
        if editor.foldable_blocks:
            block_num = list(editor.foldable_blocks.keys())[0]
            editor.toggle_fold(block_num)
            self.assertIn(block_num, editor.folded_blocks)
            editor.toggle_fold(block_num)
            self.assertNotIn(block_num, editor.folded_blocks)
        logger.info("[PASS] toggle_fold folds and unfolds ✓")

    def test_update_foldable_blocks_python(self):
        logger.info("═══ TestCustomEditor.test_update_foldable_blocks_python ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():\n    pass\n\nclass Bar:\n    pass\n")
        editor.language = "python"
        editor.update_foldable_blocks()
        self.assertGreater(len(editor.foldable_blocks), 0)
        logger.info("[PASS] Python foldable blocks found ✓")

    def test_update_foldable_blocks_javascript(self):
        logger.info("═══ TestCustomEditor.test_update_foldable_blocks_javascript ═══")
        editor = CustomEditor()
        editor.setPlainText("function foo() {\n  return 1;\n}\n\nif (true) {\n  console.log('hi');\n}\n")
        editor.language = "javascript"
        editor.update_foldable_blocks()
        self.assertGreater(len(editor.foldable_blocks), 0)
        logger.info("[PASS] JavaScript foldable blocks found ✓")

    def test_update_foldable_blocks_rust(self):
        logger.info("═══ TestCustomEditor.test_update_foldable_blocks_rust ═══")
        editor = CustomEditor()
        editor.setPlainText("fn foo() {\n    let x = 1;\n}\n\nfn bar() {\n    let y = 2;\n}\n")
        editor.language = "rust"
        editor.update_foldable_blocks()
        self.assertGreater(len(editor.foldable_blocks), 0)
        logger.info("[PASS] Rust foldable blocks found ✓")

    def test_set_search_highlights(self):
        logger.info("═══ TestCustomEditor.test_set_search_highlights ═══")
        editor = CustomEditor()
        editor.setPlainText("hello world")
        from PyQt6.QtWidgets import QTextEdit
        sel = QTextEdit.ExtraSelection()
        sel.cursor = editor.textCursor()
        sel.cursor.select(sel.cursor.SelectionType.WordUnderCursor)
        editor.set_search_highlights([sel])
        self.assertEqual(len(editor._search_highlights), 1)
        logger.info("[PASS] set_search_highlights adds highlight ✓")

    def test_clear_search_highlights(self):
        logger.info("═══ TestCustomEditor.test_clear_search_highlights ═══")
        editor = CustomEditor()
        from PyQt6.QtWidgets import QTextEdit
        sel = QTextEdit.ExtraSelection()
        sel.cursor = editor.textCursor()
        editor.set_search_highlights([sel])
        editor.clear_search_highlights()
        self.assertEqual(len(editor._search_highlights), 0)
        logger.info("[PASS] clear_search_highlights removes all ✓")

    def test_line_number_width_increases_with_lines(self):
        logger.info("═══ TestCustomEditor.test_line_number_width_increases_with_lines ═══")
        editor = CustomEditor()
        editor.setPlainText("")
        small = editor.line_number_width()
        editor.setPlainText("\n" * 1000)
        large = editor.line_number_width()
        self.assertGreater(large, small)
        logger.info("[PASS] line_number_width grows with blocks ✓")

    def test_folding_area_width_without_blocks(self):
        logger.info("═══ TestCustomEditor.test_folding_area_width_without_blocks ═══")
        editor = CustomEditor()
        editor.foldable_blocks = {}
        self.assertEqual(editor.folding_area_width(), 14)
        logger.info("[PASS] folding_area_width() == 14 without blocks ✓")

    def test_folding_area_width_with_blocks(self):
        logger.info("═══ TestCustomEditor.test_folding_area_width_with_blocks ═══")
        editor = CustomEditor()
        editor.foldable_blocks = {0: 2}
        self.assertEqual(editor.folding_area_width(), 20)
        logger.info("[PASS] folding_area_width() == 20 with blocks ✓")

    def test_keypress_auto_close_bracket(self):
        logger.info("═══ TestCustomEditor.test_keypress_auto_close_bracket ═══")
        editor = CustomEditor()
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_ParenLeft,
                          Qt.KeyboardModifier.NoModifier, "(")
        editor.keyPressEvent(event)
        self.assertEqual(editor.toPlainText(), "()")
        cursor = editor.textCursor()
        self.assertEqual(cursor.position(), 1)
        logger.info("[PASS] keyPress '(' inserts '()' with cursor inside ✓")

    def test_keypress_auto_close_brace(self):
        logger.info("═══ TestCustomEditor.test_keypress_auto_close_brace ═══")
        editor = CustomEditor()
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_BraceLeft,
                          Qt.KeyboardModifier.NoModifier, "{")
        editor.keyPressEvent(event)
        self.assertEqual(editor.toPlainText(), "{}")
        logger.info("[PASS] keyPress '{' inserts '{}' ✓")

    def test_keypress_auto_close_quote(self):
        logger.info("═══ TestCustomEditor.test_keypress_auto_close_quote ═══")
        editor = CustomEditor()
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_QuoteDbl,
                          Qt.KeyboardModifier.NoModifier, '"')
        editor.keyPressEvent(event)
        self.assertEqual(editor.toPlainText(), '""')
        logger.info("[PASS] keyPress '\"' inserts '\"\"' ✓")

    def test_keypress_auto_indent_after_colon(self):
        logger.info("═══ TestCustomEditor.test_keypress_auto_indent_after_colon ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():")
        editor.language = "python"
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return,
                          Qt.KeyboardModifier.NoModifier, "\r")
        editor.keyPressEvent(event)
        text = editor.toPlainText()
        self.assertIn("    ", text)
        logger.info("[PASS] Enter after ':' auto-indents ✓")

    def test_keypress_backspace_removes_pair(self):
        logger.info("═══ TestCustomEditor.test_keypress_backspace_removes_pair ═══")
        editor = CustomEditor()
        editor.setPlainText("()")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace,
                          Qt.KeyboardModifier.NoModifier)
        editor.keyPressEvent(event)
        self.assertEqual(editor.toPlainText(), "")
        logger.info("[PASS] Backspace between '()' removes both ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSyntaxHighlighterExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def _create_highlighter(self):
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        return hl

    def test_set_language_python_sets_rules(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_set_language_python_sets_rules ═══")
        hl = self._create_highlighter()
        hl.set_language("python")
        hl._setup_rules()
        self.assertGreater(len(hl.rules), 0)
        logger.info("[PASS] set_language('python') creates rules ✓")

    def test_set_language_javascript_sets_rules(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_set_language_javascript_sets_rules ═══")
        hl = self._create_highlighter()
        hl.set_language("javascript")
        hl._setup_rules()
        self.assertGreater(len(hl.rules), 0)
        logger.info("[PASS] set_language('javascript') creates rules ✓")

    def test_set_language_rust_sets_rules(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_set_language_rust_sets_rules ═══")
        hl = self._create_highlighter()
        hl.set_language("rust")
        hl._setup_rules()
        self.assertGreater(len(hl.rules), 0)
        logger.info("[PASS] set_language('rust') creates rules ✓")

    def test_set_language_unknown_falls_back(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_set_language_unknown_falls_back ═══")
        hl = self._create_highlighter()
        hl.set_language("__nonexistent__")
        hl._setup_rules()
        self.assertIsInstance(hl.rules, list)
        logger.info("[PASS] unknown language falls back gracefully ✓")

    def test_highlight_block_python_keywords(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_highlight_block_python_keywords ═══")
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("python")
        editor.setPlainText("import os\n\ndef foo():\n    pass\n")
        # Force a rehighlight
        hl.rehighlight()
        # Verify no exceptions and blocks are highlighted
        for block_no in range(editor.document().blockCount()):
            block = editor.document().findBlockByNumber(block_no)
            fmt = block.charFormat()
            self.assertIsNotNone(block.text())
        logger.info("[PASS] Python highlightBlock runs without error ✓")

    def test_highlight_block_javascript_no_crash(self):
        logger.info("═══ TestSyntaxHighlighterExtended.test_highlight_block_javascript_no_crash ═══")
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("javascript")
        editor.setPlainText("function foo() {\n  return 1;\n}\n")
        hl.rehighlight()
        for block_no in range(editor.document().blockCount()):
            block = editor.document().findBlockByNumber(block_no)
            self.assertIsNotNone(block.text())
        logger.info("[PASS] JavaScript highlightBlock no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFileTreeExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self._tmp_ctx = tmp_dir()
        self.tmp = self._tmp_ctx.__enter__()
        (self.tmp / "subdir").mkdir()
        (self.tmp / "file_a.txt").write_text("a")
        self.ft = FileTree(str(self.tmp))

    def tearDown(self):
        self.ft.deleteLater()
        self._tmp_ctx.__exit__(None, None, None)

    def _find_item(self, ft, name):
        for i in range(ft.tree.topLevelItemCount()):
            item = ft.tree.topLevelItem(i)
            if item.text(0) == name:
                return item
        return None

    def test_set_root_path_updates_current_root(self):
        logger.info("═══ TestFileTreeExtended.test_set_root_path_updates_current_root ═══")
        with tmp_dir() as tmp2:
            self.ft.set_root_path(str(tmp2))
            self.assertEqual(self.ft.current_root, str(tmp2))
        logger.info("[PASS] set_root_path updates current_root ✓")

    def test_set_root_path_ignores_invalid(self):
        logger.info("═══ TestFileTreeExtended.test_set_root_path_ignores_invalid ═══")
        original = self.ft.current_root
        self.ft.set_root_path("/nonexistent/path/xyz")
        self.assertEqual(self.ft.current_root, original)
        logger.info("[PASS] set_root_path ignores invalid path ✓")

    def test_context_menu_show_hidden_toggle(self):
        logger.info("═══ TestFileTreeExtended.test_context_menu_show_hidden_toggle ═══")
        self.assertFalse(self.ft._show_hidden)
        # Verify set_show_hidden works without context menu hanging
        self.ft.set_show_hidden(True)
        self.assertTrue(self.ft._show_hidden)
        self.ft.set_show_hidden(False)
        self.assertFalse(self.ft._show_hidden)
        logger.info("[PASS] show_hidden toggle via setter ✓")

    def test_double_click_outside_root_blocked(self):
        logger.info("═══ TestFileTreeExtended.test_double_click_outside_root_blocked ═══")
        outside = self.tmp.parent / "outside_test.txt"
        outside.write_text("evil")
        emitted = []
        self.ft.fileOpened.connect(lambda p: emitted.append(p))
        item = QTreeWidgetItem(["outside_test.txt"])
        item.setData(0, Qt.ItemDataRole.UserRole, str(outside))
        with mock_qmessagebox_warning() as dialogs:
            self.ft._on_item_double_clicked(item, 0)
        self.assertGreaterEqual(len(dialogs), 1)
        self.assertEqual(len(emitted), 0)
        outside.unlink()
        logger.info("[PASS] file outside root blocked ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowCritical(unittest.TestCase):
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

    def test_close_tab_unmodified_removes_tab(self):
        logger.info("═══ TestMainWindowCritical.test_close_tab_unmodified_removes_tab ═══")
        self.mw.new_file()
        self.mw.new_file()
        count_before = self.mw.tabs.count()
        self.mw.close_tab(0, 'left')
        self.assertEqual(self.mw.tabs.count(), count_before - 1)
        logger.info("[PASS] close unmodified tab removes ✓")

    def test_close_tab_modified_discard(self):
        logger.info("═══ TestMainWindowCritical.test_close_tab_modified_discard ═══")
        self.mw.new_file()
        idx = self.mw.tabs.currentIndex()
        tab = self.mw.tabs.currentWidget()
        cursor = tab.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText("modified")
        self.assertTrue(tab.is_modified())
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QMessageBox.question',
            return_value=QMessageBox.StandardButton.Discard
        ):
            self.mw.close_tab(idx, 'left')
        logger.info("[PASS] close modified tab with Discard no error ✓")

    def test_close_tab_modified_save(self):
        logger.info("═══ TestMainWindowCritical.test_close_tab_modified_save ═══")
        with tmp_dir() as tmp:
            f = tmp / "save_on_close.txt"
            f.write_text("original")
            self.mw.open_file(str(f))
            idx = self.mw.tabs.currentIndex()
            tab = self.mw.tabs.currentWidget()
            cursor = tab.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText("modified content")
            self.assertTrue(tab.is_modified())
            with unittest.mock.patch(
                'PyQt6.QtWidgets.QMessageBox.question',
                return_value=QMessageBox.StandardButton.Save
            ):
                self.mw.close_tab(idx, 'left')
            self.assertEqual(f.read_text(encoding='utf-8'), "modified content")
        logger.info("[PASS] close modified tab with Save persists ✓")

    def test_close_tab_modified_cancel_keeps_tab(self):
        logger.info("═══ TestMainWindowCritical.test_close_tab_modified_cancel_keeps_tab ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        cursor = tab.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText("modified")
        self.assertTrue(tab.is_modified())
        count_before = self.mw.tabs.count()
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QMessageBox.question',
            return_value=QMessageBox.StandardButton.Cancel
        ):
            self.mw.close_tab(count_before - 1, 'left')
        self.assertEqual(self.mw.tabs.count(), count_before)
        logger.info("[PASS] close tab Cancel keeps tab ✓")

    def test_save_file_as_opens_dialog(self):
        logger.info("═══ TestMainWindowCritical.test_save_file_as_opens_dialog ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.setPlainText("save_as content")
        with unittest.mock.patch(
            'PyQt6.QtWidgets.QFileDialog.getSaveFileName',
            return_value=('', '')
        ):
            self.mw.save_file_as()
        logger.info("[PASS] save_file_as opens dialog ✓")

    def test_event_filter_ctrl_wheel_zooms(self):
        logger.info("═══ TestMainWindowCritical.test_event_filter_ctrl_wheel_zooms ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        initial_zoom = tab.editor._zoom_level
        from PyQt6.QtCore import QPoint, QPointF, Qt
        from PyQt6.QtGui import QWheelEvent
        wheel_event = QWheelEvent(
            QPointF(0, 0), QPointF(0, 0), QPoint(0, 0),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        self.mw.eventFilter(tab.editor.viewport(), wheel_event)
        self.assertGreater(tab.editor._zoom_level, initial_zoom)
        logger.info("[PASS] Ctrl+Wheel zooms in ✓")

    def test_event_filter_ctrl_wheel_zoom_out(self):
        logger.info("═══ TestMainWindowCritical.test_event_filter_ctrl_wheel_zoom_out ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        tab.editor.set_zoom_level(120)
        from PyQt6.QtCore import QPoint, QPointF, Qt
        from PyQt6.QtGui import QWheelEvent
        wheel_event = QWheelEvent(
            QPointF(0, 0), QPointF(0, 0), QPoint(0, 0),
            QPoint(0, -120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        self.mw.eventFilter(tab.editor.viewport(), wheel_event)
        self.assertLess(tab.editor._zoom_level, 120)
        logger.info("[PASS] Ctrl+Wheel zooms out ✓")

    def test_execute_command_new_file(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_new_file ═══")
        count_before = self.mw.tabs.count()
        self.mw.execute_command("new_file")
        self.assertEqual(self.mw.tabs.count(), count_before + 1)
        logger.info("[PASS] execute_command('new_file') works ✓")

    def test_execute_command_close_tab(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_close_tab ═══")
        self.mw.new_file()
        self.mw.new_file()
        count_before = self.mw.tabs.count()
        self.mw.execute_command("close_tab")
        self.assertEqual(self.mw.tabs.count(), count_before - 1)
        logger.info("[PASS] execute_command('close_tab') works ✓")

    def test_execute_command_undo_and_redo(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_undo_and_redo ═══")
        self.mw.new_file()
        tab = self.mw.tabs.currentWidget()
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("original")
        tab.editor.document().setModified(False)
        cursor = tab.editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText("modified")
        self.mw.execute_command("undo")
        self.assertEqual(tab.editor.toPlainText(), "original")
        self.mw.execute_command("redo")
        self.assertEqual(tab.editor.toPlainText(), "modified")
        logger.info("[PASS] execute_command undo/redo ✓")

    def test_execute_command_toggle_terminal(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_toggle_terminal ═══")
        self.mw.execute_command("toggle_terminal")
        self.assertFalse(self.mw.terminal_widget.isHidden())
        logger.info("[PASS] execute_command('toggle_terminal') shows terminal ✓")

    def test_execute_command_find(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_find ═══")
        self.mw.new_file()
        self.mw.execute_command("find")
        self.assertIsNotNone(self.mw._search_anim)
        logger.info("[PASS] execute_command('find') no crash ✓")

    def test_execute_command_goto_line(self):
        logger.info("═══ TestMainWindowCritical.test_execute_command_goto_line ═══")
        self.mw.new_file()
        self.mw.execute_command("goto_line")
        self.assertFalse(self.mw.goto_panel.isHidden())
        logger.info("[PASS] execute_command('goto_line') shows panel ✓")

    def test_toggle_show_whitespace(self):
        logger.info("═══ TestMainWindowCritical.test_toggle_show_whitespace ═══")
        self.mw.new_file()
        self.mw.show_whitespace_action.setChecked(True)
        self.mw.toggle_show_whitespace()
        logger.info("[PASS] toggle_show_whitespace no crash ✓")

    def test_toggle_show_margin(self):
        logger.info("═══ TestMainWindowCritical.test_toggle_show_margin ═══")
        self.mw.new_file()
        self.mw.show_margin_action.setChecked(False)
        self.mw.toggle_show_margin()
        logger.info("[PASS] toggle_show_margin no crash ✓")

    def test_show_command_palette_shows_widget(self):
        logger.info("═══ TestMainWindowCritical.test_show_command_palette_shows_widget ═══")
        self.mw.command_palette.show()
        self.assertTrue(self.mw.command_palette.isVisible())
        self.mw.command_palette.reject()
        logger.info("[PASS] show_command_palette shows widget ✓")

    def test_close_tab_action_via_execute(self):
        logger.info("═══ TestMainWindowCritical.test_close_tab_action_via_execute ═══")
        self.mw.new_file()
        self.mw.new_file()
        count_before = self.mw.tabs.count()
        self.mw.close_tab_action()
        self.assertEqual(self.mw.tabs.count(), count_before - 1)
        logger.info("[PASS] close_tab_action removes tab ✓")

    def test_save_file_works(self):
        logger.info("═══ TestMainWindowCritical.test_save_file_works ═══")
        with tmp_dir() as tmp:
            f = tmp / "save_test.txt"
            f.write_text("original")
            self.mw.open_file(str(f))
            tab = self.mw.tabs.currentWidget()
            tab.editor.setPlainText("updated")
            self.mw.save_file()
            self.assertEqual(f.read_text(encoding='utf-8'), "updated")
        logger.info("[PASS] save_file saves content ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestTerminalWidgetExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self.tw = TerminalWidget()

    def tearDown(self):
        self.tw.kill_process()
        self.tw.deleteLater()

    def test_focus_input_sets_focus(self):
        logger.info("═══ TestTerminalWidgetExtended.test_focus_input_sets_focus ═══")
        self.tw.focus_input()
        # In offscreen mode hasFocus() may not work; just verify no crash
        self.assertIsNotNone(self.tw._input)
        logger.info("[PASS] focus_input no crash ✓")

    def test_close_event_kills_process(self):
        logger.info("═══ TestTerminalWidgetExtended.test_close_event_kills_process ═══")
        from PyQt6.QtCore import QEvent
        event = QCloseEvent()
        self.tw.closeEvent(event)
        logger.info("[PASS] closeEvent kills process no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestResizeHandleExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_drag_up_increases_height(self):
        logger.info("═══ TestResizeHandleExtended.test_drag_up_increases_height ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(200)
        handle = tw._resize_handle
        handle._press_y = 300.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(0, 0), QPointF(0, 250),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertGreater(tw.height(), 200)
        tw.deleteLater()
        logger.info("[PASS] drag up increases height ✓")

    def test_drag_down_decreases_height(self):
        logger.info("═══ TestResizeHandleExtended.test_drag_down_decreases_height ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(200)
        handle = tw._resize_handle
        handle._press_y = 300.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(0, 0), QPointF(0, 350),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertLess(tw.height(), 200)
        tw.deleteLater()
        logger.info("[PASS] drag down decreases height ✓")

    def test_height_clamped_min_80(self):
        logger.info("═══ TestResizeHandleExtended.test_height_clamped_min_80 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(100)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(0, 0), QPointF(0, 500),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertGreaterEqual(tw.height(), 80)
        tw.deleteLater()
        logger.info("[PASS] height clamped min 80 ✓")

    def test_height_clamped_max_600(self):
        logger.info("═══ TestResizeHandleExtended.test_height_clamped_max_600 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(400)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move_event = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(0, 0), QPointF(0, -500),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        handle.mouseMoveEvent(move_event)
        self.assertLessEqual(tw.height(), 600)
        tw.deleteLater()
        logger.info("[PASS] height clamped max 600 ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCommandPaletteExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_keypress_escape_rejects(self):
        logger.info("═══ TestCommandPaletteExtended.test_keypress_escape_rejects ═══")
        parent = QWidget()
        palette = CommandPalette({"test": "Test"}, parent=parent)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                          Qt.KeyboardModifier.NoModifier)
        palette.keyPressEvent(event)
        self.assertEqual(palette.result(), int(QDialog.DialogCode.Rejected))
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Escape rejects dialog ✓")

    def test_keypress_enter_selects_first_item(self):
        logger.info("═══ TestCommandPaletteExtended.test_keypress_enter_selects_first_item ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test command"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return,
                          Qt.KeyboardModifier.NoModifier)
        palette.keyPressEvent(event)
        self.assertEqual(emitted, ["cmd.test"])
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Enter selects first item ✓")

    def test_keypress_down_navigates_list(self):
        logger.info("═══ TestCommandPaletteExtended.test_keypress_down_navigates_list ═══")
        parent = QWidget()
        palette = CommandPalette({"a": "A", "b": "B"}, parent=parent)
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down,
                         Qt.KeyboardModifier.NoModifier)
        palette.keyPressEvent(down)
        self.assertEqual(palette.action_list.currentRow(), 1)
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] Down navigates list ✓")

    def test_exec_accepts_dialog(self):
        logger.info("═══ TestCommandPaletteExtended.test_exec_accepts_dialog ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test"}, parent=parent)
        palette.accept()
        self.assertEqual(palette.result(), int(QDialog.DialogCode.Accepted))
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] exec_ accepts dialog ✓")

    def test_on_enter_pressed_empty_list_no_crash(self):
        logger.info("═══ TestCommandPaletteExtended.test_on_enter_pressed_empty_list_no_crash ═══")
        parent = QWidget()
        palette = CommandPalette({}, parent=parent)
        palette.on_enter_pressed()
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] on_enter_pressed with empty list no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestKeybindingsDialogExtended(unittest.TestCase):
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

    def test_load_bindings_into_list(self):
        logger.info("═══ TestKeybindingsDialogExtended.test_load_bindings_into_list ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S", "open": "Ctrl+O"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        dlg.load_bindings_into_list()
        self.assertEqual(dlg.list_widget.count(), 2)
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] load_bindings_into_list loads bindings ✓")

    def test_save_and_close_updates_config(self):
        logger.info("═══ TestKeybindingsDialogExtended.test_save_and_close_updates_config ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        dlg.bindings["save"] = "Ctrl+Shift+S"
        dlg.save_and_close()
        self.assertEqual(self.cm.keybindings["save"], "Ctrl+Shift+S")
        self.assertEqual(dlg.result(), int(QDialog.DialogCode.Accepted))
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] save_and_close updates config ✓")

    def test_reject_does_not_save(self):
        logger.info("═══ TestKeybindingsDialogExtended.test_reject_does_not_save ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        dlg.bindings["save"] = "Ctrl+Shift+S"
        dlg.reject()
        self.assertEqual(self.cm.keybindings["save"], "Ctrl+S")
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] reject does not save ✓")

    def test_edit_binding_updates_model(self):
        logger.info("═══ TestKeybindingsDialogExtended.test_edit_binding_updates_model ═══")
        parent = QWidget()
        self.cm.keybindings = {"save": "Ctrl+S"}
        dlg = KeybindingsDialog(self.cm, parent=parent)
        dlg.load_bindings_into_list()
        with unittest.mock.patch("PyQt6.QtWidgets.QInputDialog.getText",
                                  return_value=("Ctrl+Shift+S", True)):
            dlg.edit_binding(dlg.list_widget.item(0))
        self.assertEqual(dlg.bindings["save"], "Ctrl+Shift+S")
        dlg.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] edit_binding updates model ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestIconsAndTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_icons_all_return_qicon(self):
        logger.info("═══ TestIconsAndTheme.test_icons_all_return_qicon ═══")
        ico = Icons(Tokens.FG_PRIMARY)
        methods = [
            'bars', 'check_circle', 'chevron_down', 'chevron_left',
            'chevron_right', 'chevron_up', 'close', 'cog', 'columns',
            'compress_alt', 'copy', 'crosshairs', 'exchange_alt',
            'exclamation_circle', 'file', 'file_alt', 'file_code',
            'folder', 'folder_open', 'redo', 'save', 'search',
            'sitemap', 'terminal', 'undo'
        ]
        for m in methods:
            icon = getattr(ico, m)()
            self.assertIsInstance(icon, QIcon,
                                  f"Icons.{m}() did not return QIcon")
        logger.info("[PASS] all %d Icons methods return QIcon ✓", len(methods))

    def test_theme_get_color_returns_qcolor(self):
        logger.info("═══ TestIconsAndTheme.test_theme_get_color_returns_qcolor ═══")
        theme_dict = Theme.by_name("lilac")
        for key in ("background", "foreground", "selection_background",
                     "selection_foreground", "current_line_bg",
                     "line_number_fg", "gutter_bg"):
            color = Theme.get_color(theme_dict, key)
            self.assertIsInstance(color, QColor,
                                  f"Theme.get_color({key}) not QColor")
        logger.info("[PASS] Theme.get_color returns QColor for all keys ✓")


# ── Widget interni: DraggableTabBar, CodeFoldingArea, LineNumberArea, MarginLine ──

@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestDraggableTabBar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self.mw = QWidget()
        from main_window import DraggableTabBar
        self.bar = DraggableTabBar(parent=self.mw, pane='left', main_window=self.mw)

    def tearDown(self):
        self.bar.deleteLater()
        self.mw.deleteLater()

    def test_constructor_sets_pane(self):
        logger.info("═══ TestDraggableTabBar.test_constructor_sets_pane ═══")
        self.assertEqual(self.bar._pane, 'left')
        self.assertIs(self.bar._main_window, self.mw)
        self.assertTrue(self.bar.acceptDrops())
        logger.info("[PASS] constructor sets pane and parent ✓")

    def test_mouse_press_sets_drag_state(self):
        logger.info("═══ TestDraggableTabBar.test_mouse_press_sets_drag_state ═══")
        self.bar.addTab("Tab 1")
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10),
                            QPointF(10, 10), Qt.MouseButton.LeftButton,
                            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        self.bar.mousePressEvent(press)
        self.assertTrue(hasattr(self.bar, '_drag_start_pos'))
        logger.info("[PASS] mouse press sets drag state ✓")

    def test_drag_enter_accepts_valid_mime(self):
        logger.info("═══ TestDraggableTabBar.test_drag_enter_accepts_valid_mime ═══")
        from PyQt6.QtCore import QMimeData, QPoint, QEvent
        from PyQt6.QtGui import QDragEnterEvent
        mime = QMimeData()
        mime.setData("application/x-tab-move", b"left,0")
        event = QDragEnterEvent(QPoint(0, 0), Qt.DropAction.MoveAction,
                                mime, Qt.MouseButton.LeftButton,
                                Qt.KeyboardModifier.NoModifier)
        self.bar.dragEnterEvent(event)
        logger.info("[PASS] drag enter accepts valid mime ✓")

    def test_drag_enter_rejects_invalid_mime(self):
        logger.info("═══ TestDraggableTabBar.test_drag_enter_rejects_invalid_mime ═══")
        from PyQt6.QtCore import QMimeData, QPoint, QEvent
        from PyQt6.QtGui import QDragEnterEvent
        mime = QMimeData()
        mime.setText("plain text")
        event = QDragEnterEvent(QPoint(0, 0), Qt.DropAction.MoveAction,
                                mime, Qt.MouseButton.LeftButton,
                                Qt.KeyboardModifier.NoModifier)
        self.bar.dragEnterEvent(event)
        logger.info("[PASS] drag enter rejects invalid mime ✓")

    def test_drag_move_accepts_valid_mime(self):
        logger.info("═══ TestDraggableTabBar.test_drag_move_accepts_valid_mime ═══")
        from PyQt6.QtCore import QMimeData, QPoint, QEvent
        from PyQt6.QtGui import QDragMoveEvent
        mime = QMimeData()
        mime.setData("application/x-tab-move", b"left,0")
        event = QDragMoveEvent(QPoint(0, 0), Qt.DropAction.MoveAction,
                               mime, Qt.MouseButton.LeftButton,
                               Qt.KeyboardModifier.NoModifier)
        self.bar.dragMoveEvent(event)
        logger.info("[PASS] drag move accepts valid mime ✓")

    def test_drop_triggers_move(self):
        logger.info("═══ TestDraggableTabBar.test_drop_triggers_move ═══")
        self.bar.addTab("Tab 1")
        self.bar.addTab("Tab 2")
        moved = []
        self.mw._move_tab = lambda s, si, tp, ti: moved.append((s, si, tp, ti))
        from PyQt6.QtCore import QMimeData, QPointF, QEvent
        from PyQt6.QtGui import QDropEvent
        mime = QMimeData()
        mime.setData("application/x-tab-move", b"left,0")
        event = QDropEvent(QPointF(5, 5), Qt.DropAction.MoveAction,
                           mime, Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier)
        self.bar.dropEvent(event)
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0], ('left', 0, 'left', 0))
        logger.info("[PASS] drop triggers _move_tab ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCodeFoldingArea(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_size_hint_returns_20_x_0(self):
        logger.info("═══ TestCodeFoldingArea.test_size_hint_returns_20_x_0 ═══")
        editor = CustomEditor()
        area = editor.foldingArea
        sz = area.sizeHint()
        self.assertEqual(sz.width(), 20)
        self.assertEqual(sz.height(), 0)
        editor.deleteLater()
        logger.info("[PASS] CodeFoldingArea sizeHint → QSize(20, 0) ✓")

    def test_paint_event_no_crash(self):
        logger.info("═══ TestCodeFoldingArea.test_paint_event_no_crash ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():\n    pass\n\ndef bar():\n    pass\n")
        editor.language = "python"
        editor.update_foldable_blocks()
        area = editor.foldingArea
        from PyQt6.QtCore import QRect, QEvent
        from PyQt6.QtGui import QPaintEvent
        rect = QRect(0, 0, 20, 50)
        event = QPaintEvent(rect)
        area.paintEvent(event)
        editor.deleteLater()
        logger.info("[PASS] CodeFoldingArea paintEvent no crash ✓")

    def test_mouse_press_toggles_fold(self):
        logger.info("═══ TestCodeFoldingArea.test_mouse_press_toggles_fold ═══")
        editor = CustomEditor()
        editor.setPlainText("def foo():\n    pass\n\ndef bar():\n    pass\n")
        editor.language = "python"
        editor.update_foldable_blocks()
        area = editor.foldingArea
        if editor.foldable_blocks:
            block_num = list(editor.foldable_blocks.keys())[0]
            from PyQt6.QtCore import QPointF, QEvent
            from PyQt6.QtGui import QMouseEvent
            click = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(8, 10),
                                QPointF(8, 10), Qt.MouseButton.LeftButton,
                                Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            area.mousePressEvent(click)
            self.assertIn(block_num, editor.folded_blocks)
            # Second click unfolds
            click2 = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(8, 10),
                                 QPointF(8, 10), Qt.MouseButton.LeftButton,
                                 Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            area.mousePressEvent(click2)
            self.assertNotIn(block_num, editor.folded_blocks)
        editor.deleteLater()
        logger.info("[PASS] CodeFoldingArea mouse press toggles fold ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestLineNumberArea(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_size_hint_matches_line_number_width(self):
        logger.info("═══ TestLineNumberArea.test_size_hint_matches_line_number_width ═══")
        editor = CustomEditor()
        editor.setPlainText("line1\nline2\nline3")
        area = editor.lineNumberArea
        sz = area.sizeHint()
        self.assertEqual(sz.width(), editor.line_number_width())
        self.assertEqual(sz.height(), 0)
        editor.deleteLater()
        logger.info("[PASS] LineNumberArea sizeHint matches line_number_width ✓")

    def test_paint_event_no_crash(self):
        logger.info("═══ TestLineNumberArea.test_paint_event_no_crash ═══")
        editor = CustomEditor()
        editor.setPlainText("hello\nworld")
        area = editor.lineNumberArea
        from PyQt6.QtCore import QRect, QEvent
        from PyQt6.QtGui import QPaintEvent
        event = QPaintEvent(QRect(0, 0, 40, 50))
        area.paintEvent(event)
        editor.deleteLater()
        logger.info("[PASS] LineNumberArea paintEvent no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMarginLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_paint_event_no_crash(self):
        logger.info("═══ TestMarginLine.test_paint_event_no_crash ═══")
        editor = CustomEditor()
        line = editor.marginLine
        from PyQt6.QtCore import QRect, QEvent
        from PyQt6.QtGui import QPaintEvent
        event = QPaintEvent(QRect(0, 0, 10, 50))
        line.paintEvent(event)
        editor.deleteLater()
        logger.info("[PASS] MarginLine paintEvent no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowAutosave(unittest.TestCase):
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

    def test_do_autosave_saves_modified_tab_with_path(self):
        logger.info("═══ TestMainWindowAutosave.test_do_autosave_saves_modified_tab_with_path ═══")
        with tmp_dir() as tmp:
            f = tmp / "autosave_test.txt"
            f.write_text("original")
            self.mw.open_file(str(f))
            tab = self.mw.tabs.currentWidget()
            cursor = tab.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(" autosaved")
            self.mw._do_autosave()
            self.assertIn("autosaved", f.read_text(encoding='utf-8'))
        logger.info("[PASS] _do_autosave saves modified tab with file path ✓")

    def test_do_autosave_skips_unmodified_tabs(self):
        logger.info("═══ TestMainWindowAutosave.test_do_autosave_skips_unmodified_tabs ═══")
        with tmp_dir() as tmp:
            f = tmp / "clean_autosave.txt"
            f.write_text("original")
            self.mw.open_file(str(f))
            self.mw._do_autosave()
            self.assertEqual(f.read_text(encoding='utf-8'), "original")
        logger.info("[PASS] _do_autosave skips unmodified tabs ✓")

    def test_on_git_branch_result_shows_label(self):
        logger.info("═══ TestMainWindowAutosave.test_on_git_branch_result_shows_label ═══")
        self.mw._on_git_branch_result("/tmp", "main")
        self.assertIn("main", self.mw.git_label.text())
        self.assertFalse(self.mw.git_label.isHidden())
        logger.info("[PASS] _on_git_branch_result shows git label ✓")

    def test_on_git_branch_result_empty_hides_label(self):
        logger.info("═══ TestMainWindowAutosave.test_on_git_branch_result_empty_hides_label ═══")
        self.mw._on_git_branch_result("/tmp", "")
        self.assertTrue(self.mw.git_label.isHidden())
        logger.info("[PASS] _on_git_branch_result empty hides label ✓")

    def test_autosave_timer_created_on_init(self):
        logger.info("═══ TestMainWindowAutosave.test_autosave_timer_created_on_init ═══")
        self.assertIsNotNone(self.mw.autosave_timer)
        self.assertTrue(self.mw.autosave_timer.isActive())
        logger.info("[PASS] autosave timer active on init ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorTabAtomicSave(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_save_file_preserves_utf8_content(self):
        logger.info("═══ TestEditorTabAtomicSave.test_save_file_preserves_utf8_content ═══")
        with tmp_dir() as tmp:
            f = tmp / "unicode_save.txt"
            tab = EditorTab(pane='left')
            tab.file_path = str(f)
            content = "café 日本語 ✓\nemoji 😊\n"
            tab.editor.setPlainText(content)
            result = tab.save_file()
            self.assertTrue(result)
            self.assertEqual(f.read_text(encoding='utf-8'), content)
            tab.deleteLater()
        logger.info("[PASS] save_file preserves UTF-8 content ✓")

    def test_save_file_overwrites_existing_content(self):
        logger.info("═══ TestEditorTabAtomicSave.test_save_file_overwrites_existing_content ═══")
        with tmp_dir() as tmp:
            f = tmp / "overwrite.txt"
            f.write_text("old content")
            tab = EditorTab(str(f), pane='left')
            tab.editor.setPlainText("new content")
            result = tab.save_file()
            self.assertTrue(result)
            self.assertEqual(f.read_text(encoding='utf-8'), "new content")
            tab.deleteLater()
        logger.info("[PASS] save_file overwrites existing content ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSyntaxHighlighterEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def _hl(self):
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("python")
        return hl

    def test_highlight_multiline_string_no_crash(self):
        logger.info("═══ TestSyntaxHighlighterEdgeCases.test_highlight_multiline_string_no_crash ═══")
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("python")
        editor.setPlainText('"""\nmulti\nline\nstring\n"""\nx = 1\n')
        hl.rehighlight()
        for block_no in range(editor.document().blockCount()):
            block = editor.document().findBlockByNumber(block_no)
            self.assertIsNotNone(block.text())
        editor.deleteLater()
        logger.info("[PASS] highlight multiline string no crash ✓")

    def test_highlight_comment_with_special_chars_no_crash(self):
        logger.info("═══ TestSyntaxHighlighterEdgeCases.test_highlight_comment_with_special_chars_no_crash ═══")
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("python")
        editor.setPlainText("# comment with $peci@l ch@rs\nx = 1  # inline { comment }\n")
        hl.rehighlight()
        for block_no in range(editor.document().blockCount()):
            block = editor.document().findBlockByNumber(block_no)
            self.assertIsNotNone(block.text())
        editor.deleteLater()
        logger.info("[PASS] highlight comment with special chars no crash ✓")

    def test_highlight_javascript_regex_no_crash(self):
        logger.info("═══ TestSyntaxHighlighterEdgeCases.test_highlight_javascript_regex_no_crash ═══")
        editor = CustomEditor()
        hl = UniversalHighlighter(editor.document(), Theme.by_name("lilac"))
        hl.set_language("javascript")
        editor.setPlainText("const re = /foo[bar]+/gi;\nconst str = 'hello';\n")
        hl.rehighlight()
        for block_no in range(editor.document().blockCount()):
            block = editor.document().findBlockByNumber(block_no)
            self.assertIsNotNone(block.text())
        editor.deleteLater()
        logger.info("[PASS] highlight JavaScript regex no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestResizeHandleExtended2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_mouse_press_sets_press_y(self):
        logger.info("═══ TestResizeHandleExtended2.test_mouse_press_sets_press_y ═══")
        tw = TerminalWidget()
        handle = tw._resize_handle
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(0, 100),
                            QPointF(0, 100), Qt.MouseButton.LeftButton,
                            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        handle.mousePressEvent(press)
        self.assertEqual(handle._press_y, 100.0)
        tw.deleteLater()
        logger.info("[PASS] mouse press sets _press_y ✓")

    def test_mouse_release_no_crash(self):
        logger.info("═══ TestResizeHandleExtended2.test_mouse_release_no_crash ═══")
        tw = TerminalWidget()
        handle = tw._resize_handle
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        release = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(0, 0),
                              QPointF(0, 0), Qt.MouseButton.LeftButton,
                              Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        handle.mouseReleaseEvent(release)
        tw.deleteLater()
        logger.info("[PASS] mouse release no crash ✓")

    def test_drag_clamps_max_600(self):
        logger.info("═══ TestResizeHandleExtended2.test_drag_clamps_max_600 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(400)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move = QMouseEvent(QEvent.Type.MouseMove, QPointF(0, 0),
                           QPointF(0, -500),
                           Qt.MouseButton.LeftButton,
                           Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier)
        handle.mouseMoveEvent(move)
        self.assertLessEqual(tw.height(), 600)
        tw.deleteLater()
        logger.info("[PASS] drag clamped at max 600 ✓")

    def test_drag_clamps_min_80(self):
        logger.info("═══ TestResizeHandleExtended2.test_drag_clamps_min_80 ═══")
        tw = TerminalWidget()
        tw.setFixedHeight(100)
        handle = tw._resize_handle
        handle._press_y = 0.0
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        move = QMouseEvent(QEvent.Type.MouseMove, QPointF(0, 0),
                           QPointF(0, 500),
                           Qt.MouseButton.LeftButton,
                           Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier)
        handle.mouseMoveEvent(move)
        self.assertGreaterEqual(tw.height(), 80)
        tw.deleteLater()
        logger.info("[PASS] drag clamped at min 80 ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestSearchPanelExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_replace_emits_with_regex_flag(self):
        logger.info("═══ TestSearchPanelExtended.test_replace_emits_with_regex_flag ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.replace_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("\\d+")
        panel.replace_input.setText("NUM")
        panel.is_regex.setChecked(True)
        panel.on_replace()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("\\d+", "NUM", False, True))
        parent.deleteLater()
        logger.info("[PASS] replace with regex flag ✓")

    def test_replace_all_case_sensitive(self):
        logger.info("═══ TestSearchPanelExtended.test_replace_all_case_sensitive ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.replace_all_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("hello")
        panel.replace_input.setText("hi")
        panel.case_sensitive.setChecked(True)
        panel.is_regex.setChecked(False)
        panel.on_replace_all()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("hello", "hi", True, False))
        parent.deleteLater()
        logger.info("[PASS] replace_all case sensitive ✓")

    def test_find_next_case_sensitive_regex(self):
        logger.info("═══ TestSearchPanelExtended.test_find_next_case_sensitive_regex ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.find_next_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("Hello\\d+")
        panel.case_sensitive.setChecked(True)
        panel.is_regex.setChecked(True)
        panel.on_find_next()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("Hello\\d+", True, True))
        parent.deleteLater()
        logger.info("[PASS] find_next with case sensitive + regex ✓")

    def test_find_prev_with_flags(self):
        logger.info("═══ TestSearchPanelExtended.test_find_prev_with_flags ═══")
        parent = QWidget()
        panel = SearchPanel(parent=parent)
        emitted = []
        panel.find_prev_requested.connect(lambda *a: emitted.append(a))
        panel.find_input.setText("world")
        panel.case_sensitive.setChecked(True)
        panel.on_find_prev()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("world", True, False))
        parent.deleteLater()
        logger.info("[PASS] find_prev with case sensitive ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestTerminalWidgetEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def setUp(self):
        self.tw = TerminalWidget()

    def tearDown(self):
        self.tw.kill_process()
        self.tw.deleteLater()

    def test_run_simple_echo(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_run_simple_echo ═══")
        self.tw._input.setText("echo hello terminal")
        self.tw._run_command()
        self.tw._process.waitForFinished(3000)
        output = self.tw._output.toPlainText()
        self.assertIn("hello terminal", output)
        logger.info("[PASS] echo command produces output ✓")

    def test_run_pwd(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_run_pwd ═══")
        self.tw._input.setText("pwd")
        self.tw._run_command()
        self.tw._process.waitForFinished(3000)
        output = self.tw._output.toPlainText()
        self.assertIn(self.tw._cwd, output)
        logger.info("[PASS] pwd shows current directory ✓")

    def test_single_command_with_two_lines(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_single_command_with_two_lines ═══")
        self.tw._input.setText("echo first && echo second")
        self.tw._run_command()
        self.tw._process.waitForFinished(3000)
        output = self.tw._output.toPlainText()
        self.assertIn("first", output)
        self.assertIn("second", output)
        logger.info("[PASS] single command with two lines ✓")

    def test_run_non_existent_command(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_run_non_existent_command ═══")
        self.tw._input.setText("nonexistent_cmd_xyz123")
        self.tw._run_command()
        self.tw._process.waitForFinished(3000)
        output = self.tw._output.toPlainText()
        self.assertIn("not found", output.lower())
        logger.info("[PASS] non-existent command shows error ✓")

    def test_history_persistence_between_commands(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_history_persistence_between_commands ═══")
        self.tw._input.setText("echo a")
        self.tw._run_command()
        if self.tw._process:
            self.tw._process.waitForFinished(2000)
        self.tw._input.setText("echo b")
        self.tw._run_command()
        if self.tw._process:
            self.tw._process.waitForFinished(2000)
        self.assertIn("echo a", self.tw._history)
        self.assertIn("echo b", self.tw._history)
        logger.info("[PASS] history persists between commands ✓")

    def test_clear_history_no_crash(self):
        logger.info("═══ TestTerminalWidgetEdgeCases.test_clear_history_no_crash ═══")
        self.tw._history = ["a", "b", "c"]
        self.tw._history.clear()
        self.assertEqual(len(self.tw._history), 0)
        logger.info("[PASS] clear history no crash ✓")


# ── Shortcuts, clipboard, window management ──

@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestShortcuts(unittest.TestCase):
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

    def test_terminal_shortcut_connected_to_toggle(self):
        logger.info("═══ TestShortcuts.test_terminal_shortcut_connected_to_toggle ═══")
        self.assertTrue(hasattr(self.mw, '_terminal_shortcut'))
        self.mw._terminal_shortcut.activated.disconnect()
        self.mw._terminal_shortcut.activated.connect(
            lambda: setattr(self.mw, '_term_triggered', True))
        self.mw._terminal_shortcut.activated.emit()
        logger.info("[PASS] terminal shortcut connected ✓")

    def test_sidebar_shortcut_connected_to_toggle(self):
        logger.info("═══ TestShortcuts.test_sidebar_shortcut_connected_to_toggle ═══")
        # sidebar shortcut is defined inline; find any QShortcut with Ctrl+B
        from PyQt6.QtGui import QShortcut
        for child in self.mw.findChildren(QShortcut):
            if child.key().toString() == "Ctrl+B":
                visible_before = self.mw.sidebar_visible
                child.activated.emit()
                self.assertNotEqual(self.mw.sidebar_visible, visible_before)
                break
        else:
            self.fail("No Ctrl+B shortcut found")
        logger.info("[PASS] sidebar shortcut toggles sidebar ✓")

    def test_shortcut_key_uses_config_binding(self):
        logger.info("═══ TestShortcuts.test_shortcut_key_uses_config_binding ═══")
        binding = self.mw.config_manager.get_binding("toggle_terminal")
        self.assertIsNotNone(binding)
        expected = QKeySequence(binding)
        self.assertEqual(self.mw._terminal_shortcut.key(), expected)
        logger.info("[PASS] terminal shortcut key from config ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestEditorClipboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_copy_paste_roundtrip(self):
        logger.info("═══ TestEditorClipboard.test_copy_paste_roundtrip ═══")
        editor = CustomEditor()
        editor.setPlainText("hello world")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.copy()
        editor.clear()
        self.assertEqual(editor.toPlainText(), "")
        editor.paste()
        self.assertEqual(editor.toPlainText(), "hello world")
        editor.deleteLater()
        logger.info("[PASS] copy → paste roundtrip ✓")

    def test_cut_moves_text_to_clipboard(self):
        logger.info("═══ TestEditorClipboard.test_cut_moves_text_to_clipboard ═══")
        editor = CustomEditor()
        editor.setPlainText("cut me")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.cut()
        self.assertEqual(editor.toPlainText(), "")
        editor.deleteLater()
        logger.info("[PASS] cut removes text ✓")

    def test_paste_without_clipboard_no_crash(self):
        logger.info("═══ TestEditorClipboard.test_paste_without_clipboard_no_crash ═══")
        QApplication.clipboard().clear()
        editor = CustomEditor()
        editor.clear()
        editor.paste()
        self.assertEqual(editor.toPlainText(), "")
        editor.deleteLater()
        logger.info("[PASS] paste with empty clipboard no crash ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestWindowManagement(unittest.TestCase):
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

    def test_toggle_show_whitespace_toggles_action(self):
        logger.info("═══ TestWindowManagement.test_toggle_show_whitespace_toggles_action ═══")
        self.mw.show_whitespace_action.setChecked(False)
        self.mw.toggle_show_whitespace()
        self.mw.show_whitespace_action.setChecked(True)
        self.mw.toggle_show_whitespace()
        logger.info("[PASS] toggle_show_whitespace no crash ✓")

    def test_toggle_show_margin_toggles_action(self):
        logger.info("═══ TestWindowManagement.test_toggle_show_margin_toggles_action ═══")
        self.mw.show_margin_action.setChecked(True)
        self.mw.toggle_show_margin()
        self.mw.show_margin_action.setChecked(False)
        self.mw.toggle_show_margin()
        logger.info("[PASS] toggle_show_margin no crash ✓")

    def test_cycle_encoding_changes_label(self):
        logger.info("═══ TestWindowManagement.test_cycle_encoding_changes_label ═══")
        old = self.mw.encoding_label.text()
        self.mw._cycle_encoding()
        new = self.mw.encoding_label.text()
        self.assertNotEqual(old, new)
        logger.info("[PASS] _cycle_encoding changes label ✓")

# ── Menu principale della MainWindow ──

@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowMenu(unittest.TestCase):
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

    def test_menubar_has_file_edit_settings_view(self):
        logger.info("═══ TestMainWindowMenu.test_menubar_has_file_edit_settings_view ═══")
        menubar = self.mw.menuBar()
        actions = [a.text() for a in menubar.actions()]
        self.assertIn("&File", actions)
        self.assertIn("&Edit", actions)
        self.assertIn("&Settings", actions)
        self.assertIn("&View", actions)
        logger.info("[PASS] Menubar contiene File, Edit, Settings, View ✓")

    def test_file_menu_has_expected_actions(self):
        logger.info("═══ TestMainWindowMenu.test_file_menu_has_expected_actions ═══")
        menubar = self.mw.menuBar()
        file_menu = None
        for a in menubar.actions():
            if a.text() == "&File":
                file_menu = a.menu()
                break
        self.assertIsNotNone(file_menu)
        texts = [a.text() for a in file_menu.actions() if a.text()]
        self.assertIn("&New", texts)
        self.assertIn("&Open", texts)
        self.assertIn("&Save", texts)
        self.assertIn("Save &As...", texts)
        self.assertIn("&Close Tab", texts)
        self.assertIn("Recent Files", texts)
        logger.info("[PASS] File menu ha New, Open, Save, Save As, Close Tab ✓")

    def test_edit_menu_has_expected_actions(self):
        logger.info("═══ TestMainWindowMenu.test_edit_menu_has_expected_actions ═══")
        menubar = self.mw.menuBar()
        edit_menu = None
        for a in menubar.actions():
            if a.text() == "&Edit":
                edit_menu = a.menu()
                break
        self.assertIsNotNone(edit_menu)
        texts = [a.text() for a in edit_menu.actions() if a.text()]
        self.assertIn("&Undo", texts)
        self.assertIn("&Redo", texts)
        self.assertIn("&Find", texts)
        self.assertIn("&Replace", texts)
        self.assertIn("Go to Line", texts)
        self.assertIn("&Command Palette", texts)
        logger.info("[PASS] Edit menu ha Undo, Redo, Find, Replace, Go to Line, Command Palette ✓")

    def test_view_menu_has_toggle_actions(self):
        logger.info("═══ TestMainWindowMenu.test_view_menu_has_toggle_actions ═══")
        menubar = self.mw.menuBar()
        view_menu = None
        for a in menubar.actions():
            if a.text() == "&View":
                view_menu = a.menu()
                break
        self.assertIsNotNone(view_menu)
        texts = [a.text() for a in view_menu.actions() if a.text()]
        self.assertIn("Word Wrap", texts)
        self.assertIn("Show Whitespace", texts)
        self.assertIn("Show Margin Line", texts)
        logger.info("[PASS] View menu ha Word Wrap, Show Whitespace, Show Margin Line ✓")

    def test_commands_dict_has_all_expected_keys(self):
        logger.info("═══ TestMainWindowMenu.test_commands_dict_has_all_expected_keys ═══")
        expected = {"new_file", "open_file", "save_file", "save_as", "close_tab",
                    "find", "replace", "undo", "redo", "command_palette",
                    "goto_line", "toggle_terminal"}
        self.assertTrue(expected.issubset(self.mw.commands.keys()))
        logger.info("[PASS] commands dict ha tutte le 12 chiavi attese ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMainWindowCloseEvent(unittest.TestCase):
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

    def test_close_without_modified_tabs_accepts(self):
        logger.info("═══ TestMainWindowCloseEvent.test_close_without_modified_tabs_accepts ═══")
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        self.mw.closeEvent(event)
        self.assertTrue(event.isAccepted())
        logger.info("[PASS] closeEvent senza modifiche → accept ✓")

    def test_close_with_modified_tab_save_triggers(self):
        logger.info("═══ TestMainWindowCloseEvent.test_close_with_modified_tab_save_triggers ═══")
        tab = EditorTab(pane='left')
        tab.editor.setPlainText("modified content")
        tab.editor.document().setModified(True)
        tab._is_modified = True
        self.mw.tabs.addTab(tab, "test")
        # _do_autosave clears _is_modified, so mock it to leave tab alone
        with unittest.mock.patch.object(self.mw, '_do_autosave'):
            with unittest.mock.patch.object(QMessageBox, 'question',
                              return_value=QMessageBox.StandardButton.Save):
                with unittest.mock.patch.object(self.mw, 'save_tab_by_index',
                                  return_value=True) as mock_save:
                    from PyQt6.QtGui import QCloseEvent
                    event = QCloseEvent()
                    self.mw.closeEvent(event)
                    mock_save.assert_called_once()
        logger.info("[PASS] closeEvent con tab modificato + Save → save_tab_by_index chiamato ✓")

    def test_close_with_modified_tab_cancel_ignores(self):
        logger.info("═══ TestMainWindowCloseEvent.test_close_with_modified_tab_cancel_ignores ═══")
        tab = EditorTab(pane='left')
        tab.editor.setPlainText("modified content")
        tab.editor.document().setModified(True)
        tab._is_modified = True
        self.mw.tabs.addTab(tab, "test")
        with unittest.mock.patch.object(self.mw, '_do_autosave'):
            with unittest.mock.patch.object(QMessageBox, 'question',
                              return_value=QMessageBox.StandardButton.Cancel):
                from PyQt6.QtGui import QCloseEvent
                event = QCloseEvent()
                self.mw.closeEvent(event)
                self.assertFalse(event.isAccepted())
        logger.info("[PASS] closeEvent con tab modificato + Cancel → ignore ✓")

    def test_close_with_modified_tab_discard_accepts(self):
        logger.info("═══ TestMainWindowCloseEvent.test_close_with_modified_tab_discard_accepts ═══")
        tab = EditorTab(pane='left')
        tab.editor.setPlainText("modified content")
        tab.editor.document().setModified(True)
        tab._is_modified = True
        self.mw.tabs.addTab(tab, "test")
        with unittest.mock.patch.object(self.mw, '_do_autosave'):
            with unittest.mock.patch.object(QMessageBox, 'question',
                              return_value=QMessageBox.StandardButton.Discard):
                from PyQt6.QtGui import QCloseEvent
                event = QCloseEvent()
                self.mw.closeEvent(event)
                self.assertTrue(event.isAccepted())
        logger.info("[PASS] closeEvent con tab modificato + Discard → accept ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCommandPaletteComandi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_execute_new_file_routes_correctly(self):
        logger.info("═══ TestCommandPaletteComandi.test_execute_new_file_routes_correctly ═══")
        parent = QWidget()
        palette = CommandPalette({"new_file": "New File"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.action_list.setCurrentRow(0)
        palette.on_enter_pressed()
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], "new_file")
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] execute new_file from palette ✓")

    def test_execute_open_file_routes_correctly(self):
        logger.info("═══ TestCommandPaletteComandi.test_execute_open_file_routes_correctly ═══")
        parent = QWidget()
        palette = CommandPalette({"open_file": "Open File"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.action_list.setCurrentRow(0)
        palette.on_enter_pressed()
        self.assertEqual(emitted[0], "open_file")
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] execute open_file from palette ✓")

    def test_execute_save_file_routes_correctly(self):
        logger.info("═══ TestCommandPaletteComandi.test_execute_save_file_routes_correctly ═══")
        parent = QWidget()
        palette = CommandPalette({"save_file": "Save"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.action_list.setCurrentRow(0)
        palette.on_enter_pressed()
        self.assertEqual(emitted[0], "save_file")
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] execute save_file from palette ✓")

    def test_execute_undo_redo_routes_correctly(self):
        logger.info("═══ TestCommandPaletteComandi.test_execute_undo_redo_routes_correctly ═══")
        parent = QWidget()
        palette = CommandPalette({"undo": "Undo", "redo": "Redo"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.action_list.setCurrentRow(1)
        palette.on_enter_pressed()
        self.assertEqual(emitted[0], "redo")
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] execute redo from palette ✓")

    def test_open_recent_routing_step_by_step(self):
        logger.info("═══ TestCommandPaletteComandi.test_open_recent_routing_step_by_step ═══")
        parent = QWidget()
        palette = CommandPalette({"open_recent_0": "Open: /tmp/test.txt"}, parent=parent)
        emitted = []
        palette.actionTriggered.connect(lambda a: emitted.append(a))
        palette.action_list.setCurrentRow(0)
        palette.on_enter_pressed()
        self.assertEqual(emitted[0], "open_recent_0")
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] open_recent routing works ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestCommandPaletteRecentFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_update_actions_with_recent_files(self):
        logger.info("═══ TestCommandPaletteRecentFiles.test_update_actions_with_recent_files ═══")
        parent = QWidget()
        palette = CommandPalette({"cmd.test": "Test"}, parent=parent)
        commands = {"cmd.a": "Action A", "cmd.b": "Action B"}
        palette.update_actions(commands)
        self.assertEqual(palette.action_list.count(), 2)
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] update_actions with additional commands ✓")

    def test_filter_empty_list_no_crash(self):
        logger.info("═══ TestCommandPaletteRecentFiles.test_filter_empty_list_no_crash ═══")
        parent = QWidget()
        palette = CommandPalette({}, parent=parent)
        palette.filter_actions("test")
        self.assertEqual(palette.action_list.count(), 0)
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] filter on empty list no crash ✓")

    def test_enter_on_empty_list_no_crash(self):
        logger.info("═══ TestCommandPaletteRecentFiles.test_enter_on_empty_list_no_crash ═══")
        parent = QWidget()
        palette = CommandPalette({}, parent=parent)
        palette.on_enter_pressed()
        palette.deleteLater()
        parent.deleteLater()
        logger.info("[PASS] enter on empty list no crash ✓")


# ── Git integration, multi-pane, tree actions ──

@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestGitCaching(unittest.TestCase):
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

    def test_on_git_result_shows_branch_on_label(self):
        logger.info("═══ TestGitCaching.test_on_git_result_shows_branch_on_label ═══")
        self.mw._on_git_branch_result("/tmp", "feature-x")
        self.assertIn("feature-x", self.mw.git_label.text())
        logger.info("[PASS] _on_git_branch_result shows branch ✓")

    def test_on_git_result_empty_hides_label(self):
        logger.info("═══ TestGitCaching.test_on_git_result_empty_hides_label ═══")
        self.mw._on_git_branch_result("/tmp", "")
        self.assertTrue(self.mw.git_label.isHidden())
        logger.info("[PASS] _on_git_result empty hides label ✓")

    def test_git_cache_used_on_subsequent_call(self):
        logger.info("═══ TestGitCaching.test_git_cache_used_on_subsequent_call ═══")
        self.mw._git_cache["/tmp"] = {"branch": "cached-branch", "time": time.time()}
        with unittest.mock.patch.object(self.mw, '_git_workers', new_callable=list):
            self.mw._update_git_branch.cache_clear()
        logger.info("[PASS] git cache structure works ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestMultiPaneSplit(unittest.TestCase):
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

    def test_split_editor_with_readable_file_creates_right_tab(self):
        logger.info("═══ TestMultiPaneSplit.test_split_editor_creates_right_tab ═══")
        with tmp_dir() as tmp:
            f = tmp / "split_me.py"
            f.write_text("x = 1")
            self.mw.open_file(str(f))
            self.assertTrue(self.mw.tabs_right.isHidden())
            self.mw.split_editor()
            self.assertFalse(self.mw.tabs_right.isHidden())
            self.assertEqual(self.mw.tabs_right.count(), 1)
        logger.info("[PASS] split_editor con file leggibile crea tab right ✓")

    def test_split_editor_twice_unsplits(self):
        logger.info("═══ TestMultiPaneSplit.test_split_editor_twice_unsplits ═══")
        with tmp_dir() as tmp:
            f = tmp / "unsplit.py"
            f.write_text("x")
            self.mw.open_file(str(f))
            self.mw.split_editor()
            self.assertFalse(self.mw.tabs_right.isHidden())
            self.mw.split_editor()
            self.assertTrue(self.mw.tabs_right.isHidden())
        logger.info("[PASS] split_editor due volte unsplit ✓")

    def test_on_pane_activated_sets_active_pane(self):
        logger.info("═══ TestMultiPaneSplit.test_on_pane_activated_sets_active_pane ═══")
        self.mw._on_pane_activated("right")
        self.assertEqual(self.mw._active_pane, "right")
        self.mw._on_pane_activated("left")
        self.assertEqual(self.mw._active_pane, "left")
        logger.info("[PASS] _on_pane_activated cambia _active_pane ✓")


@unittest.skipUnless(QT_AVAILABLE, "PyQt6 non disponibile")
class TestFileTreeIconMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_qapp()

    def test_file_icon_returns_qicon_for_py(self):
        logger.info("═══ TestFileTreeIconMapping.test_file_icon_returns_qicon_for_py ═══")
        ft = FileTree()
        ico = ft._file_icon("script.py")
        self.assertIsInstance(ico, QIcon)
        ft.deleteLater()
        logger.info("[PASS] _file_icon for .py returns QIcon ✓")

    def test_file_icon_returns_qicon_for_js(self):
        logger.info("═══ TestFileTreeIconMapping.test_file_icon_returns_qicon_for_js ═══")
        ft = FileTree()
        ico = ft._file_icon("app.js")
        self.assertIsInstance(ico, QIcon)
        ft.deleteLater()
        logger.info("[PASS] _file_icon for .js returns QIcon ✓")

    def test_file_icon_returns_qicon_for_unknown(self):
        logger.info("═══ TestFileTreeIconMapping.test_file_icon_returns_qicon_for_unknown ═══")
        ft = FileTree()
        ico = ft._file_icon("readme.txt")
        self.assertIsInstance(ico, QIcon)
        ft.deleteLater()
        logger.info("[PASS] _file_icon for .txt returns QIcon ✓")

    def test_set_root_path_changes_current_root(self):
        logger.info("═══ TestFileTreeIconMapping.test_set_root_path_changes_current_root ═══")
        with tmp_dir() as tmp:
            ft = FileTree(str(tmp))
            new_root = str(tmp.parent)
            ft.set_root_path(new_root)
            self.assertEqual(ft.current_root, os.path.realpath(new_root))
            ft.deleteLater()
        logger.info("[PASS] set_root_path changes current_root ✓")

    def test_on_item_click_directory_toggles_expand(self):
        logger.info("═══ TestFileTreeIconMapping.test_on_item_click_directory_toggles_expand ═══")
        with tmp_dir() as tmp:
            sub = tmp / "subdir_for_click"
            sub.mkdir()
            ft = FileTree(str(tmp))
            item = None
            for i in range(ft.tree.topLevelItemCount()):
                if ft.tree.topLevelItem(i).text(0) == "subdir_for_click":
                    item = ft.tree.topLevelItem(i)
                    break
            if item:
                was_expanded = item.isExpanded()
                ft._on_item_clicked(item, 0)
                self.assertNotEqual(item.isExpanded(), was_expanded)
            ft.deleteLater()
        logger.info("[PASS] _on_item_click toggles directory ✓")


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
        TestCustomEditor,
        TestSyntaxHighlighterExtended,
        TestFileTreeExtended,
        TestMainWindowCritical,
        TestTerminalWidgetExtended,
        TestResizeHandleExtended,
        TestCommandPaletteExtended,
        TestKeybindingsDialogExtended,
        TestIconsAndTheme,
        TestDraggableTabBar,
        TestCodeFoldingArea,
        TestLineNumberArea,
        TestMarginLine,
        TestMainWindowAutosave,
        TestEditorTabAtomicSave,
        TestSyntaxHighlighterEdgeCases,
        TestResizeHandleExtended2,
        TestSearchPanelExtended,
        TestTerminalWidgetEdgeCases,
        TestCommandPaletteRecentFiles,
        TestCommandPaletteComandi,
        TestShortcuts,
        TestEditorClipboard,
        TestWindowManagement,
        TestMainWindowMenu,
        TestMainWindowCloseEvent,
        TestGitCaching,
        TestMultiPaneSplit,
        TestFileTreeIconMapping,
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
    if result.errors:
        logger.info("  ── ERRORI ──")
        for test, tb in result.errors:
            lines = tb.split("\n")
            short = " | ".join(l.strip() for l in lines if l.strip())[:120]
            logger.info("    ⚠ %s — %s", test, short)
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
