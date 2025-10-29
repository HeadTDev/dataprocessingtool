import sys
import threading
from importlib import import_module

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt

BUTTON_SIZE = (300, 40)

def resource_path(*parts: str) -> str:
    """
    Erőforrás elérés fejlesztői és becsomagolt (PyInstaller) futásnál is.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        import os
        return os.path.join(base, *parts)
    import os
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, *parts)


class UpdateUIBridge(QObject):
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


_update_bridge = None

def start_auto_update(version_label: QLabel):
    global _update_bridge
    try:
        from auto_updater import perform_update_flow, read_local_version_info
    except ImportError:
        return

    info = read_local_version_info()
    version_label.setText(f"Verzió: {info.get('version') or 'ismeretlen'}")

    _update_bridge = UpdateUIBridge(version_label)
    perform_update_flow(
        incremental_preferred=True,
        ui_prompt=_update_bridge.ui_prompt,
        ui_info=_update_bridge.ui_info,
        ui_error=_update_bridge.ui_error,
        ui_set_version=_update_bridge.ui_set_version,
        run_in_thread=True,
        delay_seconds=1.0
    )


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon(resource_path("synthwave_icon.png")))
        self.setMinimumSize(320, 220)
        self.version_label = QLabel("Verzió: betöltés...")
        f = self.version_label.font()
        f.setPointSize(f.pointSize() - 1)
        self.version_label.setFont(f)

        # Megnyitott modulablakok referenciái (hogy ne gyűjtse be a GC)
        # kulcs: pkg név, érték: QWidget példány
        self._open_windows = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))

        buttons = [
            ("💸 Merkantil PDF Feldolgozó", "merkantil_pdf_feldolgozo"),
            ("📂 Vonalkód PDF Másolás", "barcode_pdf_masolas"),
            ("📚 Cofanet Help", "cofanet_help"),
            ("🔧 KSH Iparági Értékesítés", "ksh_iparagi_ertekesites"),
            ("🖱️ Automatikus Egér Mozgató", "mouse_mover"),
        ]

        for text, pkg in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.clicked.connect(lambda _, p=pkg: self.open_module(p, "run", "main"))
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def open_module(self, pkg_name: str, entry_module: str = "run", entry_func: str = "main"):
        """
        Modul indítása importtal és a visszaadott ablak referencia eltárolása.
        Ha már megnyitottuk, hozza előre.
        """
        # Ha már van példány, csak előtérbe hozzuk
        w = self._open_windows.get(pkg_name)
        if w is not None:
            try:
                w.show()
                w.raise_()
                w.activateWindow()
                return
            except RuntimeError:
                # lehet, hogy már bezárták → töröljük a referenciát és újranyitjuk
                self._open_windows.pop(pkg_name, None)

        try:
            mod = import_module(f"{pkg_name}.{entry_module}")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni a modult: {pkg_name}\n{e}")
            return

        entry = getattr(mod, entry_func, None)
        if not callable(entry):
            QMessageBox.critical(self, "Hiba", f"A modul bejárata hiányzik: {pkg_name}.{entry_module}:{entry_func}")
            return

        # A modul main() visszaadja az ablakot
        try:
            w = entry()
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba a modul indításakor: {pkg_name}\n{e}")
            return

        # Ha a modul nem adott vissza ablakot, nem tudjuk tartani a referenciát,
        # de megpróbáljuk előtérbe hozni, hátha mégis létezik
        if w is None:
            return

        # Referencia megtartása, és ha bezárják, töröljük a referenciát
        self._open_windows[pkg_name] = w
        try:
            w.destroyed.connect(lambda: self._open_windows.pop(pkg_name, None))
            w.show()
            w.raise_()
            w.activateWindow()
        except Exception:
            pass


# Statikus import hint PyInstallerhez
if False:
    import barcode_pdf_masolas.run  # noqa: F401
    import cofanet_help.run         # noqa: F401
    import ksh_iparagi_ertekesites.run  # noqa: F401
    import merkantil_pdf_feldolgozo.run # noqa: F401
    import mouse_mover.run          # noqa: F401


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    QTimer.singleShot(500, lambda: start_auto_update(window.version_label))
    sys.exit(app.exec())