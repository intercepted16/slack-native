import math
from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QWheelEvent, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextBrowser, QPushButton, QScrollArea

from messages.send import send_message
from ui.widgets.text_browser import TextBrowser
from slack_sdk.web import WebClient


def send_message_on_return(slack_client: WebClient, input_element: QLineEdit, channel: dict):
    text = input_element.text()
    input_element.clear()
    send_message(slack_client, channel["id"], text)


class MessagesBrowser(QWidget):
    def __init__(self, channel: dict, slack_client: WebClient):
        super().__init__()
        self.slack_client = slack_client
        self.scroll_area = QScrollArea()
        # self.text_browser = TextBrowser()

        scroll_layout = QVBoxLayout(self)
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Mid)
        scroll_layout.addWidget(self.scroll_area)

        # text_browser = self.text_browser
        # text_browser.setOpenExternalLinks(True)

        # scroll_layout.addWidget(text_browser)
        message_input = QLineEdit()

        message_input.returnPressed.connect(
            partial(send_message_on_return, self.slack_client, message_input, channel))
        scroll_layout.addWidget(message_input)
