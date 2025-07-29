import sys
import os
import csv

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from .extract_data import extract_invoice_data_from_unicode_text
BUTTON_SIZE = (300, 40)

class ResultsTable(QWidget):
    def __init__(self, data, headers):
        super().__init__()
        self.setWindowTitle("Feldolgozott vevő adatok")
        layout = QVBoxLayout()
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for row_idx, row in enumerate(data):
            for col_idx, item in enumerate(row):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        self.setLayout(layout)
        self.resize(700, 400)

class CofanetHelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cofanet Help")
        self.selected_file = None

        layout = QVBoxLayout()
        self.label = QLabel("Válaszd ki az SAP export (.xls, .txt, .csv) input fájlt!")
        layout.addWidget(self.label)

        self.browse_button = QPushButton("📂 Tallózás")
        self.browse_button.setFixedSize(*BUTTON_SIZE)
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        self.process_button = QPushButton("⚙️ Feldolgozás")
        self.process_button.setFixedSize(*BUTTON_SIZE)
        self.process_button.clicked.connect(self.process_file)
        layout.addWidget(self.process_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def browse_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilters(["SAP Unicode Text export (*.xls *.txt *.csv)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_file = selected_files[0]
                filename = os.path.basename(self.selected_file)
                self.label.setText(f"Kiválasztott fájl: {filename}")

    def process_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Hiba", "Először válassz ki egy input fájlt!")
            return

        # Az output mappa a projekt gyökérben van (az app mappával egy szinten)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            invoice_rows = extract_invoice_data_from_unicode_text(self.selected_file)
            invoice_rows_sorted = sorted(invoice_rows, key=lambda row: (row[0] or "").lower())
            output_path = os.path.join(output_dir, "vevok.csv")
            headers = ["Vevő", "Számla", "Összeg BP-ben", "BP pénznem", "Összeg SP-ben", "SP pénznem"]
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for row in invoice_rows_sorted:
                    writer.writerow(row)
            self.result_label.setText(
                f"Sikeres feldolgozás! {len(invoice_rows_sorted)} számla sor írva: output/vevok.csv"
            )
            self.show_results_table(invoice_rows_sorted, headers)
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt: {e}")

    def show_results_table(self, data, headers):
        self.results_window = ResultsTable(data, headers)
        self.results_window.show()