from PySide6.QtWidgets import QHBoxLayout, QLabel


def create_file_picker_row(label_text, input_widget, button_widget):
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addWidget(QLabel(label_text), 0)
    row.addWidget(input_widget, 1)
    row.addWidget(button_widget, 0)
    return row
