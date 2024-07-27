from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit

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

        scroll_layout = QVBoxLayout(self)

        scroll_widget = TextBrowser()
        scroll_widget.setOpenExternalLinks(True)

        label = QLabel(f"Messages for {channel['name']}")
        label.setFont(QFont("Arial", 20))
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        scroll_layout.addWidget(label)
        scroll_layout.addWidget(scroll_widget)
        message_input = QLineEdit()

        message_input.returnPressed.connect(
            partial(send_message_on_return, self.slack_client, message_input, channel))
        scroll_layout.addWidget(message_input)
