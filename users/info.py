async def fetch_user_info(slack_client, user_id) -> dict:
    user_info = slack_client.users_info(user=user_id)
    return user_info["user"]
