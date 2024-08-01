from functools import partial
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel
from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient

from messages.fetch import fetch_messages
from ui.widgets.messages_browser import MessagesBrowser


class ChannelsList:
    def __init__(self, slack_client: WebClient, channels: List[dict], messages_updated_signal, messages_page):
        self.channel_widgets = {}
        self.selected_channel = None
        self.channels = channels
        self.slack_client = slack_client
        self.channels_list_widget = QListWidget()
        self.messages_updated_signal = messages_updated_signal
        self.messages_page = messages_page
        # Dictionary to store scrollable widgets for each channel
        channel_widgets = self.channel_widgets

        # Channels list area
        channels_list_widget = self.channels_list_widget
        if channels:
            for channel in channels:
                item = QListWidgetItem(channel["name"])
                item.setData(Qt.ItemDataRole.UserRole, channel)
                channels_list_widget.addItem(item)

                widget = QWidget()
                layout = QVBoxLayout(widget)
                label = QLabel(f"Messages for {channel['name']}")
                label.setFont(QFont("Arial", 20))
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(label)

                messages_browser = MessagesBrowser(channel, self.slack_client)
                layout.addWidget(messages_browser)

                channel_widgets[channel["id"]] = widget

        runner = QtAsyncRunner()
        channels_list_widget.itemPressed.connect(
            lambda item: runner.to_sync(self.on_channel_selected)(item))
        for channel_id, widget in channel_widgets.items():
            widget.setVisible(False)

    async def on_channel_selected(self, item: QListWidgetItem):
        channel = item.data(Qt.ItemDataRole.UserRole)
        print(f"Channel selected: {channel['name']}")

        if self.selected_channel == channel["id"]:
            print("Channel already selected")
            return

        self.show_channel(channel)

        channel_messages = await fetch_messages(self.slack_client, channel["id"])
        print(f"Channel messages: {channel_messages}")
        self.messages_updated_signal.messages_updated.emit(self.messages_page, channel, channel_messages)

    def show_channel(self, channel: dict):
        channel_widgets = self.channel_widgets
        print("channel_widgets", channel_widgets)
        # Hide the previously selected channel's messages widget
        if channel_widgets:
            if self.selected_channel in channel_widgets:
                channel_widgets[self.selected_channel].setVisible(False)

        # Reassign the selected channel
        self.selected_channel = channel["id"]

        # Show the selected channel's messages widget
        if channel:
            channel_widgets[channel["id"]].setVisible(True)
