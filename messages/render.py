from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor

from utils.image_processing import RoundedImage


def render_message(message, text_browser):
    if isinstance(message["user"]["profile"]["image_48"], bytes):
        print("Rendering message and image is", message["user"]["profile"]["image_48"][0:10])
    else:
        print("Rendering message and image is", message["user"]["profile"]["image_48"])
    cursor = text_browser.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)

    data_url = message["user"]["profile"]["image_48"]

    print("also person being rendered is", message["user"]["profile"]["real_name"])

    cursor.insertImage(RoundedImage(data_url, 50))

    user_format = QTextCharFormat()
    user_format.setFontPointSize(20)
    user_format.setFontWeight(QFont.Weight.Bold)
    cursor.insertText(f"\n{message['user']['real_name']}\n", user_format)

    text_format = "font-size: 18px;"
    cursor.insertHtml(f"<p style=\"{text_format}\">{message['text']}</p>\n")
    # if it's the last message, add less space
    if message["is_last"]:
        cursor.insertHtml("<br>")
    else:
        cursor.insertHtml("<br>" * 2)
