from typing import List

from PySide6.QtWidgets import QScrollArea

from slack_native.widgets import Message


async def render_messages(
    scroll_area: QScrollArea, channel_messages: List[dict]
) -> None:
    """Given a list of messages, a Slack API Client, an array of messages` text browsers, render each message in their
     respective text browser.
     This is different from the `write` method in the `Message` class, as it also fetches user
    information and profile pictures.
    """
    # clear the scroll area
    for i in reversed(range(scroll_area.widget().layout().count())):
        scroll_area.widget().layout().itemAt(i).widget().deleteLater()
    for message in channel_messages:
        await Message.write(scroll_area, message=message)
