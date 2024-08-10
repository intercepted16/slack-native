from functools import partial

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea
from slack_native.messages.send import send_message
from slack_sdk.web import WebClient


def send_message_on_return(
    slack_client: WebClient, input_element: QLineEdit, channel: dict
):
    text = input_element.text()
    input_element.clear()
    send_message(slack_client, channel["id"], text)


class MessagesBrowser(QWidget):
    def __init__(self, channel: dict, slack_client: WebClient):
        super().__init__()
        self.slack_client = slack_client
        message_widget = QWidget()
        message_widget.setLayout(QVBoxLayout())
        messages_browser = QScrollArea()
        self.messages_browser = messages_browser
        messages_browser.setWidgetResizable(True)
        messages_browser.setWidget(message_widget)

        scroll_layout = QVBoxLayout(self)
        self.scroll_layout = scroll_layout
        scroll_layout.addWidget(messages_browser)

        message_input = QLineEdit()

        message_input.returnPressed.connect(
            partial(send_message_on_return, self.slack_client, message_input, channel)
        )
        scroll_layout.addWidget(message_input)
