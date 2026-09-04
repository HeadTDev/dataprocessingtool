from typing import Any, Callable

from PySide6.QtCore import QObject, Qt, QThread
from PySide6.QtWidgets import QProgressDialog, QWidget

from app.backend.workers.background_worker import BackgroundWorker


class BackgroundTask(QObject):
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
        super().__init__(parent)
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
        self.progress_dialog = self._get_progress_dialog()
        self.progress_dialog.setWindowTitle(self.title)
        self.progress_dialog.setLabelText("Előkészítés...")
        self.progress_dialog.setRange(0, 100)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

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

    def _get_progress_dialog(self) -> QProgressDialog:
        """Returns a single QProgressDialog reused across every run for this
        parent widget, instead of constructing a new WindowModal dialog each
        time. Two independently-constructed WindowModal QProgressDialogs can
        briefly coexist on fast, back-to-back runs (setValue() pumps the Qt
        event loop internally, which can reenter this class mid-call) and
        closing one while the other is mid-show can wedge Qt's internal
        modal-window bookkeeping, freezing the whole UI. Reusing one dialog
        object per parent makes that overlap impossible by construction.
        """
        dialog = getattr(self.parent, "_shared_progress_dialog", None)
        if dialog is None:
            dialog = QProgressDialog("", "Mégse", 0, 100, self.parent)
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            dialog.setMinimumDuration(0)
            dialog.setAutoClose(False)
            dialog.setAutoReset(False)
            self.parent._shared_progress_dialog = dialog
        else:
            try:
                dialog.canceled.disconnect()
            except (RuntimeError, TypeError):
                pass  # nothing was connected
        return dialog

    def cancel(self):
        if self.worker is not None:
            self.worker.request_cancel()

    def _on_progress(self, message: str, current: int, total: int):
        dialog = self.progress_dialog
        if dialog is None:
            return
        try:
            if total > 0:
                dialog.setRange(0, total)
                dialog.setValue(current)
            else:
                dialog.setRange(0, 0)
            dialog.setLabelText(message)
        except RuntimeError:
            pass

    def _on_result(self, result: Any):
        self._hide_progress_dialog()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.on_result(result))

    def _on_error(self, error_message: str):
        self._hide_progress_dialog()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.on_error(error_message))

    def _on_finished(self):
        self.button.setEnabled(True)
        self.thread = None
        self.worker = None
        self._hide_progress_dialog()
        if self.on_finished is not None:
            self.on_finished()

    def _hide_progress_dialog(self):
        if self.progress_dialog is None:
            return
        dialog = self.progress_dialog
        self.progress_dialog = None
        try:
            dialog.hide()
        except RuntimeError:
            pass
