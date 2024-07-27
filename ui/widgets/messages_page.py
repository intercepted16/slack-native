from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QWidget, QHBoxLayout, QListWidget
from slack_sdk.web import WebClient

from messages.fetch import fetch_messages
from ui.widgets.messages_browser import MessagesBrowser


class MessagesPage(QWidget):
    channel_widgets: dict = {}

    def __init__(self, slack_client: WebClient, messages_updated_signal, channels: List[dict] = None):
        super().__init__()
        self.messages_updated_signal = messages_updated_signal
        self.slack_client = slack_client
        self.selected_channel = None
        if channels is None:
            channels = []

        main_layout = QHBoxLayout(self)

        # Dictionary to store scrollable widgets for each channel
        channel_widgets = {}

        # Channels list area
        channels_list_widget = QListWidget()
        if channels:
            for channel in channels:
                item = QListWidgetItem(channel["name"])
                item.setData(Qt.ItemDataRole.UserRole, channel)
                channels_list_widget.addItem(item)

                channel_widgets[channel["id"]] = MessagesBrowser(channel, self.slack_client)

        channels_list_widget.itemPressed.connect(
            lambda selected_channel: self.on_channel_selected(selected_channel, self.messages_updated_signal))

        for channel_id, widget in channel_widgets.items():
            main_layout.addWidget(widget, 3)
            widget.setVisible(False)

        main_layout.addWidget(channels_list_widget, 1)  # Channels list takes less space

        self.channel_widgets = channel_widgets

        if channels:
            self.show_channel(channels[0])

    def on_channel_selected(self, item: QListWidgetItem, messages_updated_signal):
        channel = item.data(Qt.ItemDataRole.UserRole)
        print(f"Channel selected: {channel['name']}")

        if self.selected_channel == channel["id"]:
            print("Channel already selected")
            return

        self.show_channel(channel)

        channel_messages = fetch_messages(self.slack_client, channel["id"])
        messages_updated_signal.messages_updated.emit(self, channel, channel_messages)

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
