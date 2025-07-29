from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
import csv

class CSVViewer(QDialog):
    def __init__(self, csv_path):
        super().__init__()
        self.setWindowTitle("Feldolgozott adatok")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.load_csv(csv_path)

    def load_csv(self, csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)

            if not data:
                return

            self.table.setRowCount(len(data) - 1)
            self.table.setColumnCount(len(data[0]))
            self.table.setHorizontalHeaderLabels(data[0])

            for row_idx, row in enumerate(data[1:]):
                for col_idx, cell in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(cell))

            self.table.resizeColumnsToContents()