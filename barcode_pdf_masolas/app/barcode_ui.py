import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from .barcode_copier import copy_matching_pdfs

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from theme import get_dark_theme_stylesheet, get_action_button_stylesheet, get_browse_button_stylesheet

class BarcodeCopierWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vonalkód alapú PDF másoló")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "pdf_icon.png")))
        self.setMinimumWidth(280)
        self.setMinimumHeight(220)

        self.excel_path_input = QLineEdit()
        self.excel_path_input.setPlaceholderText("Excel fájl elérési útja...")
        self.excel_browse_btn = QPushButton("📂")
        self.excel_browse_btn.setMaximumWidth(45)
        self.excel_browse_btn.setToolTip("Tallózás az Excel fájlhoz")
        self.excel_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.excel_browse_btn.clicked.connect(self.browse_excel)

        self.pdf_folder_input = QLineEdit()
        self.pdf_folder_input.setPlaceholderText("PDF mappa elérési útja...")
        self.pdf_browse_btn = QPushButton("📂")
        self.pdf_browse_btn.setMaximumWidth(45)
        self.pdf_browse_btn.setToolTip("Tallózás a PDF mappához")
        self.pdf_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.pdf_browse_btn.clicked.connect(self.browse_pdf_folder)

        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Kimeneti mappa elérési útja...")
        self.output_browse_btn = QPushButton("📂")
        self.output_browse_btn.setMaximumWidth(45)
        self.output_browse_btn.setToolTip("Tallózás a kimeneti mappához")
        self.output_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.output_browse_btn.clicked.connect(self.browse_output_folder)

        self.copy_btn = QPushButton("📋 MÁSOL")
        self.copy_btn.setMinimumHeight(36)
        self.copy_btn.setStyleSheet(get_action_button_stylesheet())
        self.copy_btn.setToolTip("Vonalkódok alapján PDF fájlok másolása")
        self.copy_btn.clicked.connect(self.start_copying)

        # Grouping
        input_group = QGroupBox("📁 Fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(self._create_row("Excel:", self.excel_path_input, self.excel_browse_btn))
        input_layout.addLayout(self._create_row("PDF mappa:", self.pdf_folder_input, self.pdf_browse_btn))
        input_layout.addLayout(self._create_row("Kimenet:", self.output_folder_input, self.output_browse_btn))
        input_group.setLayout(input_layout)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.copy_btn)

        self.setLayout(layout)
        self.setStyleSheet(get_dark_theme_stylesheet())

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Excel fájl kiválasztása", "", "Excel fájlok (*.xlsx *.xls)")
        if path:
            self.excel_path_input.setText(path)

    def browse_pdf_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "PDF fájlokat tartalmazó mappa kiválasztása")
        if folder:
            self.pdf_folder_input.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Kimeneti mappa kiválasztása")
        if folder:
            self.output_folder_input.setText(folder)

    def start_copying(self):
        excel_path = self.excel_path_input.text()
        pdf_folder = self.pdf_folder_input.text()
        output_folder = self.output_folder_input.text()

        try:
            count = copy_matching_pdfs(excel_path, pdf_folder, output_folder)
            QMessageBox.information(self, "Siker", f"{count} PDF fájl sikeresen átmásolva.")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt a másolás során:\n{str(e)}")
