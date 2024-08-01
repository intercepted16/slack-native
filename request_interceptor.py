import os.path
import names
import httpretty
import json


class MockUser:
    def __init__(self, user_id):
        random_full_name = names.get_full_name()
        random_name = names.get_first_name()
        self.typical_response = {
            "ok": True,
            "user": {
                "id": user_id,
                "team_id": "T012AB3C4",
                "name": random_name,
                "deleted": False,
                "color": "9f69e7",
                "real_name": random_full_name,
                "tz": "America/Los_Angeles",
                "tz_label": "Pacific Daylight Time",
                "tz_offset": -25200,
                "profile": {
                    "avatar_hash": "ge3b51ca72de",
                    "status_text": "Print is dead",
                    "status_emoji": ":books:",
                    "real_name": random_full_name,
                    "display_name": random_name,
                    "real_name_normalized": random_full_name,
                    "display_name_normalized": random_name,
                    "email": "spengler@ghostbusters.example.com",
                    "image_original": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_24": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_32": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_48": os.path.abspath("assets/slack.png"),
                    "image_72": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_192": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_512": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "team": "T012AB3C4"
                },
                "is_admin": True,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": False,
                "updated": 1502138686,
                "is_app_user": False,
                "has_2fa": False
            }
        }


def users_info(request, uri, response_headers):
    if not request.headers.get("Authorization"):
        return [200, response_headers, json.dumps({"ok": False, "error": "not_authed"})]
    else:
        print(request.body)
        # weird quirk with the request body, it's a string
        body = request.body.decode("utf-8")
        user = body.split("=")[1]
        return [200, response_headers, json.dumps(MockUser(user).typical_response)]


class MockUserConversations:
    def __init__(self):
        self.typical_response = {
            "ok": True,
            "channels": [
                {
                    "id": "C012AB3CD",
                    "name": "general",
                    "is_channel": True,
                    "is_group": False,
                    "is_im": False,
                    "created": 1449252889,
                    "creator": "U012A3CDE",
                    "is_archived": False,
                    "is_general": True,
                    "unlinked": 0,
                    "name_normalized": "general",
                    "is_shared": False,
                    "is_ext_shared": False,
                    "is_org_shared": False,
                    "pending_shared": [],
                    "is_pending_ext_shared": False,
                    "is_member": True,
                    "is_private": False,
                    "is_mpim": False,
                    "updated": 1678229664302,
                    "topic": {
                        "value": "Company-wide announcements and work-based matters",
                        "creator": "",
                        "last_set": 0
                    },
                    "purpose": {
                        "value": "This channel is for team-wide communication and announcements. All team members are in this channel.",
                        "creator": "",
                        "last_set": 0
                    },
                    "previous_names": [],
                },
                {
                    "id": "C061EG9T2",
                    "name": "random",
                    "is_channel": True,
                    "is_group": False,
                    "is_im": False,
                    "created": 1449252889,
                    "creator": "U061F7AUR",
                    "is_archived": False,
                    "is_general": False,
                    "unlinked": 0,
                    "name_normalized": "random",
                    "is_shared": False,
                    "is_ext_shared": False,
                    "is_org_shared": False,
                    "pending_shared": [],
                    "is_pending_ext_shared": False,
                    "is_private": False,
                    "is_mpim": False,
                    "updated": 1678229664302,
                    "topic": {
                        "value": "Non-work banter and water cooler conversation",
                        "creator": "",
                        "last_set": 0
                    },
                    "purpose": {
                        "value": "A place for non-work-related flimflam, faffing, hodge-podge or jibber-jabber you'd "
                                 "prefer to keep out of more focused work-related channels.",
                        "creator": "",
                        "last_set": 0
                    },
                    "previous_names": [],
                    "num_members": 4
                }
            ],
            "response_metadata": {
                "next_cursor": "dGVhbTpDMDYxRkE1UEI="
            }
        }


class MockConversationsHistory:
    def __init__(self):
        self.typical_response = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U123ABC456",
                    "text": "Hello!",
                    "ts": "1512085950.000216"
                },
                {
                    "type": "message",
                    "user": "U222BBB222",
                    "text": "Hi! How are you?",
                    "ts": "1512104434.000490"
                },
                {
                    "type": "message",
                    "user": "U123ABC456",
                    "ts": "1512104434.000490",
                    "thread_ts": "1512104434.0004900",
                    "text": "Guys, how are you doing?"
                }
            ],
            "has_more": True,
            "pin_count": 0,
            "response_metadata": {
                "next_cursor": "bmV4dF90czoxNTEyMDg1ODYxMDAwNTQz"
            }
        }


class MockConversationsReplies:
    def __init__(self):
        self.typical_response = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U123ABC456",
                    "text": "Hello!",
                    "ts": "1512085950.000216",
                    "parent_user_id": "U456XYZ789"
                },
            ]
        }


def user_conversations(request, uri, response_headers):
    if not request.headers.get("Authorization"):
        return [200, response_headers, json.dumps({"ok": False, "error": "not_authed"})]
    else:
        return [200, response_headers, json.dumps(MockUserConversations().typical_response)]


def conversations_history(request, uri, response_headers):
    if not request.headers.get("Authorization"):
        return [200, response_headers, json.dumps({"ok": False, "error": "not_authed"})]
    else:
        return [200, response_headers, json.dumps(MockConversationsHistory().typical_response)]


def conversations_replies(request, uri, response_headers):
    if not request.headers.get("Authorization"):
        return [200, response_headers, json.dumps({"ok": False, "error": "not_authed"})]
    else:
        return [200, response_headers, json.dumps(MockConversationsReplies().typical_response)]


def inject():
    httpretty.enable(verbose=True,
                     allow_net_connect=True)  # enable HTTPretty so that it will monkey patch the socket module
    httpretty.register_uri(httpretty.POST, "https://slack.com/api/users.info",
                           body=users_info)
    httpretty.register_uri(httpretty.POST, "https://slack.com/api/users.conversations", body=user_conversations)
    httpretty.register_uri(httpretty.POST, "https://slack.com/api/conversations.history", body=conversations_history)
    httpretty.register_uri(httpretty.POST, "https://slack.com/api/conversations.replies", body=conversations_replies)
    # do not disable if in DEV mode, we want to mock still
    # httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
    # httpretty.reset()    # reset HTTPretty state (clean up registered urls and request history)
