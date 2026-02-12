import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from .extract_data import extract_invoice_summary
from .coface_copy import fill_coface_excel_and_open

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from theme import get_dark_theme_stylesheet, get_action_button_stylesheet, get_browse_button_stylesheet

class CofanetHelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cofanet Help")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "coface_icon.png")))
        self.setMinimumWidth(300)
        self.setMinimumHeight(280)

        self.sap_path_input = QLineEdit()
        self.sap_path_input.setPlaceholderText("SAP input fájl elérési útja...")
        self.sap_browse_btn = QPushButton("📂")
        self.sap_browse_btn.setMaximumWidth(45)
        self.sap_browse_btn.setToolTip("Tallózás a SAP fájlhoz")
        self.sap_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.sap_browse_btn.clicked.connect(self.browse_sap)

        self.coface_excel_input = QLineEdit()
        self.coface_excel_input.setPlaceholderText("Coface Excel fájl elérési útja...")
        self.coface_browse_btn = QPushButton("📂")
        self.coface_browse_btn.setMaximumWidth(45)
        self.coface_browse_btn.setToolTip("Tallózás a Coface Excel fájlhoz")
        self.coface_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.coface_browse_btn.clicked.connect(self.browse_coface_excel)

        self.eur_rate_input = QLineEdit()
        self.eur_rate_input.setPlaceholderText("Pl. 400")
        self.eur_rate_input.setToolTip("EUR/HUF árfolyam a konverzióhoz")

        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setMinimumHeight(36)
        self.process_btn.setStyleSheet(get_action_button_stylesheet())
        self.process_btn.setToolTip("SAP adatok feldolgozása és Coface Excel kitöltése")
        self.process_btn.clicked.connect(self.process_file)

        # Grouping
        input_group = QGroupBox("📁 Bemeneti fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(self._create_row("SAP input:", self.sap_path_input, self.sap_browse_btn))
        input_layout.addLayout(self._create_row("Coface Excel:", self.coface_excel_input, self.coface_browse_btn))
        input_group.setLayout(input_layout)

        config_group = QGroupBox("⚙️ Beállítások")
        config_layout = QVBoxLayout()
        eur_row = QHBoxLayout()
        eur_row.addWidget(QLabel("EUR árfolyam:"), 0)
        eur_row.addWidget(self.eur_rate_input, 1)
        config_layout.addLayout(eur_row)
        config_group.setLayout(config_layout)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(config_group)
        layout.addWidget(self.process_btn)

        self.setLayout(layout)
        self.setStyleSheet(get_dark_theme_stylesheet())

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_sap(self):
        path, _ = QFileDialog.getOpenFileName(self, "SAP input kiválasztása", "", "SAP Unicode Text export (*.xls *.txt *.csv)")
        if path:
            self.sap_path_input.setText(path)

    def browse_coface_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Coface Excel kiválasztása", "", "Excel fájlok (*.xlsx *.xls)")
        if path:
            self.coface_excel_input.setText(path)

    def process_file(self):
        sap_path = self.sap_path_input.text()
        coface_excel_path = self.coface_excel_input.text()
        eur_rate_str = self.eur_rate_input.text()

        if not sap_path:
            QMessageBox.warning(self, "Hiba", "Válassz SAP input fájlt!")
            return
        if not coface_excel_path:
            QMessageBox.warning(self, "Hiba", "Válassz Coface Excel fájlt!")
            return
        try:
            eur_rate = float(eur_rate_str.replace(',', '.').strip())
        except Exception:
            QMessageBox.warning(self, "Hiba", "Kérlek, érvényes EUR árfolyamot adj meg (pl. 400)!")
            return

        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            summary_rows = extract_invoice_summary(sap_path)
            summary_rows_sorted = sorted(summary_rows, key=lambda x: x["cegnev"].lower())
            output_path = os.path.join(output_dir, "vevok.csv")
            headers = [
                "Vevő",
                "Összeg BP-ben",
                "BP pénznem",
                "Összeg SP-ben",
                "SP pénznem",
                "Forintosítva HUF"
            ]
            import csv
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for row in summary_rows_sorted:
                    osszeg_bp = row.get("osszeg_bp", "").replace('.', '').replace(',', '.')
                    bp_penznem = row.get("bp_penznem", "").upper()
                    try:
                        osszeg_bp_float = float(osszeg_bp) if osszeg_bp else 0.0
                    except Exception:
                        osszeg_bp_float = 0.0
                    if bp_penznem != "HUF":
                        forintositva = osszeg_bp_float * eur_rate
                        forintositva_str = f'{forintositva:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        forintositva_str = row.get("osszeg_bp", "")
                    writer.writerow([
                        row.get("cegnev", ""),
                        row.get("osszeg_bp", ""),
                        row.get("bp_penznem", ""),
                        row.get("osszeg_sp", ""),
                        row.get("sp_penznem", ""),
                        forintositva_str
                    ])
            # Mentési hely kiválasztása
            save_path, _ = QFileDialog.getSaveFileName(self, "Mentés kitöltött Coface Excelként", "coface_output.xlsx", "Excel fájlok (*.xlsx)")
            if not save_path:
                QMessageBox.information(self, "Mentés megszakítva", "A kitöltött Excel mentése megszakítva lett.")
                return
            coface_output_path = fill_coface_excel_and_open(coface_excel_path, output_path, save_path=save_path)
            QMessageBox.information(
                self,
                "Sikeres feldolgozás",
                f"Sikeres feldolgozás! {len(summary_rows_sorted)} vevő sor írva: output/vevok.csv\n"
                f"Coface Excel kitöltve: {coface_output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt: {e}")