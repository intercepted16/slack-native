from typing import List

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from qt_async_threads import QtAsyncRunner

from .messages_browser import MessagesBrowser
from slack_native.slack_client import slack_client


class ThreadSidebarUpdated(QObject):
    thread_sidebar_updated = Signal(list)

    def __init__(self):
        super().__init__()


class ThreadSidebar(QWidget):
    def __init__(self, channel: dict, parent: QWidget):
        super().__init__()
        self.setParent(parent)
        self.show()
        self.text_browser = None
        self.slack_client = slack_client
        self.channel = channel
        self.messages_browser = MessagesBrowser(channel, self.slack_client)
        self.messages_browser.setParent(self)
        self.thread_sidebar_updated = ThreadSidebarUpdated()
        runner = QtAsyncRunner()

        self.thread_sidebar_updated.thread_sidebar_updated.connect(
            lambda messages: runner.to_sync(self.update_thread_sidebar_ui)(messages)
        )
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Threads"))
        layout.addWidget(self.messages_browser)

    async def update_thread_sidebar_ui(self, messages: List[dict]):
        scroll_area: QScrollArea = self.messages_browser.messages_browser
        scroll_area.children().clear()
        from slack_native.messages.render import render_messages

        await render_messages(scroll_area, messages)
