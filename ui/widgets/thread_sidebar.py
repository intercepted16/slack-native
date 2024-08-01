from functools import partial
from typing import List

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from qt_async_threads import QtAsyncRunner

from ui.widgets.messages_browser import MessagesBrowser
from slack_client import slack_client


class ThreadSidebarUpdated(QObject):
    thread_sidebar_updated = Signal(List[dict])

    def __init__(self):
        super().__init__()


class ThreadSidebar(QWidget):

    def __init__(self, channel: dict, messages: List[dict] = None):
        super().__init__()
        self.text_browser = None
        self.slack_client = slack_client
        self.messages = messages
        self.channel = channel
        self.messages_browser = MessagesBrowser(channel, self.slack_client)
        self.thread_sidebar_updated = ThreadSidebarUpdated()
        runner = QtAsyncRunner()
        self.thread_sidebar_updated.thread_sidebar_updated.connect(partial(runner.to_sync(self.update_thread_sidebar_ui)))
        if messages is None:
            self.messages = []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Threads"))
        layout.addWidget(self.messages_browser)

    async def update_thread_sidebar_ui(self, messages: List[dict]):
        scroll_area: QScrollArea = self.messages_browser.messages_browser.layout().findChild(QScrollArea)
        scroll_area.children().clear()
        from messages.render import render_messages
        await render_messages(scroll_area, messages)

    async def init(self):
        from messages.render import render_messages
        print(self.messages_browser.layout().findChild(QScrollArea))
        await render_messages(self.messages_browser.messages_browser, self.messages)
