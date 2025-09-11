from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QApplication
)
from PySide6.QtGui import QKeySequence, QShortcut
import csv
import shutil
import os

class CSVViewer(QDialog):
    def __init__(self, csv_path):
        super().__init__()
        self.setWindowTitle("Feldolgozott adatok")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)

        QShortcut(QKeySequence.Copy, self.table, self.copy_selection)

        self.load_csv(csv_path)

        self.output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'output')
        )

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

    def copy_selection(self):
        selection = self.table.selectedIndexes()
        if not selection:
            return
        selection = sorted(selection, key=lambda x: (x.row(), x.column()))
        rows = {}
        for index in selection:
            row, col = index.row(), index.column()
            if row not in rows:
                rows[row] = {}
            rows[row][col] = self.table.item(row, col).text() if self.table.item(row, col) else ""
        copied_lines = []
        for row in sorted(rows):
            line = []
            row_dict = rows[row]
            for col in sorted(row_dict):
                line.append(row_dict[col])
            copied_lines.append("\t".join(line))
        QApplication.clipboard().setText("\n".join(copied_lines))

    def closeEvent(self, event):
        if os.path.exists(self.output_dir) and os.path.isdir(self.output_dir):
            try:
                shutil.rmtree(self.output_dir)
            except Exception as e:
                print(f"Nem sikerült törölni az output mappát: {e}")
        event.accept()