from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import os
from .process import Processor

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from theme import get_dark_theme_stylesheet, get_action_button_stylesheet, get_browse_button_stylesheet
from utils import resource_path

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KSH + Matstamm egyesítő")
        self.setWindowIcon(QIcon(resource_path("icons", "ksh_icon.png")))
        self.setMinimumWidth(320)
        self.setMinimumHeight(210)

        self.ksh_input = QLineEdit()
        self.ksh_input.setPlaceholderText("KSH fájl elérési útja...")
        ksh_btn = QPushButton("📂")
        ksh_btn.setMaximumWidth(45)
        ksh_btn.setToolTip("Tallózás a KSH fájlhoz")
        ksh_btn.setStyleSheet(get_browse_button_stylesheet())
        ksh_btn.clicked.connect(self.browse_ksh)

        self.mat_input = QLineEdit()
        self.mat_input.setPlaceholderText("Matstamm fájl elérési útja...")
        mat_btn = QPushButton("📂")
        mat_btn.setMaximumWidth(45)
        mat_btn.setToolTip("Tallózás a Matstamm fájlhoz")
        mat_btn.setStyleSheet(get_browse_button_stylesheet())
        mat_btn.clicked.connect(self.browse_mat)

        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setMinimumHeight(36)
        self.process_btn.setStyleSheet(get_action_button_stylesheet())
        self.process_btn.setToolTip("KSH és Matstamm fájlok feldolgozása")
        self.process_btn.clicked.connect(self.process_files)

        # Grouping
        input_group = QGroupBox("📁 Bemeneti fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(self._row("KSH fájl:", self.ksh_input, ksh_btn))
        input_layout.addLayout(self._row("Matstamm:", self.mat_input, mat_btn))
        input_group.setLayout(input_layout)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.process_btn)

        self.processor = Processor()
        self.setStyleSheet(get_dark_theme_stylesheet())

    def _row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_ksh(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "KSH fájl kiválasztása",
            "",
            "Minden fájl (*.*)",
        )
        if path:
            self.ksh_input.setText(path)

    def browse_mat(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Matstamm fájl kiválasztása",
            "",
            "Excel munkafüzet (*.xlsx);;Minden fájl (*.*)",
        )
        if path:
            self.mat_input.setText(path)

    def process_files(self):
        ksh = self.ksh_input.text().strip()
        mat = self.mat_input.text().strip()

        if not ksh:
            QMessageBox.warning(self, "Hiányzó KSH", "Válaszd ki a KSH fájlt.")
            return
        if not mat:
            QMessageBox.warning(self, "Hiányzó Matstamm", "Válaszd ki a Matstamm fájlt.")
            return

        try:
            output_path = self.processor.process(ksh, mat)
            QMessageBox.information(
                self,
                "Kész",
                f"A feldolgozás elkészült.\nAz új fájl itt található:\n{output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{e}")