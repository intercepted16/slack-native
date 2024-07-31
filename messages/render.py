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
    # Add new messages to the specific channel's widget
    users_pending_cache = {}
    length = len(channel_messages)
    for i, message in enumerate(channel_messages):
        tasks = []
        if "user" not in message:
            print("No user found in message")
            channel_messages.remove(message)
            continue

        user_id = message["user"]
        if not user_id:
            # TODO: implement handling for bot messages
            continue
        cached_users = get_cached_users()
        if not cached_users:
            cached_users = {}

        message["is_last"] = i == length - 1

        cached_user = cached_users.get(user_id)
        if cached_user:
            print(f"User found in cache: (ID: {user_id})")
            message["user"] = cached_user
            Message.write(text_browser.textCursor(), message)
            continue
        elif user_id not in users_pending_cache:
            print("user and client", user_id, slack_client)
            tasks.append(partial(fetch_user_info, slack_client, user_id))
        else:
            # As the condition above was not met, the user is accessible in `users_pending_cache`
            print("User is already being processed", user_id)
            message["user"] = users_pending_cache[user_id]
            # if the file has already been downloaded, we can just use it
            if isinstance(message["user"]["profile"]["image_48"], bytes) or isinstance(
                    message["user"]["profile"]["image_48"], str):
                Message.write(text_browser.textCursor(), message)
                continue
            else:
                # small case where the file has not been downloaded yet
                while message["user"]["lock"].locked():
                    pass
                # the file has been downloaded, we can use it now
                Message.write(text_browser.textCursor(), message)
                continue

        resolutions: list[str] = ["48"]
        async for user in runner.run_parallel(tasks):
            user = await user
            message["user"] = user

            for res in resolutions:
                image_tasks: list[partial | Any] = [partial(fetch_image, user["profile"][f"image_{res}"])]

            images = []
            runner = QtAsyncRunner()
            async for image in runner.run_parallel(image_tasks):
                images.append(await image)

            for res, image in zip(resolutions, images):
                message["user"]["profile"][f"image_{res}"] = image

            users_pending_cache[message["user"]["id"]] = message["user"]
            users_pending_cache[message["user"]["id"]]["lock"] = threading.Lock()
        Message.write(text_browser.textCursor(), message)

    # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
    if len(users_pending_cache) > 0:
        io_thread = threading.Thread(target=cache_profile_pictures,
                                     args=(users_pending_cache,))
        io_thread.start()
