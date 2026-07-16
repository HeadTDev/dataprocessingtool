from PySide6.QtWidgets import QMessageBox


def show_error(parent, title: str, message: str, details: str | None = None):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    if details:
        box.setDetailedText(details)
    box.exec()
