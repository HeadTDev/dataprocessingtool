"""
Mouse Mover UI using PySide6.
Simple automatic mouse movement application to prevent screen savers and auto-lock.
"""
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QSpinBox,
    QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from .mouse_controller import MouseController


class MouseMoverWindow(QWidget):
    """Main window for the mouse mover application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🖱️ Automatikus Egér Mozgató")
        
        # Try to set icon if available
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "synthwave_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.controller = MouseController()
        self.controller.status_changed.connect(self.update_status)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Ez az alkalmazás automatikusan mozgatja az egeret kis távolságokkal,\n"
            "hogy megakadályozza a képernyővédő vagy automatikus zárolás aktiválódását."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Settings group
        settings_group = QGroupBox("Beállítások")
        settings_layout = QVBoxLayout()
        
        # Interval setting
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Időköz (másodperc):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(5)
        self.interval_spinbox.setMaximum(300)
        self.interval_spinbox.setValue(30)
        self.interval_spinbox.setToolTip("Milyen gyakran mozogjon az egér (5-300 másodperc)")
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        settings_layout.addLayout(interval_layout)
        
        # Distance setting
        distance_layout = QHBoxLayout()
        distance_layout.addWidget(QLabel("Mozgási távolság (pixel):"))
        self.distance_spinbox = QSpinBox()
        self.distance_spinbox.setMinimum(1)
        self.distance_spinbox.setMaximum(50)
        self.distance_spinbox.setValue(5)
        self.distance_spinbox.setToolTip("Maximális mozgási távolság pixelekben (1-50)")
        distance_layout.addWidget(self.distance_spinbox)
        distance_layout.addStretch()
        settings_layout.addLayout(distance_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶️ Indítás")
        self.start_button.setFixedSize(150, 40)
        self.start_button.clicked.connect(self.start_movement)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ Leállítás")
        self.stop_button.setFixedSize(150, 40)
        self.stop_button.clicked.connect(self.stop_movement)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Status display
        status_group = QGroupBox("Állapot")
        status_layout = QVBoxLayout()
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(150)
        self.status_display.setPlainText("Várakozás indításra...")
        status_layout.addWidget(self.status_display)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        self.setLayout(layout)
        self.setMinimumSize(400, 350)
        
    def start_movement(self):
        """Start the automatic mouse movement."""
        interval = self.interval_spinbox.value()
        distance = self.distance_spinbox.value()
        
        self.controller.start(interval, distance)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.interval_spinbox.setEnabled(False)
        self.distance_spinbox.setEnabled(False)
        
    def stop_movement(self):
        """Stop the automatic mouse movement."""
        self.controller.stop()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.interval_spinbox.setEnabled(True)
        self.distance_spinbox.setEnabled(True)
        
    def update_status(self, message):
        """Update the status display with a new message."""
        current_text = self.status_display.toPlainText()
        lines = current_text.split('\n')
        
        # Keep only last 10 lines
        if len(lines) >= 10:
            lines = lines[-9:]
        
        lines.append(message)
        self.status_display.setPlainText('\n'.join(lines))
        
        # Scroll to bottom
        cursor = self.status_display.textCursor()
        cursor.movePosition(cursor.End)
        self.status_display.setTextCursor(cursor)
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop the controller when window closes
        self.controller.stop()
        event.accept()
