import ctypes
import math
import random
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class MoveSettings:
    min_distance: int = 60
    max_distance: int = 150
    min_duration_s: float = 0.6
    max_duration_s: float = 1.6
    curve_intensity: float = 0.35
    move_interval_s: float = 10.0


class CursorMover(QObject):
    userInterruption = Signal()

    def __init__(self, settings: MoveSettings):
        super().__init__()
        self.settings = settings
        self._step_timer = QTimer(self)
        self._step_timer.timeout.connect(self._step)
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._begin_move)
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._monitor_user_move)
        self._moving = False
        self._path = []
        self._index = 0
        self._base_interval_ms = 10
        self._last_auto_pos = None

    def start(self):
        if self._moving:
            return
        self._moving = True
        self._path = []
        self._index = 0
        self._last_auto_pos = _get_cursor_pos()
        self._monitor_timer.start(200)
        self._schedule_next_move()

    def stop(self):
        self._moving = False
        self._step_timer.stop()
        self._idle_timer.stop()
        self._monitor_timer.stop()

    def is_running(self) -> bool:
        return self._moving

    def _step(self):
        if not self._moving:
            return
        if self._index >= len(self._path):
            self._finish_move()
            return
        if not self._path:
            return

        x, y = self._path[self._index]
        _set_cursor_pos(x, y)
        self._last_auto_pos = (x, y)
        self._index += 1

        jitter = random.uniform(0.8, 1.2)
        interval = max(5, int(self._base_interval_ms * jitter))
        self._step_timer.setInterval(interval)

    def _begin_move(self):
        if not self._moving:
            return
        self._build_path()
        if not self._path:
            self._schedule_next_move()
            return
        self._step_timer.start(self._base_interval_ms)

    def _finish_move(self):
        self._step_timer.stop()
        self._path = []
        self._index = 0
        self._schedule_next_move()

    def _schedule_next_move(self):
        interval_ms = max(500, int(self.settings.move_interval_s * 1000))
        self._idle_timer.start(interval_ms)

    def _monitor_user_move(self):
        if not self._moving:
            return
        if self._last_auto_pos is None:
            return
        x, y = _get_cursor_pos()
        lx, ly = self._last_auto_pos
        if abs(x - lx) > 2 or abs(y - ly) > 2:
            self.stop()
            self.userInterruption.emit()

    def _build_path(self):
        start_x, start_y = _get_cursor_pos()
        end_x, end_y = _pick_target(start_x, start_y, self.settings)
        distance = math.hypot(end_x - start_x, end_y - start_y)

        duration_s = random.uniform(self.settings.min_duration_s, self.settings.max_duration_s)
        steps = _compute_steps(distance)
        total_ms = max(50, int(duration_s * 1000))
        self._base_interval_ms = max(5, int(total_ms / steps))

        self._path = _bezier_path(
            (start_x, start_y),
            (end_x, end_y),
            steps,
            self.settings.curve_intensity,
        )
        self._index = 0


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _get_cursor_pos() -> tuple[int, int]:
    pt = _Point()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def _set_cursor_pos(x: int, y: int) -> None:
    ctypes.windll.user32.SetCursorPos(int(x), int(y))


def _screen_size() -> tuple[int, int]:
    width = ctypes.windll.user32.GetSystemMetrics(0)
    height = ctypes.windll.user32.GetSystemMetrics(1)
    return int(width), int(height)


def _pick_target(start_x: int, start_y: int, settings: MoveSettings) -> tuple[int, int]:
    width, height = _screen_size()
    min_d = max(5, settings.min_distance)
    max_d = max(min_d + 1, settings.max_distance)

    for _ in range(8):
        angle = random.uniform(0, math.tau)
        dist = random.uniform(min_d, max_d)
        end_x = start_x + math.cos(angle) * dist
        end_y = start_y + math.sin(angle) * dist
        clamped_x = int(max(0, min(width - 1, end_x)))
        clamped_y = int(max(0, min(height - 1, end_y)))
        if math.hypot(clamped_x - start_x, clamped_y - start_y) >= min_d * 0.6:
            return clamped_x, clamped_y

    clamped_x = int(max(0, min(width - 1, start_x + min_d)))
    clamped_y = int(max(0, min(height - 1, start_y + min_d)))
    return clamped_x, clamped_y


def _compute_steps(distance: float) -> int:
    steps = int(max(18, min(220, distance * 0.8)))
    return max(steps, 18)


def _bezier_path(start: tuple[int, int], end: tuple[int, int], steps: int, curve: float) -> list[tuple[int, int]]:
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy) or 1.0

    nx = -dy / length
    ny = dx / length
    offset = length * max(0.05, min(0.9, curve))
    offset *= random.uniform(0.25, 0.75) * random.choice([-1.0, 1.0])

    c1x = sx + dx * 0.3 + nx * offset * random.uniform(0.4, 0.9)
    c1y = sy + dy * 0.3 + ny * offset * random.uniform(0.4, 0.9)
    c2x = sx + dx * 0.7 + nx * offset * random.uniform(0.4, 0.9)
    c2y = sy + dy * 0.7 + ny * offset * random.uniform(0.4, 0.9)

    path = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        x = (
            mt * mt * mt * sx
            + 3 * mt * mt * t * c1x
            + 3 * mt * t * t * c2x
            + t * t * t * ex
        )
        y = (
            mt * mt * mt * sy
            + 3 * mt * mt * t * c1y
            + 3 * mt * t * t * c2y
            + t * t * t * ey
        )
        path.append((int(x), int(y)))

    return path
