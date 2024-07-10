from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class MessagesManager(QObject):
    # The signal contains the channel ID and a list of messages
    messages_updated = pyqtSignal(str, list)  # Signal carrying a list of messages
    messages_frame: tuple[QWidget, dict] | None = None
