from typing import Any, Callable

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QProgressDialog, QWidget

from background_worker import BackgroundWorker


class BackgroundTask:
    def __init__(
        self,
        parent: QWidget,
        button,
        title: str,
        func: Callable[..., Any],
        args: tuple[Any, ...],
        on_result: Callable[[Any], None],
        on_error: Callable[[str], None],
        on_finished: Callable[[], None] | None = None,
    ):
        self.parent = parent
        self.button = button
        self.title = title
        self.func = func
        self.args = args
        self.on_result = on_result
        self.on_error = on_error
        self.on_finished = on_finished
        self.thread = None
        self.worker = None
        self.progress_dialog = None

    def start(self):
        self.button.setEnabled(False)
        self.progress_dialog = QProgressDialog(
            "Előkészítés...", "Mégse", 0, 100, self.parent
        )
        self.progress_dialog.setWindowTitle(self.title)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)

        self.thread = QThread(self.parent)
        self.worker = BackgroundWorker(self.func, *self.args)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._on_finished)
        self.progress_dialog.canceled.connect(self.worker.request_cancel)

        self.thread.start()

    def cancel(self):
        if self.worker is not None:
            self.worker.request_cancel()

    def _on_progress(self, message: str, current: int, total: int):
        if self.progress_dialog is None:
            return
        if total > 0:
            self.progress_dialog.setRange(0, total)
            self.progress_dialog.setValue(current)
        else:
            self.progress_dialog.setRange(0, 0)
        self.progress_dialog.setLabelText(message)

    def _on_result(self, result: Any):
        self._close_progress_dialog()
        self.on_result(result)

    def _on_error(self, error_message: str):
        self._close_progress_dialog()
        self.on_error(error_message)

    def _on_finished(self):
        self.button.setEnabled(True)
        self.thread = None
        self.worker = None
        self._close_progress_dialog()
        if self.on_finished is not None:
            self.on_finished()

    def _close_progress_dialog(self):
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
