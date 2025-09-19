import sys
import subprocess
import threading

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt

BUTTON_SIZE = (300, 40)

# --- AUTO-UPDATE INTEGRÁCIÓ (Thread-safe Qt bridge) ---

class UpdateUIBridge(QObject):
    requestPrompt = Signal(str)
    requestInfo = Signal(str)
    requestError = Signal(str)

    def __init__(self):
        super().__init__()
        self._prompt_event = None
        self._prompt_answer = False

        self.requestPrompt.connect(self._onPrompt, Qt.QueuedConnection)
        self.requestInfo.connect(self._onInfo, Qt.QueuedConnection)
        self.requestError.connect(self._onError, Qt.QueuedConnection)

    @Slot(str)
    def _onPrompt(self, question: str):
        # Ez a főszálban fut
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

    # --- Ezeket a függvényeket adjuk át callbackként a háttérszálnak ---

    def ui_prompt(self, question: str) -> bool:
        # A háttérszálból hívódik: szignál a főszálnak + várakozás
        self._prompt_event = threading.Event()
        self.requestPrompt.emit(question)
        self._prompt_event.wait()
        return self._prompt_answer

    def ui_info(self, msg: str):
        self.requestInfo.emit(msg)

    def ui_error(self, msg: str):
        self.requestError.emit(msg)


_update_bridge = None  # hogy ne gyűjtse be a GC

def start_auto_update():
    global _update_bridge
    try:
        from auto_updater import perform_update_flow
    except ImportError:
        return

    _update_bridge = UpdateUIBridge()

    # Háttérszálban fut; a UI interakciók a bridge-en keresztül a főszálra kerülnek
    perform_update_flow(
        incremental_preferred=True,
        ui_prompt=_update_bridge.ui_prompt,
        ui_info=_update_bridge.ui_info,
        ui_error=_update_bridge.ui_error,
        run_in_thread=True,
        delay_seconds=1.0
    )

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon("synthwave_icon.png"))
        self.setMinimumSize(320, 160)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))

        buttons = [
            ("💸 Merkantil PDF Feldolgozó", "merkantil_pdf_feldolgozo/run.py"),
            ("📂 Vonalkód PDF Másolás", "barcode_pdf_masolas/run.py"),
            ("📚 Cofanet Help", "cofanet_help/run.py"),
            ("🔧 KSH Iparági Értékesítés", "ksh_iparagi_ertekesites/run.py"),
        ]

        for text, path in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.clicked.connect(lambda _, p=path: subprocess.Popen([sys.executable, p]))
            layout.addWidget(btn)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainMenu()
    window.show()

    # Indítás után kis késleltetéssel ellenőrzés
    QTimer.singleShot(500, start_auto_update)

    sys.exit(app.exec())