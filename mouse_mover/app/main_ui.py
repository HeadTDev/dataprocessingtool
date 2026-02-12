from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from .mover import CursorMover, MoveSettings


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🖱️ Mouse Mover")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        self._apply_dark_theme()

        # Motion group: distance controls
        self.min_dist_slider = QSlider(Qt.Horizontal)
        self.min_dist_slider.setRange(5, 1000)
        self.min_dist_slider.setValue(60)
        self.min_dist_slider.setToolTip("Minimum cursor movement distance in pixels")
        self.min_dist_label = QLabel("60 px")
        self.min_dist_label.setMinimumWidth(50)
        self.min_dist_label.setAlignment(Qt.AlignRight)
        self.min_dist_slider.valueChanged.connect(lambda v: self.min_dist_label.setText(f"{v} px"))

        self.max_dist_slider = QSlider(Qt.Horizontal)
        self.max_dist_slider.setRange(10, 2000)
        self.max_dist_slider.setValue(150)
        self.max_dist_slider.setToolTip("Maximum cursor movement distance in pixels")
        self.max_dist_label = QLabel("150 px")
        self.max_dist_label.setMinimumWidth(50)
        self.max_dist_label.setAlignment(Qt.AlignRight)
        self.max_dist_slider.valueChanged.connect(lambda v: self.max_dist_label.setText(f"{v} px"))

        # Timing group: duration controls
        self.min_dur_slider = QSlider(Qt.Horizontal)
        self.min_dur_slider.setRange(2, 100)
        self.min_dur_slider.setValue(6)
        self.min_dur_slider.setToolTip("Minimum duration for each movement in seconds")
        self.min_dur_label = QLabel("0.6 s")
        self.min_dur_label.setMinimumWidth(50)
        self.min_dur_label.setAlignment(Qt.AlignRight)
        self.min_dur_slider.valueChanged.connect(lambda v: self.min_dur_label.setText(f"{v / 10.0:.1f} s"))

        self.max_dur_slider = QSlider(Qt.Horizontal)
        self.max_dur_slider.setRange(3, 150)
        self.max_dur_slider.setValue(16)
        self.max_dur_slider.setToolTip("Maximum duration for each movement in seconds")
        self.max_dur_label = QLabel("1.6 s")
        self.max_dur_label.setMinimumWidth(50)
        self.max_dur_label.setAlignment(Qt.AlignRight)
        self.max_dur_slider.valueChanged.connect(lambda v: self.max_dur_label.setText(f"{v / 10.0:.1f} s"))

        # Interval group: time between movements
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setRange(10, 6000)
        self.interval_slider.setValue(100)
        self.interval_slider.setToolTip("Wait time between automatic movements in seconds")
        self.interval_label = QLabel("10.0 s")
        self.interval_label.setMinimumWidth(50)
        self.interval_label.setAlignment(Qt.AlignRight)
        self.interval_slider.valueChanged.connect(lambda v: self.interval_label.setText(f"{v / 10.0:.1f} s"))

        # Curve group: curve intensity
        self.curve_slider = QSlider(Qt.Horizontal)
        self.curve_slider.setRange(5, 90)
        self.curve_slider.setValue(35)
        self.curve_slider.setToolTip("Higher = more curved, serpent-like paths")
        self.curve_label = QLabel("0.35")
        self.curve_label.setMinimumWidth(50)
        self.curve_label.setAlignment(Qt.AlignRight)
        self.curve_slider.valueChanged.connect(lambda v: self.curve_label.setText(f"{v / 100.0:.2f}"))

        # Buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #22aa44;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #28cc55;
            }
            QPushButton:pressed {
                background-color: #1a8833;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
        """)
        self.start_btn.clicked.connect(self.start_mover)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #cc2222;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_mover)
        self.stop_btn.setEnabled(False)

        # Status display
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #aa0000; font-size: 16px;")
        self.status_text = QLabel("Idle")
        status_font = QFont()
        status_font.setPointSize(11)
        status_font.setBold(True)
        self.status_text.setFont(status_font)

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        # Build layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Motion group
        motion_group = QGroupBox("🎯 Beweging (Motion)")
        motion_layout = QVBoxLayout()
        motion_layout.addLayout(self._slider_row("Min distance:", self.min_dist_slider, self.min_dist_label))
        motion_layout.addLayout(self._slider_row("Max distance:", self.max_dist_slider, self.max_dist_label))
        motion_group.setLayout(motion_layout)
        main_layout.addWidget(motion_group)

        # Timing group
        timing_group = QGroupBox("⏱️ Timing")
        timing_layout = QVBoxLayout()
        timing_layout.addLayout(self._slider_row("Min duration (s):", self.min_dur_slider, self.min_dur_label))
        timing_layout.addLayout(self._slider_row("Max duration (s):", self.max_dur_slider, self.max_dur_label))
        timing_layout.addLayout(self._slider_row("Move every (s):", self.interval_slider, self.interval_label))
        timing_group.setLayout(timing_layout)
        main_layout.addWidget(timing_group)

        # Curve group
        curve_group = QGroupBox("〰️ Curve")
        curve_layout = QVBoxLayout()
        curve_layout.addLayout(self._slider_row("Intensity:", self.curve_slider, self.curve_label))
        curve_group.setLayout(curve_layout)
        main_layout.addWidget(curve_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        # Status bar
        main_layout.addLayout(status_layout)

        self._mover = None
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_countdown)

    def _apply_dark_theme(self):
        stylesheet = """
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #444444;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444444;
                height: 6px;
                background: #2a2a2a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00aaff;
                border: 1px solid #00aaff;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #00ccff;
            }
            QLabel {
                color: #e0e0e0;
            }
        """
        self.setStyleSheet(stylesheet)

    def _slider_row(self, label_text, slider, value_label):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        row.addWidget(label)
        row.addWidget(slider, 1)
        row.addWidget(value_label)
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
        self.status_indicator.setStyleSheet("color: #22aa44; font-size: 16px;")
        self.status_text.setText("Running")
        self._countdown_timer.start(100)

    def stop_mover(self):
        if self._mover is None:
            return
        self._mover.stop()
        self._countdown_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_indicator.setStyleSheet("color: #aa0000; font-size: 16px;")
        self.status_text.setText("Idle")

    def _on_user_interrupt(self):
        self._countdown_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_indicator.setStyleSheet("color: #ffaa00; font-size: 16px;")
        self.status_text.setText("Stopped (user)")

    def _update_countdown(self):
        if self._mover is None or not self._mover.is_running():
            return
        idle_remaining = self._mover._idle_timer.remainingTime()
        if idle_remaining > 0:
            countdown_s = idle_remaining / 1000.0
            self.status_text.setText(f"Running • Next: {countdown_s:.1f}s")

    def _read_settings(self) -> MoveSettings:
        min_dist = int(self.min_dist_slider.value())
        max_dist = int(self.max_dist_slider.value())
        if max_dist <= min_dist:
            raise ValueError("Max distance must be greater than min distance.")

        min_dur = float(self.min_dur_slider.value()) / 10.0
        max_dur = float(self.max_dur_slider.value()) / 10.0
        if max_dur <= min_dur:
            raise ValueError("Max duration must be greater than min duration.")

        curve = float(self.curve_slider.value()) / 100.0
        interval_s = float(self.interval_slider.value()) / 10.0

        return MoveSettings(
            min_distance=min_dist,
            max_distance=max_dist,
            min_duration_s=min_dur,
            max_duration_s=max_dur,
            curve_intensity=curve,
            move_interval_s=interval_s,
        )

    def closeEvent(self, event):
        self._countdown_timer.stop()
        if self._mover is not None:
            self._mover.stop()
        event.accept()
