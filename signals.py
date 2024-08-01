import io
import os
import threading
from functools import partial
from typing import List, Any

import requests
from PIL import Image

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QTextBrowser
from qt_async_threads import QtAsyncRunner
from slack_sdk.web import WebClient

from messages.render import render_messages
from ui.widgets.message import Message
from users.cache import get_cached_users, cache_profile_pictures
from users.info import fetch_user_info
from ui.widgets.messages_page import MessagesPage


class ShowWindowSignal(QObject):
    show_window = Signal()


class MessagesUpdatedSignal(QObject):
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

    async def fetch_image(self, url: str):
        if os.environ.get("DEV"):
            # In development mode, the image is not 48 x 48, so we need to resize it
            img = Image.open(url)
            new_img = img.resize((48, 48))
            bytes_io = io.BytesIO()
            new_img.save(bytes_io, format="PNG")
            return bytes_io.getvalue()

        image = await self.runner.run(
            requests.get, url
        )
        image.raise_for_status()
        return image.content

    async def update_messages_ui(self, messages_page: MessagesPage, channel: dict, channel_messages: List[dict]):
        channel_id = channel["id"]
        channel_widgets = messages_page.channel_widgets
        print(f"Channel widgets: {channel_widgets}")
        message_widgets = channel_widgets[channel_id]
        text_browser = message_widgets.findChild(QTextBrowser)
        print(f"Text browser: {text_browser}")

        # clear the text browser
        text_browser.clear()

        # Log the channel update
        print(f"Updating messages for channel {channel_id}")
        print(channel_messages)

        await render_messages(self.slack_client, text_browser, channel_messages)