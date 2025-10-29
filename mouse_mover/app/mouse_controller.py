"""
Mouse controller module using PySide6's QCursor for mouse movement.
"""
from PySide6.QtGui import QCursor
from PySide6.QtCore import QTimer, QObject, Signal
import random


class MouseController(QObject):
    """Controls automatic mouse movement."""
    
    status_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._move_mouse)
        self.is_running = False
        self.interval_seconds = 30
        self.move_distance = 5
        
    def start(self, interval_seconds=30, move_distance=5):
        """Start automatic mouse movement.
        
        Args:
            interval_seconds: Interval between movements in seconds
            move_distance: Maximum distance to move in pixels
        """
        if self.is_running:
            return
            
        self.interval_seconds = interval_seconds
        self.move_distance = move_distance
        self.is_running = True
        
        # Start timer with interval in milliseconds
        self.timer.start(interval_seconds * 1000)
        self.status_changed.emit(f"Elindítva: {interval_seconds}s időközönként, {move_distance}px mozgás")
        
    def stop(self):
        """Stop automatic mouse movement."""
        if not self.is_running:
            return
            
        self.timer.stop()
        self.is_running = False
        self.status_changed.emit("Leállítva")
        
    def _move_mouse(self):
        """Move mouse by a small random amount."""
        current_pos = QCursor.pos()
        
        # Generate random offset
        dx = random.randint(-self.move_distance, self.move_distance)
        dy = random.randint(-self.move_distance, self.move_distance)
        
        # Move cursor to new position
        new_x = current_pos.x() + dx
        new_y = current_pos.y() + dy
        
        QCursor.setPos(new_x, new_y)
        self.status_changed.emit(f"Egér mozgatva: ({dx}, {dy}) @ {current_pos.x()},{current_pos.y()}")
