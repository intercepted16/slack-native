import json
import os
import time
from typing import List

import xxhash


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


def cache_profile_pictures(users: dict[str, dict]):
    for user in users:
        user = users[user]
        cache_profile_picture(user, ["48"], [user["profile"]["image_48"]], user["lock"])


def cache_profile_picture(user, resolutions: List[str], images: List[bytes], file_write_lock=None):
    with file_write_lock:
        for res, image in zip(resolutions, images):
            start = time.perf_counter()
            file_name = xxhash.xxh64(user["id"].encode()).hexdigest() + f"_x{res}" + ".png"
            end = time.perf_counter()
            print(f"Time to calculate xxhash: {end - start}")
            image_path = f"{os.environ.get('LOCALAPPDATA')}/slack_native/{file_name}"
            if os.path.exists(image_path):
                # the hash has probably produced a collision, so we'll just skip this image
                continue
            with open(image_path, "wb") as f:
                print("image is", image)
                f.write(image)
            user["profile"][f"image_{res}"] = image_path
        # now cache the image path in the user's profile
        # before caching the user, we need to remove the lock
        user.pop("lock")
        cache_users({user["id"]: user})
