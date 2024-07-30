from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor

from utils.image_processing import RoundedImage


class Message:
    @staticmethod
    def write(cur: QTextCursor, message: dict):
        cur.movePosition(QTextCursor.MoveOperation.End)

        data_url = message["user"]["profile"]["image_48"]

        print("also person being rendered is", message["user"]["profile"]["real_name"])

        cur.insertImage(RoundedImage(data_url, 50))

        user_format = QTextCharFormat()
        user_format.setFontPointSize(20)
        user_format.setFontWeight(QFont.Weight.Bold)
        cur.insertText(f"\n{message['user']['profile']['real_name']}\n", user_format)

        text_format = "font-size: 18px;"
        cur.insertHtml(f"<p style=\"{text_format}\">{message['text']}</p>\n")
        # if it's the last message, add less space
        if message["is_last"]:
            cur.insertHtml("<br>")
        else:
            cur.insertHtml("<br>" * 2)
