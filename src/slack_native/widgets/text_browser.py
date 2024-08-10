from typing import Optional

import PySide6
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QTextBrowser


class TextBrowser(QTextBrowser):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.default_font_size = 14

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = (
                event.angleDelta().y() / 120
            )  # Typically, one wheel step is 120 units
            self.change_font_size(delta)
        else:
            super().wheelEvent(
                event
            )  # Call the base class implementation for normal scrolling

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self.change_font_size(1)
            elif event.key() == Qt.Key.Key_Minus:
                self.change_font_size(-1)

    def change_font_size(self, delta):
        self.default_font_size += delta
        self.default_font_size = max(1, self.default_font_size)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        text_format = QTextCharFormat()
        text_format.setFontPointSize(self.default_font_size)
        cursor.mergeCharFormat(text_format)
        self.mergeCurrentCharFormat(text_format)
