from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QScrollArea


class MessagesManager(QObject):
    messages_updated = pyqtSignal(list)  # Signal carrying a list of messages
    messages_frame: tuple[QScrollArea, QVBoxLayout] | None = None
