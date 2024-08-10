import threading
from functools import partial
from typing import List

from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .parse import parse_message
from slack_native.users.cache import get_cached_users, cache_profile_pictures
from slack_native.users.info import fetch_user_info, fetch_image


async def _normalize_messages(
    slack_client: WebClient, channel_messages: List[dict], channel_id: str
):
    """Normalize messages by fetching user info and profile pictures."""
    channel_messages = list(reversed(channel_messages))
    users_pending_cache = {}
    length = len(channel_messages)
    runner = QtAsyncRunner()
    for i, message in enumerate(channel_messages):
        tasks = []
        if "user" not in message:
            channel_messages.remove(message)
            continue

        message["text"] = parse_message(message["text"])
        message["channel"] = channel_id

        cached_users = get_cached_users()
        if not cached_users:
            cached_users = {}

        message["is_last"] = i == length - 1

        cached_user = cached_users.get(message["user"])
        if cached_user:
            message["user"] = cached_user

            continue
        elif message["user"] not in users_pending_cache:
            tasks.append(partial(fetch_user_info, slack_client, message["user"]))
        else:
            # As the condition above was not met, the user is accessible in `users_pending_cache`
            message["user"] = users_pending_cache[message["user"]]
            # if the file has already been downloaded, we can just use it
            if isinstance(message["user"]["profile"]["image_48"], bytes) or isinstance(
                message["user"]["profile"]["image_48"], str
            ):
                continue
            else:
                # small case where the file has not been downloaded yet
                while message["user"]["lock"].locked():
                    pass
                # the file has been downloaded, we can use it now

                continue

        resolutions: List[str] = ["48"]
        async for user in runner.run_parallel(tasks):
            user = await user
            message["user"] = user
            image_tasks: List[partial] = []

            for res in resolutions:
                image_tasks.append(
                    partial(fetch_image, user["profile"][f"image_{res}"])
                )

            images = []
            async for image in runner.run_parallel(image_tasks):
                images.append(await image)

            for res, image in zip(resolutions, images):
                message["user"]["profile"][f"image_{res}"] = image

            users_pending_cache[message["user"]] = message["user"]
            users_pending_cache[message["user"]]["lock"] = threading.Lock()

    # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
    if len(users_pending_cache) > 0:
        io_thread = threading.Thread(
            target=cache_profile_pictures, args=(users_pending_cache,)
        )
        io_thread.start()
    return channel_messages


async def fetch_messages(slack_client: WebClient, channel_id: str):
    try:
        response = slack_client.conversations_history(channel=channel_id, limit=10)
        channel_messages = response.get("messages")
        channel_messages = await _normalize_messages(
            slack_client, channel_messages, channel_id
        )

        return channel_messages
    except SlackApiError:
        return []


async def fetch_replies(slack_client: WebClient, channel_id: str, thread_ts: str):
    try:
        response = slack_client.conversations_replies(channel=channel_id, ts=thread_ts)
        channel_messages = response.get("messages")
        await _normalize_messages(slack_client, channel_messages, channel_id)
        return channel_messages
    except SlackApiError:
        return []
