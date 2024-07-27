import json
import os
from typing import List

from utils.hashing import calculate_md5


def get_cached_users():
    data_dir = os.path.join(os.environ.get("LOCALAPPDATA"), "slack_native")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    users_cache = os.path.join(data_dir, "users.json")
    if not os.path.exists(users_cache):
        with open(users_cache, "w") as f:
            json.dump({}, f)
        return None
    with open(users_cache, "r") as f:
        users: dict[str, dict] = json.load(f)
        return users


def cache_users(users: dict[str, dict]):
    with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "r") as r:
        current_users: dict[str, dict] = json.load(r)
        new_users = current_users
        for user in users:
            new_users[user] = users[user]

        with open(os.environ.get("LOCALAPPDATA") + "/slack_native/users.json", "w") as w:
            json.dump(new_users, w)


def cache_profile_pictures(users: dict[str, dict], file_write_lock=None):
    for user in users:
        user = users[user]
        cache_profile_picture(user, ["48"], [user["profile"]["image_48"]], file_write_lock)


def cache_profile_picture(user, resolutions: List[str], images: List[bytes], file_write_lock=None):
    with file_write_lock:
        for res, image in zip(resolutions, images):
            file_name = calculate_md5(user["id"].encode()) + "image_" + res + ".png"
            image_path = f"{os.environ.get('LOCALAPPDATA')}/slack_native/{file_name}"
            with open(image_path, "wb") as f:
                f.write(image)
            user["profile"][f"image_{res}"] = image_path
        # now cache the image path in the user's profile
        cache_users({user["id"]: user})
