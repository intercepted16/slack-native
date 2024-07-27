import os
import threading
from functools import partial
from typing import List, Any

from messages.fetch import fetch_messages
from ui.widgets.text_browser import TextBrowser

import requests
from PySide6.QtCore import QObject, Signal
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QTextBrowser, \
    QLineEdit
from qt_async_threads import QtAsyncRunner
from slack_sdk.web import WebClient

from messages.render import render_message
from messages.send import send_message
from users.cache import get_cached_users, cache_profile_pictures
from utils.hashing import calculate_md5


class ShowWindowSignal(QObject):
    show_window = Signal()


def send_message_on_return(slack_client: WebClient, input_element: QLineEdit, channel: dict):
    text = input_element.text()
    input_element.clear()
    send_message(slack_client, channel["id"], text)


class MessagesUpdatedSignal(QObject):
    _file_write_lock = threading.Lock()
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

        channel_messages = fetch_messages(self.slack_client, channel["id"])

        # Assuming messages_manager has a method to update the UI with new messages
        self.messages_updated.emit(channel, channel_messages)

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

        # Add new messages to the specific channel's widget
        users_pending_cache = {}
        for message in channel_messages:
            tasks = []
            if "user" not in message:
                print("No user found in message")
                continue

            user_id = message["user"]
            cached_users = get_cached_users()
            if not cached_users:
                cached_users = {}

            message["is_last"] = message == channel_messages[-1]

            was_cached = True

            if user_id:
                cached_user = cached_users.get(user_id)
                if cached_user:
                    print(f"User found in cache: (ID: {user_id})")
                    message["user"] = cached_user
                    render_message(message, messages_widget, layout, text_browser)
                    continue
                elif user_id not in users_pending_cache:
                    print("user and client", user_id, self.slack_client)
                    was_cached = False
                    tasks.append(partial(self.fetch_user_info, self.slack_client, user_id))
                else:
                    print("User is already being processed", user_id)
                    file_name = calculate_md5(user_id.encode()) + "image_48.png"
                    # BUG: message["user"] hasn't been updated to the user object yet, so it's a string (user id)
                    message["user"]["profile"]["image_48"] = os.path.join(os.getenv("LOCALAPPDATA"), "slack_native",
                                                                          file_name)

                    render_message(message, messages_widget, layout, text_browser)
                    continue

            resolutions: list[str] = ["48"]
            async for user in self.runner.run_parallel(tasks):
                user = await user
                user_id = user["id"]
                message["user"] = user

                for res in resolutions:
                    image_tasks: list[partial | Any] = [partial(self.fetch_image, user["profile"][f"image_{res}"])]

                images = []
                async for image in self.runner.run_parallel(image_tasks):
                    images.append(await image)

                for res, image in zip(resolutions, images):
                    message["user"]["profile"][f"image_{res}"] = image

            if not was_cached:
                users_pending_cache[user_id] = message["user"]
            render_message(message, messages_widget, layout, text_browser)

        # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
        if len(users_pending_cache) > 0:
            io_thread = threading.Thread(target=cache_profile_pictures,
                                         args=(users_pending_cache, self._file_write_lock))
            io_thread.start()
