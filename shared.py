from PyQt6.QtCore import QObject, pyqtSignal

class MessagesManager(QObject):
    messages_updated = pyqtSignal(list)  # Signal carrying a list of messages
    messages_frame = None