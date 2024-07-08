from flask import Flask, redirect, request, session
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for session management

@app.route('/start-auth')
def start_auth():
    client_id = os.environ.get("SLACK_CLIENT_ID")
    scopes = "channels:read,chat:write"
    if bool(os.environ.get("DEV")) is True:
        redirect_uri = "https://moved-bluebird-nice.ngrok-free.app/auth/callback"
    else:
        # TODO: insert production redirect URI
        redirect_uri = ""
    slack_auth_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&user_scope={scopes}&redirect_uri={redirect_uri}"
    return redirect(slack_auth_url)

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if code:
        session['oauth_code'] = code  # Store the code in the session or handle it as needed
        return "Authorization code received."
    else:
        return "No code provided by Slack.", 400

if __name__ == '__main__':
    app.run(debug=True)