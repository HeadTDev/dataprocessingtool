import re

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.config.paths import LOGS_DIR
from app.frontend.theme import (
    COLOR_BG_INPUT,
    COLOR_BORDER_DEFAULT,
    COLOR_TEXT_PRIMARY,
    RADIUS_SM,
    SPACE_2,
    SPACE_3,
    SPACE_5,
)

_ENTRY_START_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| ")
_MAX_ENTRIES = 2000
_REFRESH_MS = 1000


class LogViewer(QDialog):
    """Read-only, combined view of every module's current log file.

    Tails each logs/<module>/<module>.log for newly appended bytes (no
    re-reading from scratch every tick), merges the parsed entries by
    timestamp across modules, and re-renders while the dialog is visible.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Napló")
        self.resize(1150, 480)
        self.setModal(False)

        self._offsets: dict[str, int] = {}
        self._entries: list[tuple[str, str]] = []  # (timestamp_str, full_text)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Szűrés:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("pl. ERROR, ksh, ...")
        self.filter_input.textChanged.connect(self._render)
        header_row.addWidget(self.filter_input, 1)
        self.autoscroll_check = QCheckBox("Automatikus görgetés")
        self.autoscroll_check.setChecked(True)
        header_row.addWidget(self.autoscroll_check)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        mono_font = QFont("Consolas")
        mono_font.setStyleHint(QFont.Monospace)
        mono_font.setPointSize(9)
        self.text.setFont(mono_font)
        self.text.setStyleSheet(
            f"background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY};"
            f"border: 1px solid {COLOR_BORDER_DEFAULT}; border-radius: {RADIUS_SM}px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_5, SPACE_5, SPACE_5, SPACE_5)
        layout.setSpacing(SPACE_3)
        layout.addLayout(header_row)
        layout.addWidget(self.text, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.setInterval(_REFRESH_MS)

    def showEvent(self, event):
        super().showEvent(event)
        self._poll()
        self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _log_files(self):
        if not LOGS_DIR.exists():
            return []
        files = []
        for module_dir in LOGS_DIR.iterdir():
            if not module_dir.is_dir():
                continue
            log_file = module_dir / f"{module_dir.name}.log"
            if log_file.exists():
                files.append(log_file)
        return files

    def _poll(self):
        changed = False
        for path in self._log_files():
            key = str(path)
            try:
                size = path.stat().st_size
            except OSError:
                continue
            last_offset = self._offsets.get(key, 0)
            if size < last_offset:
                last_offset = 0  # rotated/truncated - start over from this point
            if size == last_offset:
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_offset)
                    new_text = f.read()
                    self._offsets[key] = f.tell()
            except OSError:
                continue
            self._ingest(new_text)
            changed = True

        if changed:
            self._entries.sort(key=lambda e: e[0])
            if len(self._entries) > _MAX_ENTRIES:
                self._entries = self._entries[-_MAX_ENTRIES:]
            self._render()

    def _ingest(self, chunk: str):
        for line in chunk.splitlines():
            if not line:
                continue
            if _ENTRY_START_RE.match(line):
                timestamp = line[:23]
                self._entries.append((timestamp, line))
            elif self._entries:
                # Continuation line (e.g. exception traceback) - belongs to
                # the previous entry, not a separately sortable line.
                ts, text = self._entries[-1]
                self._entries[-1] = (ts, text + "\n" + line)

    def _render(self):
        needle = self.filter_input.text().strip().lower()
        lines = [text for _, text in self._entries if not needle or needle in text.lower()]
        self.text.setPlainText("\n".join(lines))
        if self.autoscroll_check.isChecked():
            scrollbar = self.text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
