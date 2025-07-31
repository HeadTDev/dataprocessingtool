import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from .extract_data import extract_invoice_summary
from .coface_copy import fill_coface_excel_and_open  # <-- importáljuk a modult

class CofanetHelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cofanet Help")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "coface_icon.png")))

        self.sap_path_input = QLineEdit()
        self.sap_browse_btn = QPushButton("📂 Tallózás")
        self.sap_browse_btn.clicked.connect(self.browse_sap)

        self.coface_excel_input = QLineEdit()
        self.coface_browse_btn = QPushButton("📂 Tallózás")
        self.coface_browse_btn.clicked.connect(self.browse_coface_excel)

        self.eur_rate_input = QLineEdit()
        self.eur_rate_input.setPlaceholderText("Pl. 400")

        self.process_btn = QPushButton("⚙️ Feldolgozás és Excel kitöltés")
        self.process_btn.setFixedSize(300, 40)
        self.process_btn.clicked.connect(self.process_file)

        layout = QVBoxLayout()
        layout.addLayout(self._create_row("SAP input fájl:", self.sap_path_input, self.sap_browse_btn))
        layout.addLayout(self._create_row("Coface excel:", self.coface_excel_input, self.coface_browse_btn))
        layout.addLayout(self._create_row("EUR árfolyam:", self.eur_rate_input, None))
        layout.addWidget(self.process_btn)

        self.setLayout(layout)
        self.setMinimumWidth(320)

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(input_widget)
        if button_widget:
            row.addWidget(button_widget)
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
            # Coface Excel kitöltése
            coface_output_path = fill_coface_excel_and_open(coface_excel_path, output_path)
            QMessageBox.information(
                self,
                "Sikeres feldolgozás",
                f"Sikeres feldolgozás! {len(summary_rows_sorted)} vevő sor írva: output/vevok.csv\n"
                f"Coface Excel kitöltve: {coface_output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt: {e}")