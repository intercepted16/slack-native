from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget


class MessagesManager(QObject):
    # The signal contains the channel ID and a list of messages
    messages_updated = Signal(str, list)  # Signal carrying a list of messages
    messages_frame: tuple[QWidget, dict] | None = None
