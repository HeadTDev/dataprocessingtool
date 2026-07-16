import threading

from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QMessageBox, QProgressDialog, QPushButton, QVBoxLayout, QWidget

from app.backend.services.update_service import perform_update_flow, read_local_version_info
from app.frontend.routes import ROUTES, AppRoute
from app.frontend.theme import get_action_button_stylesheet, get_dark_theme_stylesheet
from app.resources.resource_path import resource_path

BUTTON_SIZE = (300, 40)


class UpdateUIBridge(QObject):
    requestPrompt = Signal(str)
    requestInfo = Signal(str)
    requestError = Signal(str)
    requestSetVersion = Signal(str)
    requestProgress = Signal(str, int, int, bool)

    def __init__(self, version_label: QLabel):
        super().__init__()
        self._prompt_event = None
        self._prompt_answer = False
        self.version_label = version_label
        self._progress_dialog = None

        self.requestPrompt.connect(self._onPrompt, Qt.QueuedConnection)
        self.requestInfo.connect(self._onInfo, Qt.QueuedConnection)
        self.requestError.connect(self._onError, Qt.QueuedConnection)
        self.requestSetVersion.connect(self._onSetVersion, Qt.QueuedConnection)
        self.requestProgress.connect(self._onProgress, Qt.QueuedConnection)

    @Slot(str)
    def _onPrompt(self, question: str):
        res = QMessageBox.question(None, "Frissítés elérhető", question, QMessageBox.Yes | QMessageBox.No)
        self._prompt_answer = res == QMessageBox.Yes
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

    @Slot(str, int, int, bool)
    def _onProgress(self, label: str, current: int, total: int, done: bool):
        if done:
            if self._progress_dialog is not None:
                self._progress_dialog.close()
                self._progress_dialog.deleteLater()
                self._progress_dialog = None
            return

        if self._progress_dialog is None:
            dlg = QProgressDialog("Frissites folyamatban...", None, 0, 100)
            dlg.setWindowTitle("Frissites")
            dlg.setWindowModality(Qt.ApplicationModal)
            dlg.setMinimumDuration(0)
            dlg.setAutoClose(False)
            dlg.setAutoReset(False)
            dlg.setCancelButton(None)
            self._progress_dialog = dlg

        if total and total > 0:
            self._progress_dialog.setRange(0, total)
            self._progress_dialog.setValue(min(current, total))
        else:
            self._progress_dialog.setRange(0, 0)

        if label:
            self._progress_dialog.setLabelText(label)

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

    def ui_progress(self, label: str, current: int, total: int, done: bool):
        self.requestProgress.emit(label or "", int(current or 0), int(total or 0), bool(done))


_update_bridge = None


def start_auto_update(version_label: QLabel):
    global _update_bridge
    info = read_local_version_info()
    version_label.setText(f"Verzió: {info.get('version') or 'ismeretlen'}")
    _update_bridge = UpdateUIBridge(version_label)
    perform_update_flow(
        incremental_preferred=True,
        ui_prompt=_update_bridge.ui_prompt,
        ui_info=_update_bridge.ui_info,
        ui_error=_update_bridge.ui_error,
        ui_set_version=_update_bridge.ui_set_version,
        ui_progress=_update_bridge.ui_progress,
        run_in_thread=True,
        delay_seconds=1.0,
    )


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon(resource_path("icons", "synthwave_icon.png")))
        self.setMinimumSize(320, 220)
        self.version_label = QLabel("Verzió: betöltés...")
        font = self.version_label.font()
        font.setPointSize(font.pointSize() - 1)
        self.version_label.setFont(font)
        self._open_windows = {}
        self.init_ui()
        self.setStyleSheet(get_dark_theme_stylesheet())

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))
        for route in ROUTES:
            btn = QPushButton(route.label)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.setStyleSheet(get_action_button_stylesheet())
            btn.setEnabled(route.enabled)
            btn.clicked.connect(lambda _, r=route: self.open_route(r))
            layout.addWidget(btn)
        layout.addStretch()
        layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def open_route(self, route: AppRoute):
        window = self._open_windows.get(route.id)
        if window is not None:
            try:
                window.show()
                window.raise_()
                window.activateWindow()
                return
            except RuntimeError:
                self._open_windows.pop(route.id, None)
        try:
            window = route.view_class()
        except Exception as exc:
            QMessageBox.critical(self, "Hiba", f"Hiba a modul indításakor: {route.label}\n{exc}")
            return
        self._open_windows[route.id] = window
        try:
            window.destroyed.connect(lambda: self._open_windows.pop(route.id, None))
        except Exception:
            pass
        window.show()
        window.raise_()
        window.activateWindow()

    def closeEvent(self, event):
        for window in list(self._open_windows.values()):
            try:
                window.close()
            except Exception:
                pass
        event.accept()


# Static import hint for PyInstaller
if False:
    from app.frontend.modules.barcode_pdf.view import BarcodeCopierWindow as _BarcodeCopierWindow
    from app.frontend.modules.cofanet.view import CofanetHelpUI as _CofanetHelpUI
    from app.frontend.modules.ksh.view import MainUI as _KshView
    from app.frontend.modules.merkantil.view import MainUI as _MerkantilView
    from app.frontend.modules.mouse_mover.view import MainUI as _MouseMoverView
