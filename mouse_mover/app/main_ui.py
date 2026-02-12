from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)

from .mover import CursorMover, MoveSettings


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Mover")
        self.setMinimumWidth(320)

        self.min_dist = QSpinBox()
        self.min_dist.setRange(5, 1000)
        self.min_dist.setValue(60)

        self.max_dist = QSpinBox()
        self.max_dist.setRange(10, 2000)
        self.max_dist.setValue(150)

        self.min_dur = QDoubleSpinBox()
        self.min_dur.setRange(0.2, 10.0)
        self.min_dur.setSingleStep(0.1)
        self.min_dur.setValue(0.6)

        self.max_dur = QDoubleSpinBox()
        self.max_dur.setRange(0.3, 15.0)
        self.max_dur.setSingleStep(0.1)
        self.max_dur.setValue(1.6)

        self.curve = QDoubleSpinBox()
        self.curve.setRange(0.05, 0.9)
        self.curve.setSingleStep(0.05)
        self.curve.setValue(0.35)

        self.interval = QDoubleSpinBox()
        self.interval.setRange(1.0, 600.0)
        self.interval.setSingleStep(1.0)
        self.interval.setValue(10.0)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedSize(140, 40)
        self.start_btn.clicked.connect(self.start_mover)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(140, 40)
        self.stop_btn.clicked.connect(self.stop_mover)
        self.stop_btn.setEnabled(False)

        self.status_label = QLabel("Status: idle")

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addLayout(self._row("Min distance (px):", self.min_dist))
        layout.addLayout(self._row("Max distance (px):", self.max_dist))
        layout.addLayout(self._row("Min duration (s):", self.min_dur))
        layout.addLayout(self._row("Max duration (s):", self.max_dur))
        layout.addLayout(self._row("Curve intensity:", self.curve))
        layout.addLayout(self._row("Move every (s):", self.interval))

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)

        layout.addLayout(btn_row)
        layout.addWidget(self.status_label)

        self._mover = None

    def _row(self, label_text, input_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(input_widget)
        return row

    def start_mover(self):
        try:
            settings = self._read_settings()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid settings", str(exc))
            return

        if self._mover is None:
            self._mover = CursorMover(settings)
            self._mover.userInterruption.connect(self._on_user_interrupt)
        else:
            self._mover.settings = settings

        self._mover.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: running")

    def stop_mover(self):
        if self._mover is None:
            return
        self._mover.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: idle")

    def _on_user_interrupt(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: stopped (user)")

    def _read_settings(self) -> MoveSettings:
        min_dist = int(self.min_dist.value())
        max_dist = int(self.max_dist.value())
        if max_dist <= min_dist:
            raise ValueError("Max distance must be greater than min distance.")

        min_dur = float(self.min_dur.value())
        max_dur = float(self.max_dur.value())
        if max_dur <= min_dur:
            raise ValueError("Max duration must be greater than min duration.")

        curve = float(self.curve.value())
        interval_s = float(self.interval.value())

        return MoveSettings(
            min_distance=min_dist,
            max_distance=max_dist,
            min_duration_s=min_dur,
            max_duration_s=max_dur,
            curve_intensity=curve,
            move_interval_s=interval_s,
        )

    def closeEvent(self, event):
        if self._mover is not None:
            self._mover.stop()
        event.accept()
