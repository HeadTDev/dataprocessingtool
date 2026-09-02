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
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter

from app.backend.modules.mouse_mover.service import CursorMover, MoveSettings

from app.frontend.theme import (
    COLOR_ACCENT,
    COLOR_BORDER_STRONG,
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    BUTTON_HEIGHT_COMPACT,
    ICON_SIZE_INLINE,
    SPACE_3,
    SPACE_4,
    SPACE_5,
    get_browse_button_stylesheet,
    get_icon,
)


class _ToggleSwitch(QWidget):
    """A persistent on/off switch (not a QPushButton) - Mouse Mover is a
    background state, not a one-shot action, so it gets a control that reads
    that way at a glance, matching OS-level Wi-Fi/Bluetooth toggles."""

    toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self._checked = False
        self._knob_pos = 3.0
        self.setFixedSize(38, 20)
        self.setCursor(Qt.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"knobPos")
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        """Sets the visual state only - does not emit `toggled`, so callers
        can sync the switch to external state changes without feedback loops."""
        if checked == self._checked:
            return
        self._checked = checked
        self._animate_to(checked)

    def _animate_to(self, checked: bool):
        end = float(self.width() - self.height() + 3) if checked else 3.0
        self._anim.stop()
        self._anim.setStartValue(self._knob_pos)
        self._anim.setEndValue(end)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate_to(self._checked)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _get_knob_pos(self) -> float:
        return self._knob_pos

    def _set_knob_pos(self, value: float):
        self._knob_pos = value
        self.update()

    knobPos = Property(float, _get_knob_pos, _set_knob_pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        track_color = QColor(COLOR_ACCENT if self._checked else COLOR_BORDER_STRONG)
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        knob_d = rect.height() - 6
        painter.setBrush(QColor(COLOR_TEXT_PRIMARY))
        painter.drawEllipse(QRectF(self._knob_pos, 3.0, knob_d, knob_d))


class _SettingsPage(QWidget):
    """The Mouse Mover fine-tuning sliders, shown as a regular content page
    (like the other modules) when the footer's Settings button is clicked."""

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(280)

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

        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setRange(10, 6000)
        self.interval_slider.setValue(100)
        self.interval_slider.setToolTip("Wait time between automatic movements in seconds")
        self.interval_label = QLabel("10.0 s")
        self.interval_label.setMinimumWidth(50)
        self.interval_label.setAlignment(Qt.AlignRight)
        self.interval_slider.valueChanged.connect(lambda v: self.interval_label.setText(f"{v / 10.0:.1f} s"))

        self.curve_slider = QSlider(Qt.Horizontal)
        self.curve_slider.setRange(5, 90)
        self.curve_slider.setValue(35)
        self.curve_slider.setToolTip("Higher = more curved, serpent-like paths")
        self.curve_label = QLabel("0.35")
        self.curve_label.setMinimumWidth(50)
        self.curve_label.setAlignment(Qt.AlignRight)
        self.curve_slider.valueChanged.connect(lambda v: self.curve_label.setText(f"{v / 100.0:.2f}"))

        motion_group = QGroupBox("Motion")
        motion_layout = QVBoxLayout()
        motion_layout.addLayout(self._slider_row("Min distance:", self.min_dist_slider, self.min_dist_label))
        motion_layout.addLayout(self._slider_row("Max distance:", self.max_dist_slider, self.max_dist_label))
        motion_group.setLayout(motion_layout)

        timing_group = QGroupBox("Timing")
        timing_layout = QVBoxLayout()
        timing_layout.addLayout(self._slider_row("Min duration (s):", self.min_dur_slider, self.min_dur_label))
        timing_layout.addLayout(self._slider_row("Max duration (s):", self.max_dur_slider, self.max_dur_label))
        timing_layout.addLayout(self._slider_row("Move every (s):", self.interval_slider, self.interval_label))
        timing_group.setLayout(timing_layout)

        curve_group = QGroupBox("Curve")
        curve_layout = QVBoxLayout()
        curve_layout.addLayout(self._slider_row("Intensity:", self.curve_slider, self.curve_label))
        curve_group.setLayout(curve_layout)

        title = QLabel("Mouse Mover beállítások")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_5, SPACE_5, SPACE_5, SPACE_5)
        layout.setSpacing(SPACE_4)
        layout.addWidget(title)
        layout.addWidget(motion_group)
        layout.addWidget(timing_group)
        layout.addWidget(curve_group)
        layout.addStretch()

    def _slider_row(self, label_text, slider, value_label):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(110)
        row.addWidget(label)
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        return row

    def read_settings(self) -> MoveSettings:
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


