from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget


class SideBar(QWidget):
    contentStack = None

    def __init__(self, buttons: List[tuple[QPushButton, QLabel | QWidget]]):
        super().__init__()
        self.layout = QVBoxLayout()
        self.buttons = buttons
        self.contentStack = QStackedWidget()

        for i, (button, page) in enumerate(self.buttons):
            self.contentStack.addWidget(page)
            self.layout.addWidget(button)
            button.clicked.connect(lambda _, index=i: self.contentStack.setCurrentIndex(index))

        self.layout.addStretch(1)
        self.setLayout(self.layout)
