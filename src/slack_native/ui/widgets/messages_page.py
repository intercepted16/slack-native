from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter
from PySide6.QtWidgets import QWidget, QHBoxLayout
from slack_sdk.web import WebClient

from ui.widgets.channels import ChannelsList


class MessagesPage(QWidget):
    channel_widgets: dict = {}

    def __init__(self, slack_client: WebClient, messages_updated_signal, channels: List[dict] = None):
        super().__init__()
        self.messages_updated_signal = messages_updated_signal
        self.slack_client = slack_client
        self.selected_channel = None
        self.channels = channels

    async def init(self):
        channels = self.channels
        if channels is None:
            channels = []

        main_layout = QHBoxLayout(self)

        # create a QSplitter to allow resizing of the channel list and the messages
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        channels = ChannelsList(self.slack_client, channels, self.messages_updated_signal, self)

        for widget in channels.channel_widgets.values():
            splitter.addWidget(widget)
            widget.setVisible(False)

        channel_widgets = channels.channel_widgets

        splitter.addWidget(channels.channels_list_widget)

        self.channel_widgets = channel_widgets

        if channels:
            channels.show_channel(channels.channels[0])
        # add thread sidebar
        # for now add test data here
        # thread_sidebar = ThreadSidebar(
        #     self.slack_client,
        #     channels.channels[0],
        #     await fetch_messages(self.slack_client, channels.channels[0]["id"]))
        # await thread_sidebar.init()
        # splitter.addWidget(thread_sidebar)
