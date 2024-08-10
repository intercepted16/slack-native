import json
import os
import time
from typing import List
from slack_native.common import APP_DATA_DIR
import xxhash


def get_cached_users():
    if not os.path.exists(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR)
    users_cache = os.path.join(APP_DATA_DIR, "users.json")
    if not os.path.exists(users_cache):
        with open(users_cache, "w") as f:
            json.dump({}, f)
        return None
    with open(users_cache, "r") as f:
        users: dict[str, dict] = json.load(f)
        return users


def cache_users(users: dict[str, dict]):
    with open(os.path.join(APP_DATA_DIR, "users.json"), "r") as r:
        current_users: dict[str, dict] = json.load(r)
        new_users = current_users.copy()
        new_users.update(users)

        with open(os.path.join(APP_DATA_DIR, "users.json"), "w") as w:
            json.dump(new_users, w)


def cache_profile_pictures(users: dict[str, dict]):
    for user in users.values():
        cache_profile_picture(user, ["48"], [user["profile"]["image_48"]], user["lock"])


def cache_profile_picture(
    user, resolutions: List[str], images: List[bytes], file_write_lock
):
    with file_write_lock:
        for res, image in zip(resolutions, images):
            time.perf_counter()
            file_name = (
                xxhash.xxh64(user["id"].encode()).hexdigest() + f"_x{res}" + ".png"
            )
            time.perf_counter()
            image_path = f"{APP_DATA_DIR}/{file_name}"
            if os.path.exists(image_path):
                # the hash has probably produced a collision, so we'll just skip this image
                continue
            with open(image_path, "wb") as f:
                f.write(image)
            user["profile"][f"image_{res}"] = image_path
        # now cache the image path in the user's profile
        # before caching the user, we need to remove the lock
        user.pop("lock")
        cache_users({user["id"]: user})
