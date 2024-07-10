import re
import keyring
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import requests

# Slack formatting patterns
bold_pattern = re.compile(r'\*(.*?)\*')
italic_pattern = re.compile(r'_(.*?)_')
strikethrough_pattern = re.compile(r'~(.*?)~')
link_pattern = re.compile(r'<(https?://\S+)(\|.*?)?>')
channel_pattern = re.compile(r'#(\w+)')
emoji_pattern = re.compile(r':(\w+):')


def fetch_emoji(emoji_name: str):
    # TODO: dynamically create the URL with the ID of the workspace
    url = "https://edgeapi.slack.com/cache/T0266FRGM/emojis/info?fp=af&_x_num_retries=0"

    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "text/plain;charset=UTF-8",
        "priority": "u=1, i",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "cookie": "b=.7f6d3a7f91a49fa25deb1a7a75981bb8; shown_ssb_redirect_page=1; tz=600; ssb_instance_id=88782ac3-cf28-4bae-972f-37557833f9be; shown_download_ssb_modal=1; show_download_ssb_banner=1; no_download_ssb_banner=1; lc=1719302924; d-s=1720603559; d=xoxd-559HyoyjyEFcp501mtzwT0NiXC%2F6hUEMusQaYBXD%2Fv8JjATjratJD0Po2my0oDea2O2QEjfTXYDsEZAukAJRqxp3vVU8gWodPCHDNhe3bGbwqyqTYNkFkMgC7M8GBw%2By%2B4MBfFIyX7XCqkYqP1bB43iKPVpEixWz%2FSsFLrdtY1SP12heGvEwSSGYS1zS%2FDSWC6BQSmE%3D; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jul+10+2024+19%3A28%3A07+GMT%2B1000+(Australian+Eastern+Standard+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=be51caff-fb27-4b35-a38f-ad1e7e1b5dbc&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C2%3A1%2C4%3A0&AwaitingReconsent=false; x=7f6d3a7f91a49fa25deb1a7a75981bb8.1720606589; web_cache_last_updated337a2a499a436d9ae22c2cffdca55138=1720606594597"
    }

    # TODO: replace sample token with a valid token
    data = {
        "token": "xoxc-2210535565-7290482160290-7327065577730-16df343f7eeb21cd1964d263c717c20f16a3279b3f5bf14143a7c5cd25d89b85",
        "updated_ids": {
            f"{emoji_name}": 0,
        }
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()["results"]
    if len(result) > 0:
        print(result)
        return result[0]["value"]
    else:
        return None


def render_message(text):
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
    # Replace emojis with <img> elements
    # TODO: cache the emojis to avoid fetching them every time
    # BUG: `QTextBrowser` does not render `img` tags
    text = emoji_pattern.sub(lambda match: f'<img src="{fetch_emoji(match.group(1))}" alt="{match.group(1)}">', text)
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
