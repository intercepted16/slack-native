from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor
from PySide6.QtWidgets import QPushButton, QTextBrowser
from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient

from messages.fetch import apply_additional_properties
from users.info import fetch_user_info
from utils.image_processing import RoundedImage


class Message:
    @staticmethod
    async def write(slack_client: WebClient, text_browser: QTextBrowser, message: dict):
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
            cur.insertHtml("<br>")
            button = QPushButton("Show replies")
            dont_garbage_collect = DontGarbageCollect()
            dont_garbage_collect.add(button)
            # self.buttons.append(button)  # Keep a reference to prevent garbage collection

            cursor_rect = text_browser.cursorRect()
            button.move(cursor_rect.bottomLeft())
            button.show()

        # if it's a message with replies (message is a thread), render the replies
        if "replies" in message:
            print("Replies in message")
            for reply in message["replies"]:
                cur.insertHtml("<br>")
                # apply additional properties to the reply
                await Message.write(slack_client, text_browser, reply)
        # if it's the last message, add less space
        if message["is_last"]:
            cur.insertHtml("<br>")
        else:
            cur.insertHtml("<br>" * 2)


class DontGarbageCollect:
    def add(self, *args, **kwargs):
        local_vars = locals()
        for arg in args:
            var_name = [name for name, value in local_vars.items() if value == arg]
            if var_name:
                self.__setattr__(var_name[0], arg)
        for key, value in kwargs.items():
            self.__setattr__(key, value)