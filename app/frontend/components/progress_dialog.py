from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressDialog


def create_progress_dialog(title: str, parent=None) -> QProgressDialog:
    dialog = QProgressDialog("Előkészítés...", "Mégse", 0, 100, parent)
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    return dialog
