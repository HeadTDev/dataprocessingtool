import os
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class DragDropLineEdit(QLineEdit):
    def __init__(self, allowed_extensions=None, allow_folder=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.allow_folder = allow_folder
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if not urls:
                return super().dragEnterEvent(event)
            
            file_path = urls[0].toLocalFile()
            
            # Ellenőrizzük, hogy mappa-e, és megengedett-e
            if os.path.isdir(file_path):
                if self.allow_folder:
                    event.acceptProposedAction()
                else:
                    event.ignore()
                return

            # Ha fájl, ellenőrizzük a kiterjesztést
            if not self.allowed_extensions:
                # Nincs megkötés fájlokra (de mivel nem mappa, és azokat kezeltük, ide csak fájlok jutnak)
                event.acceptProposedAction()
                return

            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.allowed_extensions:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.setText(file_path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
