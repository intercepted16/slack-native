from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QTextBrowser, \
    QLineEdit
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from typing import List
import parse
from functools import partial


class ShowWindowSignal(QObject):
    show_window = Signal()


def send_message_on_return(slack_client: WebClient, input_element: QLineEdit, channel: dict):
    text = input_element.text()
    input_element.clear()
    MessagesManager.send_message(slack_client, channel["id"], text)


class MessagesManager(QObject):
    messages_updated = Signal(dict, list)  # Signal carrying a list of messages
    messages_frame: QWidget = None
    channel_widgets: dict = None
    selected_channel: str = None

    def __init__(self, slack_client: WebClient):
        super().__init__()
        self.slack_client = slack_client

    def create_page(self, channels: List[dict] = None):
        if channels is None:
            channels = []

        main_widget = QWidget()  # Main widget that holds everything
        main_layout = QHBoxLayout(main_widget)  # Main layout to arrange widgets horizontally

        # Dictionary to store scrollable widgets for each channel
        channel_widgets = {}

        # Channels list area
        channels_list_widget = QListWidget()
        if channels:
            for channel in channels:
                item = QListWidgetItem(channel["name"])
                item.setData(Qt.ItemDataRole.UserRole, channel)
                channels_list_widget.addItem(item)

                scroll_widget_container = QWidget()
                scroll_layout = QVBoxLayout(scroll_widget_container)

                scroll_widget = QTextBrowser()
                scroll_widget.setOpenExternalLinks(True)
                print(scroll_widget)

                label = QLabel(f"Messages for {channel['name']}")
                label.setFont(QFont("Arial", 20))
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                scroll_layout.addWidget(label)
                scroll_layout.addWidget(scroll_widget)
                message_input = QLineEdit()

                message_input.returnPressed.connect(
                    partial(send_message_on_return, self.slack_client, message_input, channel))
                scroll_layout.addWidget(message_input)

                # Store the scrollable widget container in the dictionary
                channel_widgets[channel["id"]] = scroll_widget_container

        # Connect the itemPressed signal to a lambda that calls on_channel_selected and passes the
        # channel_messages_widgets
        channels_list_widget.itemPressed.connect(
            lambda selected_channel: self.on_channel_selected(selected_channel))

        # Add the first channel's messages widget to the layout, or handle the default case
        for channel_id, widget in channel_widgets.items():
            main_layout.addWidget(widget, 3)
            widget.setVisible(False)

        if channels:
            first_channel_id = channels[0]["id"]
            channel_widgets[first_channel_id].setVisible(True)

        main_layout.addWidget(channels_list_widget, 1)  # Channels list takes less space

        self.messages_updated.connect(self.update_messages_ui)
        self.messages_frame = main_widget
        self.channel_widgets = channel_widgets
        return main_widget, channel_widgets  # Return the main widget and the dictionary of message widgets

    def on_channel_selected(self, item: QListWidgetItem):
        channel = item.data(Qt.ItemDataRole.UserRole)
        print(f"Channel selected: {channel['name']}")

        if self.selected_channel == channel["id"]:
            print("Channel already selected")
            return

        self.show_channel(channel)

        channel_messages = MessagesManager.fetch_messages(self.slack_client, channel["id"])

        # Assuming messages_manager has a method to update the UI with new messages
        self.messages_updated.emit(channel, channel_messages)

    @staticmethod
    def fetch_messages(slack_client: WebClient, channel_id: str):
        try:
            response = slack_client.conversations_history(channel=channel_id, limit=10)
            channel_messages = response.get("messages")
            # TODO: compile the messages into one before rendering
            channel_messages = [parse.render_message(message["text"]) for message in channel_messages if
                                "text" in message]
            return channel_messages
        except SlackApiError as e:
            print(e.response['error'])
            return []

    def show_channel(self, channel: dict):
        messages_widgets = self.channel_widgets
        # Hide the previously selected channel's messages widget
        if self.selected_channel in messages_widgets:
            messages_widgets[self.selected_channel].setVisible(False)

        # Reassign the selected channel
        self.selected_channel = channel["id"]

        # Show the selected channel's messages widget
        if channel:
            messages_widgets[channel["id"]].setVisible(True)

    def update_messages_ui(self, channel, channel_messages):
        channel_id = channel["id"]
        messages_widget = self.channel_widgets[channel_id]
        layout = messages_widget.layout()

        self.show_channel(channel)

        # Add new messages to the specific channel's widget
        print(f"Updating messages for channel {channel_id}")
        self.channel_widgets[channel_id].setVisible(True)
        # Add new messages
        for message in channel_messages:
            print(messages_widget.findChild(QTextBrowser))
            messages_widget.findChild(QTextBrowser).append(f"\n<p>{message}</p>")
            layout.addWidget(messages_widget)

    @staticmethod
    def send_message(slack_client: WebClient, channel_id: str, message: str):
        try:
            response = slack_client.chat_postMessage(channel=channel_id, text=message)
            print(response)
            return response
        except SlackApiError as e:
            print(e.response['error'])
            return None
