import math
from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QWheelEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextBrowser, QPushButton

from messages.send import send_message
from ui.widgets.text_browser import TextBrowser
from slack_sdk.web import WebClient


def send_message_on_return(slack_client: WebClient, input_element: QLineEdit, channel: dict):
    text = input_element.text()
    input_element.clear()
    send_message(slack_client, channel["id"], text)


def wrapper(wheelEvent: callable, src: QTextBrowser):
    def wrapped(event: QWheelEvent, src: QTextBrowser):
        wheelEvent(event)
        # Reposition the absolute positioned elements that are children of the text browser
        for child in src.children():
            if isinstance(child, QPushButton):
                print("Child: ", child)
                # If the distance moved is going to go out of bounds, move the button to the edge of the text browser
                if child.y() - event.angleDelta().y() < 0:
                    child.move(child.x(), 0)
                    continue
                if child.y() - event.angleDelta().y() > src.height():
                    child.move(child.x(), src.height())
                    continue
                # Move the button the same distance as the text browser moved (but a bit slower)
                child.move(child.x(), int((child.y() - event.angleDelta().y()) / int(
                 event.angleDelta().y()) * math.fabs(event.angleDelta().y())))

    return partial(wrapped, src=src)


class MessagesBrowser(QWidget):
    def __init__(self, channel: dict, slack_client: WebClient):
        super().__init__()
        self.slack_client = slack_client
        self.text_browser = TextBrowser()
        self.text_browser.wheelEvent = wrapper(self.text_browser.wheelEvent, self.text_browser)

        scroll_layout = QVBoxLayout(self)

        text_browser = self.text_browser
        text_browser.setOpenExternalLinks(True)

        scroll_layout.addWidget(text_browser)
        message_input = QLineEdit()

        message_input.returnPressed.connect(
            partial(send_message_on_return, self.slack_client, message_input, channel))
        scroll_layout.addWidget(message_input)
