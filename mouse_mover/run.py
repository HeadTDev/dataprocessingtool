from PySide6.QtWidgets import QApplication
from .app.mouse_mover_ui import MouseMoverWindow

def main():
    """Entry point for the mouse mover application."""
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True

    w = MouseMoverWindow()
    w.show()

    if owns_app:
        app.exec()

    return w

if __name__ == "__main__":
    main()
