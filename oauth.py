from flask import Flask, redirect, request, session, jsonify, Request
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.web import SlackResponse
from slack_sdk.errors import SlackApiError
import time
import hashlib
import hmac
load_dotenv(".env")
messages = []


def handle_challenge(request: Request):
    request_json = request.json
    if request_json["challenge"] is not None:
        body = request.get_data()
        timestamp = request.headers['X-Slack-Request-Timestamp']
        if abs(time.time() - float(timestamp)) > 60 * 5:
            # The request timestamp is more than five minutes from local time.
            # It could be a replay attack, so let's ignore it.
            return
        sig_basestring = 'v0:' + timestamp + ':' + body.decode('utf-8')
        signature = 'v0=' + hmac.new(os.environ.get("SLACK_SIGNING_SECRET").encode('utf-8'),
                                sig_basestring.encode('utf-8'),
                                digestmod=hashlib.sha256).hexdigest()
        slack_signature = request.headers['X-Slack-Signature']
        print("sig",signature)
        print(slack_signature)
        if hmac.compare_digest(signature, slack_signature):
            return jsonify({"challenge": request.json["challenge"]})

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

@app.route('/install')
def install():
    client_id = os.environ.get("SLACK_CLIENT_ID")
    scopes = "channels:read,chat:write,channels:history,groups:history,im:history,mpim:history"
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
                session['access_token'] = response.get("authed_user").get("access_token")
                return "Authorization code received and access token stored."
        except SlackApiError as e:
            return f"Error: {e.response['error']}", 400
    else:
        return "No code provided by Slack.", 400
    

# for development purposes, will be removed in production
@app.route('/')
def home():
   access_token = session.get('access_token', 'No access token found. Please authorize the app.') 
   return f"Access token: {access_token}"


@app.route('/message/send')
def send_message():
    token = session.get('access_token')
    if not token:
        return "Access token is missing. Please authorize first.", 401
    
    client = WebClient(token=token)
    channel_id = request.args.get('channel_id')
    if not channel_id:
        return "Channel ID parameter is missing.", 400
    text = request.args.get('text')
    if not text:
        return "Text parameter is missing.", 400
    
    try:
        response = client.chat_postMessage(channel=channel_id, text=text)
        return jsonify({"ok": response["ok"], "message": "Message sent successfully"})
    except SlackApiError as e:
        return jsonify({"ok": False, "error": e.response['error']}), 400
    
@app.route("/message/delete")
def delete_message():
    token = session.get('access_token')
    if not token:
        return "Access token is missing. Please authorize first.", 401
    
    client = WebClient(token=token)
    channel_id = request.args.get('channel_id')
    if not channel_id:
        return "Channel ID parameter is missing.", 400
    ts = request.args.get('ts')
    if not ts:
        return "Timestamp parameter is missing.", 400
    
    try:
        response = client.chat_delete(channel=channel_id, ts=ts, as_user=True)
        return jsonify({"ok": response["ok"], "message": "Message deleted successfully"})
    except SlackApiError as e:
        return jsonify({"ok": False, "error": e.response['error']}), 400
    
@app.route("/message/update")
def update_message():
    token = session.get('access_token')
    if not token:
        return "Access token is missing. Please authorize first.", 401
    
    client = WebClient(token=token)
    channel_id = request.args.get('channel_id')
    if not channel_id:
        return "Channel ID parameter is missing.", 400
    ts = request.args.get('ts')
    if not ts:
        return "Timestamp parameter is missing.", 400
    text = request.args.get('text')
    if not text:
        return "Text parameter is missing.", 400
    
    try:
        response = client.chat_update(channel=channel_id, ts=ts, text=text)
        return jsonify({"ok": response["ok"], "message": "Message updated successfully"})
    except SlackApiError as e:
        return jsonify({"ok": False, "error": e.response['error']}), 400

@app.route("/message/list")
def list_messages():
    token = session.get('access_token')
    if not token:
        return "Access token is missing. Please authorize first.", 401
    
    client = WebClient(token=token)
    channel_id = request.args.get('channel_id')
    if not channel_id:
        return "Channel ID parameter is missing.", 400
    
    limit = request.args.get('limit', None)
    
    try:
        response = client.conversations_history(channel=channel_id, limit=limit)
        messages = response.get("messages")
        return jsonify({"ok": response["ok"], "messages": messages})
    except SlackApiError as e:
        return jsonify({"ok": False, "error": e.response['error']}), 400
    
@app.route("/events/listen", methods=["POST"])
def listen():
    request_json = request.json
    if "challenge" in request_json:
        return handle_challenge(request)
    elif "event" in request_json:
        event = request_json["event"]
        if event["type"] == "message":
            # new message received, update the UI
            messages.append(event.get("text"))
            print(messages)

    return "Request received."
    
if __name__ == '__main__':
    app.run(debug=True)