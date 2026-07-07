import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, Signal, Slot


class BackgroundWorker(QObject):
    progress = Signal(str, int, int)
    result = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._cancel_requested = False

    @Slot()
    def run(self):
        try:
            result = self.func(
                *self.args,
                progress_callback=self.report_progress,
                is_cancelled=self.is_cancelled,
                **self.kwargs,
            )
            self.result.emit(result)
        except Exception as exc:
            self.error.emit(f"{exc}\n\n{traceback.format_exc()}")
        finally:
            self.finished.emit()

    @Slot()
    def request_cancel(self):
        self._cancel_requested = True

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def report_progress(self, message: str, current: int, total: int):
        self.progress.emit(message, current, total)
