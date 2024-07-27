from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from messages.parse import parse_message


def fetch_messages(slack_client: WebClient, channel_id: str):
    try:
        response = slack_client.conversations_history(channel=channel_id, limit=10)
        channel_messages = response.get("messages")
        # The newest message should be at the bottom, so reverse the list
        channel_messages = list(reversed(channel_messages))
        # TODO: compile the messages into one before rendering
        for message in channel_messages:
            message["text"] = parse_message(message["text"])

        return channel_messages
    except SlackApiError as e:
        print(e.response['error'])
        return []
