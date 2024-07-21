import json
import os

import PySide6
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QTextBrowser, \
    QLineEdit
from PySide6.QtGui import QTextCursor, QTextCharFormat, QTextImageFormat
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from typing import List, Optional
import parse
from functools import partial
from qt_async_threads import QtAsyncRunner


class TextBrowser(QTextBrowser):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.default_font_size = 14

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y() / 120  # Typically, one wheel step is 120 units
            self.change_font_size(delta)
        else:
            super().wheelEvent(event)  # Call the base class implementation for normal scrolling

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self.change_font_size(1)
            elif event.key() == Qt.Key.Key_Minus:
                self.change_font_size(-1)

    def change_font_size(self, delta):
        print(delta)
        self.default_font_size += delta
        self.default_font_size = max(1, self.default_font_size)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        text_format = QTextCharFormat()
        text_format.setFontPointSize(self.default_font_size)
        cursor.mergeCharFormat(text_format)
        self.mergeCurrentCharFormat(text_format)


class ShowWindowSignal(QObject):
    show_window = Signal()


def send_message_on_return(slack_client: WebClient, input_element: QLineEdit, channel: dict):
    text = input_element.text()
    input_element.clear()
    MessagesManager.send_message(slack_client, channel["id"], text)


class MessagesManager(QObject):
    messages_updated = Signal(dict, list)  # Signal carrying a list of messages
    messages_frame: QWidget = None
    channel_widgets: dict = {}
    selected_channel: str = None

    def __init__(self, slack_client: WebClient, runner: QtAsyncRunner):
        super().__init__()
        self.default_font_size = 14
        self.slack_client = slack_client
        self.runner = runner

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

                scroll_widget = TextBrowser()
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

        for channel_id, widget in channel_widgets.items():
            main_layout.addWidget(widget, 3)
            widget.setVisible(False)

        main_layout.addWidget(channels_list_widget, 1)  # Channels list takes less space

        self.messages_updated.connect(self.runner.to_sync(self.update_messages_ui))
        self.messages_frame = main_widget
        self.channel_widgets = channel_widgets

        if channels:
            self.show_channel(channels[0])

        return main_widget, channel_widgets

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
            for message in channel_messages:
                message["text"] = parse.render_message(message["text"])

            return channel_messages
        except SlackApiError as e:
            print(e.response['error'])
            return []

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

    @staticmethod
    async def fetch_user_info(slack_client, user_id) -> dict:
        user_info = slack_client.users_info(user=user_id)
        return user_info["user"]

    @staticmethod
    async def fetch_image(url):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()

    async def update_messages_ui(self, channel, channel_messages):
        channel_id = channel["id"]
        messages_widget = self.channel_widgets[channel_id]
        text_browser = messages_widget.findChild(QTextBrowser)
        layout = messages_widget.layout()

        # clear the text browser
        text_browser.clear()

        self.show_channel(channel)

        # Log the channel update
        print(f"Updating messages for channel {channel_id}")

        tasks = []

        # Add new messages to the specific channel's widget
        for message in channel_messages:
            if "user" not in message:
                print("No user found in message", message)
                continue

            user_id = message["user"]
            if user_id:
                cached_user = MessagesManager.get_cached_user(user_id)
                if cached_user:
                    print(f"User found in cache: {cached_user} (ID: {user_id})")
                    message["user"] = cached_user
                else:
                    tasks.append(lambda user_id=user_id: self.fetch_user_info(self.slack_client, user_id))

        users: [dict] = []
        async for user in self.runner.run_parallel(tasks):
            user = await user
            user_id = user["id"]
            MessagesManager.cache_user(user_id, user)
            users.append(user)

        for user in users:
            user_id = user["id"]
            message["user"] = user
            image_data = {key: value for key, value in user["profile"].items() if key.startswith('image_')}

            image_tasks = []

            for key, value in image_data.items():
                image_tasks.append(lambda value=value: self.fetch_image(value))

            images = []
            async for image in self.runner.run_parallel(image_tasks):
                images.append(await image)

            for key, image in zip(image_data.keys(), images):
                image_path = f"{os.environ.get('LOCALAPPDATA')}/slack_native/{user_id}_{key}.png"
                with open(image_path, "wb") as f:
                    f.write(image)

                user["profile"][key] = image_path
            MessagesManager.cache_user(user_id, user)

        for message in channel_messages:
            cursor = text_browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            img_format = QTextImageFormat()
            img_format.setName(message["user"]["profile"]["image_48"])  # Specify the path to your image
            img_format.setWidth(50)  # Set the desired width
            img_format.setHeight(50)  # Set the desired height
            cursor.insertImage(img_format)

            # Format the username
            user_format = QTextCharFormat()
            user_format.setFontWeight(QFont.Weight.Bold)
            user_format.setFontPointSize(20)
            cursor.insertText(f"{message['user']['real_name']}\n", user_format)

            # Format the message text
            text_format = QTextCharFormat()
            text_format.setFontPointSize(14)
            cursor.insertText(f"{message['text']}\n", text_format)

        if messages_widget not in [layout.itemAt(i).widget() for i in range(layout.count())]:
            layout.addWidget(messages_widget)

    @staticmethod
    def get_cached_user(user_id: str):
        data_dir = os.path.join(os.environ.get("LOCALAPPDATA"), "slack_native")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        users_cache = os.path.join(data_dir, "users.json")
        if not os.path.exists(users_cache):
            with open(users_cache, "w") as f:
                json.dump({}, f)
            return None
        with open(users_cache, "r") as f:
            users: dict[str, dict] = json.load(f)
            return users.get(user_id)

    @staticmethod
    def cache_user(user_id: str, user: dict):
        with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "r") as f:
            users: dict[str, dict] = json.load(f)
            users[user_id] = user
            with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "w") as f:
                json.dump(users, f)

    @staticmethod
    def send_message(slack_client: WebClient, channel_id: str, message: str):
        try:
            response = slack_client.chat_postMessage(channel=channel_id, text=message)
            print(response)
            return response
        except SlackApiError as e:
            print(e.response['error'])
            return None
