import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from .processor import run
from .viewer import CSVViewer

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from theme import get_dark_theme_stylesheet, get_action_button_stylesheet, get_browse_button_stylesheet

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Autóköltség Feldolgozó")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "otp_icon.png")))
        self.setMinimumWidth(300)
        self.setMinimumHeight(220)

        # PDF fájl sor
        self.pdf_path_input = QLineEdit()
        self.pdf_path_input.setPlaceholderText("PDF fájl elérési útja...")
        self.pdf_browse_btn = QPushButton("📂")
        self.pdf_browse_btn.setMaximumWidth(45)
        self.pdf_browse_btn.setToolTip("Tallózás a PDF fájlhoz")
        self.pdf_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.pdf_browse_btn.clicked.connect(self.browse_pdf)

        # Autók Excel sor
        self.xlsx_path_input = QLineEdit()
        self.xlsx_path_input.setPlaceholderText("Autók Excel elérési útja...")
        self.xlsx_browse_btn = QPushButton("📂")
        self.xlsx_browse_btn.setMaximumWidth(45)
        self.xlsx_browse_btn.setToolTip("Tallózás az autók Excel fájlhoz")
        self.xlsx_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.xlsx_browse_btn.clicked.connect(self.browse_xlsx)

        # Feldolgozás gomb
        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setMinimumHeight(36)
        self.process_btn.setStyleSheet(get_action_button_stylesheet())
        self.process_btn.setToolTip("PDF és Excel feldolgozása")
        self.process_btn.clicked.connect(self.process_file)

        # Grouping
        input_group = QGroupBox("📁 Bemeneti fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(self._create_row("PDF fájl:", self.pdf_path_input, self.pdf_browse_btn))
        input_layout.addLayout(self._create_row("Autók Excel:", self.xlsx_path_input, self.xlsx_browse_btn))
        input_group.setLayout(input_layout)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.process_btn)

        self.setLayout(layout)
        self.setStyleSheet(get_dark_theme_stylesheet())

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF fájl kiválasztása", "", "PDF fájlok (*.pdf)")
        if path:
            self.pdf_path_input.setText(path)

    def browse_xlsx(self):
        path, _ = QFileDialog.getOpenFileName(self, "Autók Excel kiválasztása", "", "Excel fájlok (*.xlsx)")
        if path:
            self.xlsx_path_input.setText(path)

    def process_file(self):
        pdf_path = self.pdf_path_input.text()
        xlsx_path = self.xlsx_path_input.text()
        if not pdf_path:
            QMessageBox.warning(self, "Nincs PDF", "Először válassz ki egy PDF-et.")
            return
        if not xlsx_path:
            QMessageBox.warning(self, "Nincs autók Excel", "Először válassz ki egy autók Excel fájlt.")
            return
        try:
            run(pdf_path, xlsx_path)
            QMessageBox.information(self, "Siker", "A feldolgozás sikeresen lefutott.")

            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_csv_path = os.path.join(BASE_DIR, "output", "output.csv")

            viewer = CSVViewer(output_csv_path)
            viewer.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{str(e)}")