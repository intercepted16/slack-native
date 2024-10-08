from flask import Flask, redirect, request, jsonify, Request
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.web import SlackResponse
from slack_sdk.errors import SlackApiError
import time
import hashlib
import hmac
from signals import MessagesUpdatedSignal
import keyring

load_dotenv(".env")
messages = []
app = Flask(__name__)
secret_key = os.environ.get("FLASK_SECRET_KEY")

if secret_key is None:
    raise Exception("FLASK_SECRET_KEY must be set in the environment.")
else:
    app.secret_key = secret_key

if bool(os.environ.get("DEV")) is True:
    redirect_uri = os.environ.get("DEV_SLACK_REDIRECT_URI")
else:
    # TODO: insert production redirect URI
    redirect_uri = ""


class This:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(This, cls).__new__(cls)
            # Initialize your global variable here
            cls._instance.messages_manager = None
        return cls._instance


this = This()


def main(messages_manager: MessagesUpdatedSignal, window):
    this.messages_manager = messages_manager
    this.show_window_signal = window
    app.run(debug=True, use_reloader=False, port=5000)


def handle_challenge(req: Request):
    request_json = req.json
    if request_json["challenge"] is not None:
        body = req.get_data()
        timestamp = req.headers['X-Slack-Request-Timestamp']
        if abs(time.time() - float(timestamp)) > 60 * 5:
            # The request timestamp is more than five minutes from local time.
            # It could be a replay attack, so let's ignore it.
            return
        sig_basestring = 'v0:' + timestamp + ':' + body.decode('utf-8')
        signature = 'v0=' + hmac.new(os.environ.get("SLACK_SIGNING_SECRET").encode('utf-8'),
                                     sig_basestring.encode('utf-8'),
                                     digestmod=hashlib.sha256).hexdigest()
        slack_signature = req.headers['X-Slack-Signature']
        if hmac.compare_digest(signature, slack_signature):
            return jsonify({"challenge": req.json["challenge"]})


@app.route('/install')
def install():
    client_id = os.environ.get("SLACK_CLIENT_ID")
    scopes = "channels:read,chat:write,channels:history,groups:history,im:history,mpim:history,emoji:read,users:read"
    if bool(os.environ.get("DEV")) is True:
        redirect_uri = os.environ.get("DEV_SLACK_REDIRECT_URI")
    else:
        # TODO: insert production redirect URI
        redirect_uri = ""
    slack_auth_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&user_scope={scopes}&redirect_uri={redirect_uri}"
    return redirect(slack_auth_url)


@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if code:
        client = WebClient()
        try:
            response: SlackResponse = client.oauth_v2_access(
                client_id=os.environ.get("SLACK_CLIENT_ID"),
                client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
                code=code,
                redirect_uri=redirect_uri
            )
            print(response.get("authed_user").get("access_token"))
            # Store access token in session or a more persistent storage
            access_token = response.get("authed_user").get("access_token")
            keyring.set_password("slack_native", "access_token", access_token)
            return "Authorization code received and access token stored."
        except SlackApiError as e:
            return f"Error: {e.response['error']}", 400
    else:
        return "No code provided by Slack.", 400


@app.route("/events/listen", methods=["POST"])
def listen():
    request_json = request.json
    if "challenge" in request_json:
        return handle_challenge(request)
    elif "event" in request_json:
        event = request_json["event"]
        if event["type"] == "message":
            # new message received, update the UI
            messages[event["channel"]].append(event["text"])
            print(messages)
            this.messages_manager.messages_updated_signal.emit(event["channel"], messages[event["channel"]])

    return "Request received."


@app.route("/ipc", methods=["POST"])
def ipc():
    body = request.json
    action: dict = body.get("action")
    if not action:
        return "No action specified", 400
    if action.get("window"):
        action = action.get("window")
        if action == "show":
            this.show_window_signal.show_window.emit()
    return "IPC endpoint"