class _FooterBar(QWidget):
    """Compact, always-visible Mouse Mover status + control, grouped into a
    single "pill" so it reads as one unit instead of loose, scattered controls.

    Sized to its own content (not stretched) so the parent footer row can
    center it; reads slider values from the associated settings page rather
    than owning them itself.
    """

    settingsRequested = Signal()

    def __init__(self, settings_page: _SettingsPage):
        super().__init__()
        self._settings_page = settings_page
        self._mover = None
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_countdown)

        icon_size = QSize(ICON_SIZE_INLINE, ICON_SIZE_INLINE)

        self.name_label = QLabel("Mouse Mover")
        name_font = self.name_label.font()
        name_font.setBold(True)
        name_font.setPointSize(name_font.pointSize() - 1)
        self.name_label.setFont(name_font)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 12px;")
        self.status_text = QLabel("Idle")
        status_font = QFont()
        status_font.setPointSize(9)
        self.status_text.setFont(status_font)
        self.status_text.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        # Fixed width, computed from the actual rendered font (not guessed),
        # sized to the longest status word - just enough to avoid a resize/
        # shift when the status changes, without leaving dead space.
        metrics = QFontMetrics(status_font)
        widest_status = max(
            metrics.horizontalAdvance(word) for word in ("Idle", "Running", "Stopped")
        )
        self.status_text.setFixedWidth(widest_status + 2)

        self.toggle_switch = _ToggleSwitch()
        self.toggle_switch.setToolTip("Mouse Mover be/ki")
        self.toggle_switch.toggled.connect(self._on_toggle)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(get_icon("sliders"))
        self.settings_btn.setIconSize(icon_size)
        self.settings_btn.setFixedSize(BUTTON_HEIGHT_COMPACT, BUTTON_HEIGHT_COMPACT)
        self.settings_btn.setToolTip("Mouse Mover beállítások megnyitása")
        self.settings_btn.setStyleSheet(get_browse_button_stylesheet())
        self.settings_btn.clicked.connect(self.settingsRequested.emit)

        pill = QWidget()
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(0, 0, 0, 0)
        pill_layout.setSpacing(SPACE_3)
        pill_layout.addWidget(self.name_label)
        pill_layout.addWidget(self.status_indicator)
        pill_layout.addWidget(self.status_text)
        pill_layout.addWidget(self.toggle_switch)
        pill_layout.addWidget(self.settings_btn)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(pill)

    def _on_toggle(self, checked: bool):
        if checked:
            self.start_mover()
        else:
            self.stop_mover()

    def start_mover(self):
        try:
            settings = self._settings_page.read_settings()
        except ValueError as exc:
            self.toggle_switch.setChecked(False)
            QMessageBox.warning(self, "Invalid settings", str(exc))
            return

        if self._mover is None:
            self._mover = CursorMover(settings)
            self._mover.userInterruption.connect(self._on_user_interrupt)
        else:
            self._mover.settings = settings

        self._mover.start()
        self.toggle_switch.setChecked(True)
        self.status_indicator.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")
        self.status_text.setText("Running")
        self._countdown_timer.start(100)

    def stop_mover(self):
        if self._mover is None:
            return
        self._mover.stop()
        self._countdown_timer.stop()
        self.toggle_switch.setChecked(False)
        self.status_indicator.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 12px;")
        self.status_text.setText("Idle")
        self.status_text.setToolTip("")

    def _on_user_interrupt(self):
        self._countdown_timer.stop()
        self.toggle_switch.setChecked(False)
        self.status_indicator.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px;")
        self.status_text.setText("Stopped")
        self.status_text.setToolTip("Leállt, mert mozgattad az egeret.")

    def _update_countdown(self):
        if self._mover is None or not self._mover.is_running():
            return
        idle_remaining = self._mover._idle_timer.remainingTime()
        if idle_remaining > 0:
            countdown_s = idle_remaining / 1000.0
            self.status_text.setToolTip(f"Next move in {countdown_s:.1f}s")

    def closeEvent(self, event):
        self._countdown_timer.stop()
        if self._mover is not None:
            self._mover.stop()
        event.accept()


class MainUI:
    """Coordinator for the mouse_mover module: builds the always-visible
    footer bar and the on-demand settings page, and wires them together.

    Not a QWidget itself - the main window places `.footer` in the bottom
    bar and `.settings_page` in the content stack, showing the latter when
    `.footer.settingsRequested` fires.
    """

    def __init__(self):
        self.settings_page = _SettingsPage()
        self.footer = _FooterBar(self.settings_page)

    def close(self):
        self.footer.close()
        self.settings_page.close()
