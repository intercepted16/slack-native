async def fetch_user_info(slack_client, user_id) -> dict:
    user_info = slack_client.users_info(user=user_id)
    return user_info["user"]

async def fetch_image(url: str):
    image = await requests.get(url)
    image.raise_for_status()
    return image.content

async def fetch_profile_picture(slack_client, user_id):
    user_info = await fetch_user_info(slack_client, user_id)
    return user_info["profile"]["image_48"]
