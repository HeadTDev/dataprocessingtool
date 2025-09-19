import sys
import subprocess
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import QTimer

BUTTON_SIZE = (300, 40)

# --- AUTO-UPDATE INTEGRÁCIÓ (PySide6) ---
def start_auto_update():
    try:
        from auto_updater import perform_update_flow
    except ImportError:
        return

    # UI callback-ek (main thread-ben fognak futni, mert a QMessageBox hívást
    # a frissítő thread közvetlenül meghívhatja – Qt általában tolerálja, de
    # legbiztosabb lenne signal-slot; itt egyszerűsítünk)
    def ui_prompt(question: str) -> bool:
        return QMessageBox.question(
            None,
            "Frissítés elérhető",
            question,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes

    def ui_info(msg: str):
        QMessageBox.information(None, "Frissítés", msg)

    def ui_error(msg: str):
        QMessageBox.critical(None, "Frissítés hiba", msg)

    # Háttérszálon futtatjuk a hálózati munkát, hogy ne blokkolja a GUI-t
    perform_update_flow(
        incremental_preferred=True,
        ui_prompt=ui_prompt,
        ui_info=ui_info,
        ui_error=ui_error,
        run_in_thread=True,
        delay_seconds=1.5  # kis késleltetés, hogy a főablak meg tudjon jelenni
    )

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon("synthwave_icon.png"))
        self.setMinimumSize(320, 160)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))

        buttons = [
            ("💸 Merkantil PDF Feldolgozó", "merkantil_pdf_feldolgozo/run.py"),
            ("📂 Vonalkód PDF Másolás", "barcode_pdf_masolas/run.py"),
            ("📚 Cofanet Help", "cofanet_help/run.py"),
            ("🔧 KSH Iparági Értékesítés", "ksh_iparagi_ertekesites/run.py"),
        ]

        for text, path in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.clicked.connect(lambda _, p=path: subprocess.Popen([sys.executable, p]))
            layout.addWidget(btn)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainMenu()
    window.show()
    
    QTimer.singleShot(500, start_auto_update)

    sys.exit(app.exec())