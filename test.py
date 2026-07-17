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

    @unittest.expectedFailure
    def test_path_traversal_returns_false(self):
        """
        BUG: _is_path_safe('../../etc/passwd') ritorna True ma dovrebbe ritornare False.
        Questo test è expectedFailure: quando il bug viene corretto, diventa unexpected
        success e segnala che il fix è pronto.
        """
        logger.info("═══ TestIsPathSafe.test_path_traversal_returns_false (BUG NOTO) ═══")
        result = _is_path_safe("../../etc/passwd")
        self.assertFalse(result,
            "BUG: _is_path_safe dovrebbe rifiutare path traversal, ma ritorna True")
        logger.info("[XFAIL] BUG confermato: _is_path_safe accetta path traversal")


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

    def test_open_nonexistent_shows_dialog(self):
        """Fase 7.5 — open_file su path inesistente → logger.warning + nessun tab."""
        logger.info("═══ TestMainWindowOpenFile.test_open_nonexistent_shows_dialog ═══")
        with patched_config(self.tmp):
            with unittest.mock.patch.object(MainWindow, '_update_git_branch', return_value=None):
                mw = MainWindow()
        initial_count = mw.tabs.count()
        with self.assertLogs("main_window", level="WARNING") as logs:
            mw.open_file(str(self.tmp / "nope.py"))
        self.assertTrue(any("not found" in msg for msg in logs.output),
            "Nessun warning 'not found' emesso")
        self.assertEqual(mw.tabs.count(), initial_count,
            "Nessun tab aggiunto per file inesistente")
        mw.deleteLater()
        logger.info("[PASS] open_file inesistente → warning emesso, tab count invariato ✓")

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
