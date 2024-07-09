from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QScrollArea
from flask import session, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class MessagesManager(QObject):
    messages_updated = pyqtSignal(list)  # Signal carrying a list of messages
    messages_frame: tuple[QScrollArea, QVBoxLayout] | None = None

def list_channels():
    token = session.get('access_token')
    if not token:
        return "Access token is missing. Please authorize first.", 401

    client = WebClient(token=token)
    try:
        response = client.conversations_list()
        channels = response.get("channels")
        return jsonify({"ok": response["ok"], "channels": channels})
    except SlackApiError as e:
        return jsonify({"ok": False, "error": e.response['error']}), 400 