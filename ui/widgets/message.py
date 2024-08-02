from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor
from PySide6.QtWidgets import QPushButton, QTextBrowser, QLabel, QScrollArea, QLayout, QWidget, QVBoxLayout
from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient

from messages.fetch import apply_additional_properties
from ui.widgets.text_browser import TextBrowser
from users.info import fetch_user_info
from utils.image_processing import RoundedImage


class Message:
    @staticmethod
    async def write(parent: QLayout, message: dict):
        buttons = []
        message_widget = QWidget()
        message_layout = QVBoxLayout()
        message_widget.setLayout(message_layout)
        text_browser = TextBrowser()
        message_layout.addWidget(text_browser)
        # Create a text browser to render the message
        parent.addWidget(message_widget)
        cur = text_browser.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        data_url = message["user"]["profile"]["image_48"]

        print("also person being rendered is", message["user"]["profile"]["real_name"])
        print("thread_ts" in message, message["ts"], message["thread_ts"] if "thread_ts" in message else None)

        cur.insertImage(RoundedImage(data_url, 50))

        user_format = QTextCharFormat()
        user_format.setFontPointSize(20)
        user_format.setFontWeight(QFont.Weight.Bold)
        cur.insertText(f"\n{message['user']['profile']['real_name']}\n", user_format)

        text_format = "font-size: 18px;"
        cur.insertHtml(f"<p style=\"{text_format}\">{message['text']}</p>\n")
        if "thread_ts" in message:
            print(message["thread_ts"], message["ts"])
            print(float(message["thread_ts"]) == float(message["ts"]))

        # if the message is a parent message with replies (message is a thread), display a button to show the replies
        if "thread_ts" in message and float(message["thread_ts"]) == float(message["ts"]):
            print("Parent message with replies")
            button = QPushButton("Show replies")
            button.size = 20
            button.setParent(message_widget)
            message_layout.addWidget(button)

            buttons.append(button)  # Keep a reference to prevent garbage collection

        if message["is_last"]:
            cur.insertHtml("<br>")
        else:
            cur.insertHtml("<br>" * 2)
