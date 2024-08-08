import threading
from functools import partial
from typing import List, Any

from qt_async_threads import QtAsyncRunner
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from messages.parse import parse_message
from ui.widgets.messages_browser import MessagesBrowser
from users.cache import get_cached_users, cache_profile_pictures
from users.info import fetch_user_info, fetch_image


async def apply_additional_properties(slack_client: WebClient, channel_messages: List[dict], channel_id: str):
    """Apply additional properties to messages, such as the user's profile picture, """
    users_pending_cache = {}
    length = len(channel_messages)
    runner = QtAsyncRunner()
    for i, message in enumerate(channel_messages):
        tasks = []
        if "user" not in message:
            print("No user found in message")
            channel_messages.remove(message)
            continue

        message["text"] = parse_message(message["text"])
        message["channel"] = channel_id

        # If it is a  *parent* message with replies (message is a thread), fetch the replies
        if "thread_ts" in message and message["thread_ts"] == message["ts"]:
            print("Fetching replies for message", message["ts"])
            replies = await runner.run(
                slack_client.conversations_replies,
                channel=message["channel"],
                ts=message["ts"]
            )
            # apply the one needed additional property here
            for reply in replies["messages"]:
                reply["channel"] = message["channel"]
            # apply additional properties to the replies
            if "messages" in replies and len(replies["messages"]) > 0:
                message["replies"] = await apply_additional_properties(slack_client, replies["messages"])

        # create a text browser for the message
        message_browser = MessagesBrowser(message["channel"], slack_client)
        message["text_browser"] = message_browser

        cached_users = get_cached_users()
        if not cached_users:
            cached_users = {}

        message["is_last"] = i == length - 1

        print("rendering and caching user", message["user"])
        cached_user = cached_users.get(message["user"])
        if cached_user:
            print(f"User found in cache: (ID: {message["user"]})")
            message["user"] = cached_user
            print("User ftched", message)
            # await Message.write(slack_client, text_browser.textCursor(), channel_messages)
            continue
        elif message["user"] not in users_pending_cache:
            print("user and client", message["user"], slack_client)
            tasks.append(partial(fetch_user_info, slack_client, message["user"]))
        else:
            # As the condition above was not met, the user is accessible in `users_pending_cache`
            print("User is already being processed", message["user"])
            message["user"] = users_pending_cache[message["user"]]
            # if the file has already been downloaded, we can just use it
            if isinstance(message["user"]["profile"]["image_48"], bytes) or isinstance(
                    message["user"]["profile"]["image_48"], str):
                # await Message.write(text_browser.textCursor(), channel_messages)
                continue
            else:
                # small case where the file has not been downloaded yet
                while message["user"]["lock"].locked():
                    pass
                # the file has been downloaded, we can use it now
                # await Message.write(text_browser.textCursor(), channel_messages)
                continue

        resolutions: list[str] = ["48"]
        async for user in runner.run_parallel(tasks):
            user = await user
            message["user"] = user

            for res in resolutions:
                image_tasks: list[partial | Any] = [partial(fetch_image, user["profile"][f"image_{res}"])]

            images = []
            async for image in runner.run_parallel(image_tasks):
                images.append(await image)

            for res, image in zip(resolutions, images):
                message["user"]["profile"][f"image_{res}"] = image

            users_pending_cache[message["user"]] = message["user"]
            users_pending_cache[message["user"]]["lock"] = threading.Lock()
        print("User ftched", message)

        # await Message.write(text_browser.textCursor(), channel_messages)

    # run this in a separate thread, because it's a blocking operation & is unnecessary to be awaited
    if len(users_pending_cache) > 0:
        io_thread = threading.Thread(target=cache_profile_pictures,
                                     args=(users_pending_cache,))
        io_thread.start()
    return channel_messages


async def fetch_messages(slack_client: WebClient, channel_id: str):
    try:
        response = slack_client.conversations_history(channel=channel_id, limit=10)
        channel_messages = response.get("messages")
        # The newest message should be at the bottom, so reverse the list
        channel_messages = list(reversed(channel_messages))
        # TODO: compile the messages into one before rendering
        for message in channel_messages:
            # only apply one additional property here; it's required in that func
            message["channel"] = channel_id
        channel_messages = await apply_additional_properties(slack_client, channel_messages, channel_id)

        return channel_messages
    except SlackApiError as e:
        print(e.response['error'])
        return []


async def fetch_replies(slack_client: WebClient, channel_id: str, thread_ts: str):
    try:
        response = slack_client.conversations_replies(channel=channel_id, ts=thread_ts)
        channel_messages = response.get("messages")
        # The newest message should be at the bottom, so reverse the list
        channel_messages = list(reversed(channel_messages))
        for message in channel_messages:
            # only apply one additional property here; it's required in that func
            message["channel"] = channel_id
        await apply_additional_properties(slack_client, channel_messages, channel_id)
    except SlackApiError as e:
        print(e.response['error'])
        return []
    return channel_messages
