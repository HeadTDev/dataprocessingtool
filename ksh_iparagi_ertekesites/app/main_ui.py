from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QProgressBar
)
import shutil
from pathlib import Path
from .process import Processor

class ProcessWorker(QObject):
    progress = Signal(int)
    finished = Signal(str, str)  # temp_output_path, error

    def __init__(self, processor: Processor, ksh_path: str, matstamm_path: str):
        super().__init__()
        self.processor = processor
        self.ksh_path = ksh_path
        self.matstamm_path = matstamm_path

    @Slot()
    def run(self):
        try:
            def progress_callback(percent):
                self.progress.emit(percent)
            # Ideiglenes output: a KSH fájl mappájába mentjük automatikusan
            temp_output = str(Path(self.ksh_path).with_suffix(".xlsx"))
            out_path = self.processor.process(self.ksh_path, self.matstamm_path, temp_output, progress_callback)
            self.finished.emit(out_path, "")
        except Exception as e:
            self.finished.emit("", str(e))

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KSH + Matstamm egyesítő")
        self.setMinimumWidth(320)

        self.ksh_input = QLineEdit()
        ksh_btn = QPushButton("📂 Tallózás")
        ksh_btn.clicked.connect(self.browse_ksh)

        self.mat_input = QLineEdit()
        mat_btn = QPushButton("📂 Tallózás")
        mat_btn.clicked.connect(self.browse_mat)

        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setFixedSize(300, 40)
        self.process_btn.clicked.connect(self.process_files)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addLayout(self._row("KSH fájl (.xls):", self.ksh_input, ksh_btn))
        layout.addLayout(self._row("Matstamm (.xlsx):", self.mat_input, mat_btn))
        layout.addWidget(self.process_btn)
        layout.addWidget(self.progress_bar)

        self.processor = Processor()
        self._thread = None
        self._worker = None

    def _row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text))
        row.addWidget(input_widget)
        row.addWidget(button_widget)
        return row

    def browse_ksh(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "KSH fájl kiválasztása",
            "",
            "Minden fájl (*.*)",
        )
        if path:
            self.ksh_input.setText(path)

    def browse_mat(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Matstamm fájl kiválasztása",
            "",
            "Excel munkafüzet (*.xlsx);;Minden fájl (*.*)",
        )
        if path:
            self.mat_input.setText(path)

    def process_files(self):
        ksh = self.ksh_input.text().strip()
        mat = self.mat_input.text().strip()

        if not ksh:
            QMessageBox.warning(self, "Hiányzó KSH", "Válaszd ki a KSH fájlt.")
            return
        if not mat:
            QMessageBox.warning(self, "Hiányzó Matstamm", "Válaszd ki a Matstamm fájlt.")
            return

        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._worker = ProcessWorker(self.processor, ksh, mat)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_process_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot(str, str)
    def _on_process_finished(self, temp_output_path, error):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        if error:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{error}")
        else:
            # Fájl mentési ablak felugrik, alapértelmezett név a temp_output_path
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Output fájl mentése",
                temp_output_path,
                "Excel munkafüzet (*.xlsx)"
            )
            if save_path:
                try:
                    shutil.copyfile(temp_output_path, save_path)
                    QMessageBox.information(
                        self,
                        "Kész",
                        f"Sikeres mentés!\nÚj fájl:\n{save_path}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Mentési hiba", f"Nem sikerült menteni:\n{e}")
            else:
                QMessageBox.information(
                    self,
                    "Mentés megszakítva",
                    "A mentés megszakítva, a fájl ideiglenesen itt található:\n" + temp_output_path
                )