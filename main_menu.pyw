import sys
import subprocess
import threading

from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt

BUTTON_SIZE = (300, 40)

class UpdateUIBridge(QObject):
    requestPrompt = Signal(str)
    requestInfo = Signal(str)
    requestError = Signal(str)
    requestSetVersion = Signal(str)  # új jel a verzió label frissítéshez

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

    # Induláskor (mielőtt frissítést kérünk) megpróbáljuk kiolvasni a lokális verziót
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
        self.setWindowIcon(QIcon("synthwave_icon.png"))
        self.setMinimumSize(320, 220)
        self.version_label = QLabel("Verzió: betöltés...")
        f = self.version_label.font()
        f.setPointSize(f.pointSize() - 1)
        self.version_label.setFont(f)
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

        # Üres hely a verzió címke előtt
        layout.addStretch()
        layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    # Verzió + frissítés indítása
    QTimer.singleShot(500, lambda: start_auto_update(window.version_label))
    sys.exit(app.exec())