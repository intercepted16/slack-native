import os
import threading
from functools import partial
from typing import List, Any

import requests
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QTextBrowser
from qt_async_threads import QtAsyncRunner
from slack_sdk.web import WebClient

from messages.render import render_message
from users.cache import get_cached_users, cache_profile_pictures
from users.info import fetch_user_info
from utils.hashing import calculate_md5
from ui.widgets.messages_page import MessagesPage


class ShowWindowSignal(QObject):
    show_window = Signal()


class MessagesUpdatedSignal(QObject):
    _file_write_lock = threading.Lock()
    messages_updated = Signal(MessagesPage, dict, list)  # Signal carrying a list of messages
    messages_frame: QWidget = None
    channel_widgets: dict = {}
    selected_channel: str = None

    def __init__(self, slack_client: WebClient, runner: QtAsyncRunner):
        super().__init__()
        self.default_font_size = 14
        self.slack_client = slack_client
        self.runner = runner
        self.messages_updated.connect(runner.to_sync(self.update_messages_ui))

    async def fetch_image(self, url):
        image = await self.runner.run(
            requests.get, url
        )
        image.raise_for_status()
        return image.content

    async def update_messages_ui(self, messages_page: MessagesPage, channel: dict, channel_messages: List[dict]):
        channel_id = channel["id"]
        channel_widgets = messages_page.channel_widgets
        print(f"Channel widgets: {channel_widgets}")
        messages_widget = channel_widgets[channel_id]
        text_browser = messages_widget.findChild(QTextBrowser)
        print(f"Text browser: {text_browser}")

        # clear the text browser
        text_browser.clear()

        messages_page.show_channel(channel)

        # Log the channel update
        print(f"Updating messages for channel {channel_id}")

        # Add new messages to the specific channel's widget
        users_pending_cache = {}
        length = len(channel_messages)
        for i, message in enumerate(channel_messages):
            tasks = []
            if "user" not in message:
                print("No user found in message")
                continue

            user_id = message["user"]
            if not user_id:
                # TODO: implement handling for bot messages
                continue
            cached_users = get_cached_users()
            if not cached_users:
                cached_users = {}

            message["is_last"] = i == length - 1

            was_cached = True

            cached_user = cached_users.get(user_id)
            if cached_user:
                print(f"User found in cache: (ID: {user_id})")
                message["user"] = cached_user
                render_message(message, text_browser)
                continue
            elif user_id not in users_pending_cache:
                print("user and client", user_id, self.slack_client)
                was_cached = False
                tasks.append(partial(fetch_user_info, self.slack_client, user_id))
            else:
                print("User is already being processed", user_id)
                file_name = calculate_md5(user_id.encode()) + "image_48.png"
                # BUG: message["user"] hasn't been updated to the user object yet, so it's a string (user id)
                message["user"]["profile"]["image_48"] = os.path.join(os.getenv("LOCALAPPDATA"), "slack_native",
                                                                      file_name)

                render_message(message, text_browser)
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
            render_message(message, text_browser)

        # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
        if len(users_pending_cache) > 0:
            io_thread = threading.Thread(target=cache_profile_pictures,
                                         args=(users_pending_cache, self._file_write_lock))
            io_thread.start()
