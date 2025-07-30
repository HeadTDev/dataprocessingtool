import sys
import os
import csv

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QLineEdit
)

from .extract_data import extract_invoice_data_from_unicode_text

BUTTON_SIZE = (300, 40)

class ResultsTable(QWidget):
    def __init__(self, data, headers):
        super().__init__()
        self.setWindowTitle("Feldolgozott vevő adatok")
        layout = QVBoxLayout(self)
        table = QTableWidget(len(data), len(headers))
        table.setHorizontalHeaderLabels(headers)
        for row_idx, row in enumerate(data):
            for col_idx, item in enumerate(row):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        self.resize(800, 400)

class CofanetHelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cofanet Help")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "coface_icon.png")))
        self.resize(320, 200)

        self.selected_file = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Válaszd ki az SAP export (.xls, .txt, .csv) input fájlt!"))

        eur_layout = QVBoxLayout()
        eur_label = QLabel("EUR árfolyam:")
        self.eur_input = QLineEdit()
        self.eur_input.setPlaceholderText("Pl. 400")
        self.eur_input.setFixedSize(100, 30)
        eur_layout.addWidget(eur_label)
        eur_layout.addWidget(self.eur_input)
        layout.addLayout(eur_layout)

        browse_btn = QPushButton("📂 Tallózás (SAP)")
        browse_btn.setFixedSize(*BUTTON_SIZE)
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)

        process_btn = QPushButton("⚙️ Feldolgozás")
        process_btn.setFixedSize(*BUTTON_SIZE)
        process_btn.clicked.connect(self.process_file)
        layout.addWidget(process_btn)

    def browse_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilters(["SAP Unicode Text export (*.xls *.txt *.csv)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_file = selected_files[0]
                filename = os.path.basename(self.selected_file)
                QMessageBox.information(self, "Fájl kiválasztva", f"Kiválasztott fájl:\n{filename}")

    def process_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Hiba", "Először válassz ki egy input fájlt!")
            return

        try:
            eur_rate = float(self.eur_input.text().replace(',', '.').strip())
        except Exception:
            QMessageBox.warning(self, "Hiba", "Kérlek, érvényes EUR árfolyamot adj meg (pl. 400)!")
            return

        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            invoice_rows = extract_invoice_data_from_unicode_text(self.selected_file, eur_rate)
            invoice_rows_sorted = sorted(invoice_rows, key=lambda row: (row[0] or "").lower())
            output_path = os.path.join(output_dir, "vevok.csv")
            headers = [
                "Vevő",
                "Számla",
                "Összeg BP-ben",
                "BP pénznem",
                "Összeg SP-ben",
                "SP pénznem",
                "Átváltva HUF"
            ]
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(invoice_rows_sorted)
            QMessageBox.information(
                self,
                "Sikeres feldolgozás",
                f"Sikeres feldolgozás! {len(invoice_rows_sorted)} számla sor írva: output/vevok.csv"
            )
            self.show_results_table(invoice_rows_sorted, headers)
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt: {e}")

    def show_results_table(self, data, headers):
        self.results_window = ResultsTable(data, headers)
        self.results_window.show()