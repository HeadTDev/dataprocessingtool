import sys
import threading
from importlib import import_module
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt

from common import Config

logger = logging.getLogger("main_menu")


def resource_path(*parts: str) -> str:
    """
    Resource path resolution for development and PyInstaller bundled execution.
    
    Args:
        *parts: Path components
        
    Returns:
        Absolute path to resource
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        import os
        return os.path.join(base, *parts)
    import os
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, *parts)


class UpdateUIBridge(QObject):
    """Bridge between auto-updater thread and UI thread for safe updates."""
    
    requestPrompt = Signal(str)
    requestInfo = Signal(str)
    requestError = Signal(str)
    requestSetVersion = Signal(str)

    def __init__(self, version_label: QLabel):
        super().__init__()
        self._prompt_event = None
        self._prompt_answer = False
        self.version_label = version_label

        self.requestPrompt.connect(self._onPrompt, Qt.QueuedConnection)
        self.requestInfo.connect(self._onInfo, Qt.QueuedConnection)
        self.requestError.connect(self._onError, Qt.QueuedConnection)
        self.requestSetVersion.connect(self._onSetVersion, Qt.QueuedConnection)

    @Slot(str)
    def _onPrompt(self, question: str):
        res = QMessageBox.question(
            None,
            "Frissítés elérhető",
            question,
            QMessageBox.Yes | QMessageBox.No
        )
        self._prompt_answer = (res == QMessageBox.Yes)
        if self._prompt_event:
            self._prompt_event.set()

    @Slot(str)
    def _onInfo(self, msg: str):
        QMessageBox.information(None, "Frissítés", msg)

    @Slot(str)
    def _onError(self, msg: str):
        QMessageBox.critical(None, "Frissítés hiba", msg)

    @Slot(str)
    def _onSetVersion(self, ver: str):
        self.version_label.setText(f"Verzió: {ver}")

    def ui_prompt(self, question: str) -> bool:
        self._prompt_event = threading.Event()
        self.requestPrompt.emit(question)
        self._prompt_event.wait()
        return self._prompt_answer

    def ui_info(self, msg: str):
        self.requestInfo.emit(msg)

    def ui_error(self, msg: str):
        self.requestError.emit(msg)

    def ui_set_version(self, version_tag: str):
        self.requestSetVersion.emit(version_tag or "ismeretlen")


def start_auto_update(version_label: QLabel) -> Optional[UpdateUIBridge]:
    """
    Start auto-update process.
    
    Args:
        version_label: Label to update with version info
        
    Returns:
        UpdateUIBridge instance or None if auto_updater unavailable
    """
    try:
        from auto_updater import perform_update_flow, read_local_version_info
    except ImportError:
        logger.warning("Auto-updater not available")
        return None

    info = read_local_version_info()
    version_label.setText(f"Verzió: {info.get('version') or 'ismeretlen'}")

    update_bridge = UpdateUIBridge(version_label)
    perform_update_flow(
        incremental_preferred=True,
        ui_prompt=update_bridge.ui_prompt,
        ui_info=update_bridge.ui_info,
        ui_error=update_bridge.ui_error,
        ui_set_version=update_bridge.ui_set_version,
        run_in_thread=True,
        delay_seconds=1.0
    )
    
    return update_bridge

class MainMenu(QWidget):
    """Main menu window for the application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon(resource_path("synthwave_icon.png")))
        self.setMinimumSize(320, 220)
        
        self.version_label = QLabel("Verzió: betöltés...")
        f = self.version_label.font()
        f.setPointSize(f.pointSize() - 1)
        self.version_label.setFont(f)

        # Keep reference to opened module windows
        self._open_windows = {}
        
        # Store update bridge reference as instance variable
        self.update_bridge = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))

        buttons = [
            ("💸 Merkantil PDF Feldolgozó", "merkantil_pdf_feldolgozo"),
            ("📂 Vonalkód PDF Másolás", "barcode_pdf_masolas"),
            ("📚 Cofanet Help", "cofanet_help"),
            ("🔧 KSH Iparági Értékesítés", "ksh_iparagi_ertekesites"),
        ]

        for text, pkg in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(Config.BUTTON_WIDTH, Config.BUTTON_HEIGHT)
            btn.clicked.connect(lambda _, p=pkg: self.open_module(p, "run", "main"))
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def open_module(self, pkg_name: str, entry_module: str = "run", entry_func: str = "main"):
        """
        Launch a module by importing and calling its entry function.
        
        Args:
            pkg_name: Package name to import
            entry_module: Module name within package
            entry_func: Function name to call
        """
        # If window already exists, bring it to front
        w = self._open_windows.get(pkg_name)
        if w is not None:
            try:
                w.show()
                w.raise_()
                w.activateWindow()
                return
            except RuntimeError:
                # Window was closed, remove reference
                self._open_windows.pop(pkg_name, None)

        try:
            mod = import_module(f"{pkg_name}.{entry_module}")
        except Exception as e:
            logger.exception(f"Failed to import module {pkg_name}")
            QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni a modult: {pkg_name}\n{e}")
            return

        entry = getattr(mod, entry_func, None)
        if not callable(entry):
            logger.error(f"Module {pkg_name} has no callable {entry_func}")
            QMessageBox.critical(self, "Hiba", f"A modul bejárata hiányzik: {pkg_name}.{entry_module}:{entry_func}")
            return

        # Call module main() which returns the window
        try:
            w = entry()
        except Exception as e:
            logger.exception(f"Error launching module {pkg_name}")
            QMessageBox.critical(self, "Hiba", f"Hiba a modul indításakor: {pkg_name}\n{e}")
            return

        if w is None:
            return

        # Keep reference and clean up when destroyed
        self._open_windows[pkg_name] = w
        try:
            w.destroyed.connect(lambda: self._open_windows.pop(pkg_name, None))
            w.show()
            w.raise_()
            w.activateWindow()
        except Exception as e:
            logger.warning(f"Failed to setup window signals: {e}")


# PyInstaller static import hints (kept for PyInstaller detection)
if False:
    import barcode_pdf_masolas.run  # noqa: F401
    import cofanet_help.run         # noqa: F401
    import ksh_iparagi_ertekesites.run  # noqa: F401
    import merkantil_pdf_feldolgozo.run # noqa: F401


if __name__ == "__main__":
    from common import setup_logging
    
    # Setup logging
    setup_logging(module_name="main_menu")
    
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    
    # Start auto-update after a short delay
    QTimer.singleShot(500, lambda: setattr(window, 'update_bridge', start_auto_update(window.version_label)))
    
    sys.exit(app.exec())