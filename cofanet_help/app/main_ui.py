import os
import sys

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .processor import process_cofanet_files

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from background_worker import BackgroundWorker
from theme import (
    get_action_button_stylesheet,
    get_browse_button_stylesheet,
    get_dark_theme_stylesheet,
)
from utils import resource_path


class CofanetHelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cofanet Help")
        self.setWindowIcon(QIcon(resource_path("icons", "coface_icon.png")))
        self.setMinimumWidth(320)
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
        input_layout.addLayout(
            self._create_row("SAP input:", self.sap_path_input, self.sap_browse_btn)
        )
        input_layout.addLayout(
            self._create_row(
                "Coface Excel:", self.coface_excel_input, self.coface_browse_btn
            )
        )
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

        self._process_thread = None
        self._process_worker = None
        self._progress_dialog = None

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_sap(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "SAP input kiválasztása",
            "",
            "SAP Unicode Text export (*.xls *.txt *.csv)",
        )
        if path:
            self.sap_path_input.setText(path)

    def browse_coface_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Coface Excel kiválasztása", "", "Excel fájlok (*.xlsx *.xls)"
        )
        if path:
            self.coface_excel_input.setText(path)

    def process_file(self):
        sap_path = self.sap_path_input.text().strip()
        coface_excel_path = self.coface_excel_input.text().strip()
        eur_rate_str = self.eur_rate_input.text().strip()

        if not sap_path or not os.path.isfile(sap_path):
            QMessageBox.warning(self, "Hiba", "Válassz létező SAP input fájlt!")
            return
        if not coface_excel_path or not os.path.isfile(coface_excel_path):
            QMessageBox.warning(self, "Hiba", "Válassz létező Coface Excel fájlt!")
            return
        try:
            eur_rate = float(eur_rate_str.replace(",", "."))
        except Exception:
            QMessageBox.warning(
                self, "Hiba", "Kérlek, érvényes EUR árfolyamot adj meg (pl. 400)!"
            )
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Mentés kitöltött Coface Excelként",
            "coface_output.xlsx",
            "Excel fájlok (*.xlsx)",
        )
        if not save_path:
            QMessageBox.information(
                self,
                "Mentés megszakítva",
                "A kitöltött Excel mentése megszakítva lett.",
            )
            return

        self.process_btn.setEnabled(False)
        self._progress_dialog = QProgressDialog("Előkészítés...", "Mégse", 0, 100, self)
        self._progress_dialog.setWindowTitle("Cofanet feldolgozás")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)

        self._process_thread = QThread(self)
        self._process_worker = BackgroundWorker(
            process_cofanet_files,
            sap_path,
            coface_excel_path,
            eur_rate,
            save_path,
        )
        self._process_worker.moveToThread(self._process_thread)

        self._process_thread.started.connect(self._process_worker.run)
        self._process_worker.progress.connect(self._on_process_progress)
        self._process_worker.result.connect(self._on_process_result)
        self._process_worker.error.connect(self._on_process_error)
        self._process_worker.finished.connect(self._process_thread.quit)
        self._process_worker.finished.connect(self._process_worker.deleteLater)
        self._process_thread.finished.connect(self._process_thread.deleteLater)
        self._process_thread.finished.connect(self._on_process_finished)
        self._progress_dialog.canceled.connect(self._process_worker.request_cancel)

        self._process_thread.start()

    def _on_process_progress(self, message, current, total):
        if self._progress_dialog is None:
            return
        if total > 0:
            self._progress_dialog.setRange(0, total)
            self._progress_dialog.setValue(current)
        else:
            self._progress_dialog.setRange(0, 0)
        self._progress_dialog.setLabelText(message)

    def _on_process_result(self, result):
        self._close_progress_dialog()
        if result.get("cancelled"):
            QMessageBox.information(self, "Megszakítva", "A feldolgozás megszakítva.")
            return

        coface_output_path = result.get("coface_output_path")
        rows_count = result.get("rows_count", 0)
        QMessageBox.information(
            self,
            "Sikeres feldolgozás",
            f"Sikeres feldolgozás! {rows_count} vevő sor írva: output/vevok.csv\n"
            f"Coface Excel kitöltve: {coface_output_path}",
        )
        if coface_output_path:
            self._open_output_file(coface_output_path)

    def _on_process_error(self, error_message):
        self._close_progress_dialog()
        QMessageBox.critical(self, "Hiba", f"Hiba történt: {error_message}")

    def _on_process_finished(self):
        self.process_btn.setEnabled(True)
        self._process_thread = None
        self._process_worker = None
        self._close_progress_dialog()

    def _close_progress_dialog(self):
        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog.deleteLater()
            self._progress_dialog = None

    def _open_output_file(self, output_path):
        try:
            if sys.platform.startswith("darwin"):
                os.system(f'open "{output_path}"')
            elif os.name == "nt":
                os.startfile(output_path)
            else:
                os.system(f'xdg-open "{output_path}"')
        except Exception:
            pass

    def closeEvent(self, event):
        if self._process_worker is not None:
            self._process_worker.request_cancel()
        event.accept()
