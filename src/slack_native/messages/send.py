import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def send_message(slack_client: WebClient, channel_id: str, message: str):
    if os.environ.get("DEV"):
        Exception("Cannot send messages in dev mode")
    try:
        response = slack_client.chat_postMessage(channel=channel_id, text=message)
        return response
    except SlackApiError:
        return None
