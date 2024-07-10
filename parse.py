import re
import keyring
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json

# Slack formatting patterns
bold_pattern = re.compile(r'\*(.*?)\*')
italic_pattern = re.compile(r'_(.*?)_')
strikethrough_pattern = re.compile(r'~(.*?)~')
link_pattern = re.compile(r'<(https?://\S+)(\|.*?)?>')
channel_pattern = re.compile(r'#(\w+)')
emoji_pattern = re.compile(r':(\w+):')



def render_message(text):
    if not load_cached_emojis():
        try:
            # fetch the emojis
            slack_client = WebClient(token=keyring.get_password("slack_native", "access_token"))
            response = slack_client.emoji_list(include_categories=False)
            emoji_dict = response.get("emoji")
            cache_emojis(emoji_dict)
        except SlackApiError as e:
            print(e.response['error'])
            emoji_dict = {}

    # Replace bold text
    text = bold_pattern.sub(r'<b>\1</b>', text)
    # Replace italic text
    text = italic_pattern.sub(r'<i>\1</i>', text)
    # Replace strikethrough text
    text = strikethrough_pattern.sub(r'<del>\1</del>', text)
    # Replace links
    text = link_pattern.sub(r'<a href="\1">\2</a>', text)
    # Replace channels
    text = channel_pattern.sub(r'<span class="channel">#\1</span>', text)
    # Replace emojis
    text = emoji_pattern.sub(lambda match: emoji_dict.get(match.group(1), match.group(0)), text)

    return text


def cache_emojis(emojis, file_path='emoji_cache.json'):
    with open(file_path, 'w') as file:
        json.dump(emojis, file)

def load_cached_emojis(file_path='emoji_cache.json'):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}