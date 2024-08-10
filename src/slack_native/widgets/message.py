from functools import partial

from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QScrollArea
from slack_native.messages.fetch import fetch_replies
from qt_async_threads import QtAsyncRunner
from slack_native.slack_client import slack_client
from slack_native.widgets import TextBrowser
from .thread_sidebar import ThreadSidebar
from slack_native.utils.image_processing import RoundedImage


async def show_replies(message: dict, parent: QWidget):
    if not parent.findChild(ThreadSidebar):
        replies_widget = ThreadSidebar(message["channel"], parent)
    else:
        replies_widget = parent.findChild(ThreadSidebar)
    replies = await fetch_replies(slack_client, message["channel"], message["ts"])
    replies_widget.thread_sidebar_updated.thread_sidebar_updated.emit(replies)


class Message:
    @staticmethod
    async def write(scroll_area: QScrollArea, message: dict):
        buttons = []
        message_widget = QWidget()
        message_layout = QVBoxLayout()
        message_widget.setLayout(message_layout)
        text_browser = TextBrowser()
        message_layout.addWidget(text_browser)
        # Create a text browser to render the message
        parent = scroll_area.widget().layout()
        parent.addWidget(message_widget)
        cur = text_browser.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        data_url = message["user"]["profile"]["image_48"]

        cur.insertImage(RoundedImage(data_url, 50))

        user_format = QTextCharFormat()
        user_format.setFontPointSize(20)
        user_format.setFontWeight(QFont.Weight.Bold)
        cur.insertText(f"\n{message['user']['profile']['real_name']}\n", user_format)

        text_format = "font-size: 18px;"
        cur.insertHtml(f"<p style=\"{text_format}\">{message['text']}</p>\n")

        # if the message is a parent message with replies (message is a thread), display a button to show the replies
        if "thread_ts" in message and float(message["thread_ts"]) == float(
            message["ts"]
        ):
            button = QPushButton("Show replies")
            button.size = 20
            button.setParent(message_widget)

            runner = QtAsyncRunner()
            parent_parent = scroll_area.parent().parent().parent()
            parent_parent.children().append(button)
            button.clicked.connect(
                partial(runner.to_sync(show_replies), message, parent_parent)
            )
            message_layout.addWidget(button)

            buttons.append(button)  # Keep a reference to prevent garbage collection
