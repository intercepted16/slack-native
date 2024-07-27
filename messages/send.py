from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def send_message(slack_client: WebClient, channel_id: str, message: str):
    try:
        response = slack_client.chat_postMessage(channel=channel_id, text=message)
        print(response)
        return response
    except SlackApiError as e:
        print(e.response['error'])
        return None
