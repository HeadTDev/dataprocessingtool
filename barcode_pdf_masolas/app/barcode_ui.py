import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from app.barcode_copier import copy_matching_pdfs

class BarcodeCopierWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vonalkód alapú PDF másoló")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "pdf_icon.png")))

        self.excel_path_input = QLineEdit()
        self.excel_browse_btn = QPushButton("📂 Tallózás")
        self.excel_browse_btn.clicked.connect(self.browse_excel)

        self.pdf_folder_input = QLineEdit()
        self.pdf_browse_btn = QPushButton("📂 Tallózás")
        self.pdf_browse_btn.clicked.connect(self.browse_pdf_folder)

        self.output_folder_input = QLineEdit()
        self.output_browse_btn = QPushButton("📂 Tallózás")
        self.output_browse_btn.clicked.connect(self.browse_output_folder)

        self.copy_btn = QPushButton("📋 MÁSOL")
        self.copy_btn.setFixedSize(300, 40)
        self.copy_btn.clicked.connect(self.start_copying)

        layout = QVBoxLayout()

        layout.addLayout(self._create_row("Vonalkód Excel fájl:", self.excel_path_input, self.excel_browse_btn))
        layout.addLayout(self._create_row("PDF fájlok mappája:", self.pdf_folder_input, self.pdf_browse_btn))
        layout.addLayout(self._create_row("Kimeneti mappa:", self.output_folder_input, self.output_browse_btn))
        layout.addWidget(self.copy_btn)

        self.setLayout(layout)
        self.setMinimumWidth(320)

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(input_widget)
        row.addWidget(button_widget)
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