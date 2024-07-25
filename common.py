import base64
import io
import json
import os
import threading

import PySide6
import requests
from PySide6.QtCore import QObject, Signal, QByteArray
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QTextBrowser, \
    QLineEdit
from PySide6.QtGui import QTextCursor, QTextCharFormat, QTextImageFormat, QPixmap, QImage, QPainter, QBrush
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from typing import List, Optional, Any
import parse
from functools import partial
from qt_async_threads import QtAsyncRunner


class RoundedImage(QImage):
    def __init__(self, source_path: str, radius: int):
        super().__init__(source_path)
        self.source_path: str | None = None
        self.radius = radius
        self.image = super()
        image = self.image
        width, height = image.width(), image.height()

        # Create a mask image with rounded corners
        mask = QImage(width, height, QImage.Format.Format_Alpha8)
        mask.fill(Qt.GlobalColor.transparent)

        # Draw the rounded rectangle
        painter = QPainter(mask)
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.setPen(Qt.GlobalColor.transparent)
        painter.drawRoundedRect(0, 0, width, height, self.radius, self.radius)
        painter.end()

        # Apply the mask to the original image
        image.setAlphaChannel(mask)


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
    def cache_profile_pictures(user, resolutions: List[str], images: List[bytes]):
        print("CACHE PROFILE PICTURES", user, resolutions, images)
        for res, image in zip(resolutions, images):
            image_path = f"{os.environ.get('LOCALAPPDATA')}/slack_native/{user["id"]}_image_{res}.png"
            with open(image_path, "wb") as f:
                f.write(image)
            user["profile"][f"image_{res}"] = image_path
        # now cache the image path in the user's profile
        MessagesManager.cache_users({user["id"]: user})

    @staticmethod
    def fetch_messages(slack_client: WebClient, channel_id: str):
        try:
            response = slack_client.conversations_history(channel=channel_id, limit=10)
            channel_messages = response.get("messages")
            # The newest message should be at the bottom, so reverse the list
            channel_messages = list(reversed(channel_messages))
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

    async def fetch_image(self, url):
        image = await self.runner.run(
            requests.get, url
        )
        image.raise_for_status()
        return image.content

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
            cached_users = MessagesManager.get_cached_users()
            if not cached_users:
                cached_users = {}
            if user_id:
                cached_user = cached_users.get(user_id)
                if cached_user:
                    print(f"User found in cache: {cached_user} (ID: {user_id})")
                    message["user"] = cached_user
                else:
                    print("user and client", user_id, self.slack_client)
                    tasks.append(partial(self.fetch_user_info, self.slack_client, user_id))

            print("tasks", tasks)

            resolutions: list[str] = ["48"]
            print("norm tasks", tasks)
            async for user in self.runner.run_parallel(tasks):
                user = await user
                user_id = user["id"]
                message["user"] = user

                for res in resolutions:
                    image_tasks: list[partial | Any] = [partial(self.fetch_image, user["profile"][f"image_{res}"])]

                images = []
                async for image in self.runner.run_parallel(image_tasks):
                    print("image", image)
                    images.append(await image)

                # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
                io_thread = threading.Thread(target=MessagesManager.cache_profile_pictures,
                                             args=(user, resolutions, images))
                io_thread.start()

                print("user", user)
                # MessagesManager.cache_users(users)
                # set the images to their binary data
                for res, image in zip(resolutions, images):
                    message["user"]["profile"][f"image_{res}"] = image

                # after caching the users, update the messages
                # for message in channel_messages:
                #     message["user"] = users.get(message["user"])

        for message in channel_messages:
            print("Message", message)
            cursor = text_browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            if "user" in message and message["user"] is not None:
                if "profile" not in message["user"]:
                    print("No profile found in message", message)
                    continue
            else:
                # Handle the case where "user" is not in the message or is None
                print("User not found or user is None in message", message)
                continue

            # Convert the image data to a data URL
            data_url: str | None = None
            if isinstance(message["user"]["profile"]["image_48"], str):
                print("not bytes")
                data_url = message["user"]["profile"]["image_48"]
            else:
                data_url = f"data:image/png;base64,{base64.b64encode(message["user"]["profile"]["image_48"]).decode()}"

            cursor.insertImage(RoundedImage(data_url, 50))

            user_format = QTextCharFormat()
            user_format.setFontPointSize(20)
            user_format.setFontWeight(QFont.Weight.Bold)
            cursor.insertText(f"\n{message['user']['real_name']}\n", user_format)

            text_format = "font-size: 18px;"
            cursor.insertHtml(f"<p style=\"{text_format}\">{message['text']}</p>\n")
            # if it's the last message, add less space
            if message == channel_messages[-1]:
                cursor.insertHtml("<br>")
            else:
                cursor.insertHtml("<br>" * 2)

            if messages_widget not in [layout.itemAt(i).widget() for i in range(layout.count())]:
                layout.addWidget(messages_widget)

    @staticmethod
    def get_cached_users():
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
            print("GETTING USERS, users", users)
            return users

    @staticmethod
    def cache_users(users: dict[str, dict]):
        with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "r") as r:
            current_users: dict[str, dict] = json.load(r)
            new_users = current_users
            for user in users:
                new_users[user] = users[user]

            with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "w") as w:
                json.dump(new_users, w)

    @staticmethod
    def send_message(slack_client: WebClient, channel_id: str, message: str):
        try:
            response = slack_client.chat_postMessage(channel=channel_id, text=message)
            print(response)
            return response
        except SlackApiError as e:
            print(e.response['error'])
            return None
