from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from .process import Processor

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

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addLayout(self._row("KSH fájl (.xls):", self.ksh_input, ksh_btn))
        layout.addLayout(self._row("Matstamm (.xlsx):", self.mat_input, mat_btn))
        layout.addWidget(self.process_btn)

        self.processor = Processor()

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

        try:
            output_path = self.processor.process(ksh, mat)
            QMessageBox.information(
                self,
                "Kész",
                f"A feldolgozás elkészült.\nAz új fájl itt található:\n{output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{e}")