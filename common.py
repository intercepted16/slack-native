from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QTextBrowser
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from typing import List
import keyring

import parse

slack_token = keyring.get_password("slack_native", "access_token")
slack_client = WebClient(slack_token)


class MessagesManager(QObject):
    # The signal contains the channel ID and a list of messages
    messages_updated = Signal(dict, list)  # Signal carrying a list of messages
    messages_frame: tuple[QWidget, dict] | None = None
    selected_channel: str | None = None

    def __init__(self):
        super().__init__()

    def create_messages_page(self, channels: List[dict] | None = None, ):
        print("running")
        if not channels:
            try:
                response = slack_client.users_conversations()
                channels = response.get("channels")
                channels.sort(key=lambda x: x["name"])
                print(channels)
            except SlackApiError as e:
                print(e.response['error'])
                channels = []

        main_widget = QWidget()  # Main widget that holds everything
        main_layout = QHBoxLayout(main_widget)  # Main layout to arrange widgets horizontally

        # Dictionary to store scrollable widgets for each channel
        channel_messages_widgets = {}

        # Channels list area
        channels_list_widget = QListWidget()
        if channels:
            for channel in channels:
                print("e", channel["name"])
                item = QListWidgetItem(channel["name"])
                item.setData(Qt.ItemDataRole.UserRole, channel)
                channels_list_widget.addItem(item)

                # Create a text browser widget to display messages for each channel
                scroll_widget = QTextBrowser()
                scroll_widget.setOpenExternalLinks(True)
                scroll_widget.setVisible(False)  # Initially hidden

                messages_layout = QVBoxLayout(scroll_widget)
                label = QLabel(f"Messages for {channel['name']}")
                label.setFont(QFont("Arial", 20))
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                messages_layout.addWidget(label)
                # scroll_widget.setLayout(messages_layout)

                # Store the scrollable widget in the dictionary
                channel_messages_widgets[channel["id"]] = scroll_widget

        # Connect the itemPressed signal to a lambda that calls on_channel_selected and passes the
        # channel_messages_widgets
        channels_list_widget.itemPressed.connect(
            lambda item: self.on_channel_selected(item))

        # Add the first channel's messages widget to the layout, or handle the default case
        for channel_id, widget in channel_messages_widgets.items():
            main_layout.addWidget(widget, 3)
            widget.setVisible(False)

        if channels:
            first_channel_id = channels[0]["id"]
            channel_messages_widgets[first_channel_id].setVisible(True)

        main_layout.addWidget(channels_list_widget, 1)  # Channels list takes less space

        print(main_widget, channel_messages_widgets)
        self.messages_updated.connect(self.update_messages_ui)
        self.messages_frame = main_widget, channel_messages_widgets
        return main_widget, channel_messages_widgets  # Return the main widget and the dictionary of message widgets

    def on_channel_selected(self, item: QListWidgetItem):
        channel = item.data(Qt.ItemDataRole.UserRole)
        print(f"Channel selected: {channel['name']}")

        if self.selected_channel == channel["id"]:
            print("Channel already selected")
            return

        self.show_channel(channel)

        channel_messages = self.fetch_messages(channel["id"])

        # Assuming messages_manager has a method to update the UI with new messages
        self.messages_updated.emit(channel, channel_messages)

    @staticmethod
    def fetch_messages(channel_id: str):
        try:
            response = slack_client.conversations_history(channel=channel_id, limit=10)
            channel_messages = response.get("messages")
            # compile the messages into one before rendering
            for message in channel_messages:
                print(type(message["text"]))
            channel_messages = [parse.render_message(message["text"]) for message in channel_messages if
                                "text" in message]
            return channel_messages
        except SlackApiError as e:
            print(e.response['error'])
            return []

    def show_channel(self, channel: dict):
        messages_widgets = self.messages_frame[1]
        # Hide the previously selected channel's messages widget
        if self.selected_channel in messages_widgets:
            messages_widgets[self.selected_channel].setVisible(False)

        # Reassign the selected channel
        self.selected_channel = channel["id"]

        # Show the selected channel's messages widget
        if channel:
            messages_widgets[channel["id"]].setVisible(True)

    def update_messages_ui(self, channel):
        print("Updating messages UI")
        channel_id = channel["id"]
        # Access the specific channel's messages widget based on channel_id
        messages_widget = self.messages_frame[1][channel_id]
        layout = messages_widget.layout()

        # Hide the currently visible channel's messages widget
        self.messages_frame[1][self.selected_channel].setVisible(False)

        self.show_channel(channel)

        # Clear existing messages in the channel's widget before adding new ones
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new messages to the specific channel's widget
        print(f"Updating messages for channel {channel_id}")
        self.messages_frame[1][channel_id].setVisible(True)
        channel_messages = self.fetch_messages(channel_id)
        # Add new messages
        for message in channel_messages:
            messages_widget.append(f"\n<p>{message}</p>")
            layout.addWidget(messages_widget)
