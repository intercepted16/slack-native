import io
import os
import threading
from functools import partial
from typing import Any, List

import requests
from PIL import Image
from PySide6.QtWidgets import QTextBrowser
from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient

from ui.widgets.message import Message
from users.cache import get_cached_users, cache_profile_pictures
from users.info import fetch_user_info


async def fetch_image(url: str):
    runner = QtAsyncRunner()
    if os.environ.get("DEV"):
        # In development mode, the image is not 48 x 48, so we need to resize it
        img = Image.open(url)
        new_img = img.resize((48, 48))
        bytes_io = io.BytesIO()
        new_img.save(bytes_io, format="PNG")
        return bytes_io.getvalue()

    image = await runner.run(
        requests.get, url
    )
    image.raise_for_status()
    return image.content


async def render_messages(slack_client: WebClient, text_browser: QTextBrowser, channel_messages: List[dict]) -> None:
    """Given a list of messages, a Slack API Client and a text browser, render messages in a
    text browser. This is different from the `write` method in the `Message` class, as it also fetches user
    information and profile pictures.
    """
    for message in channel_messages:
        await Message.write(slack_client, text_browser, message)
