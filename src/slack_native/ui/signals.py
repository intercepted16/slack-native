from typing import List

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QScrollArea
from qt_async_threads import QtAsyncRunner
from slack_sdk.web import WebClient

from slack_native.messages.render import render_messages
from slack_native.widgets import MessagesPage


class ShowWindowSignal(QObject):
    show_window = Signal()


class MessagesUpdatedSignal(QObject):
    messages_updated = Signal(
        MessagesPage, dict, list
    )  # Signal carrying a list of messages
    messages_frame: QWidget = None
    channel_widgets: dict = {}
    selected_channel: str = None

    def __init__(self, slack_client: WebClient, runner: QtAsyncRunner):
        super().__init__()
        self.default_font_size = 14
        self.slack_client = slack_client
        self.runner = runner
        self.messages_updated.connect(runner.to_sync(self.update_messages_ui))

    @staticmethod
    async def update_messages_ui(
        messages_page: MessagesPage, channel: dict, channel_messages: List[dict]
    ):
        channel_id = channel["id"]
        channel_widgets = messages_page.channel_widgets
        message_widget: QWidget = channel_widgets[channel_id]
        message_scroll_area = message_widget.findChild(QScrollArea)
        if not isinstance(message_scroll_area, QScrollArea):
            return
        # Log the channel update

        await render_messages(message_scroll_area, channel_messages)
