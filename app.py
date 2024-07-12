from typing import List
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QLabel, QPushButton, \
    QVBoxLayout  # Add QVBoxLayout import
from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtCore import Qt
import sys
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget
from PySide6.QtWidgets import QListWidgetItem
import parse
from common import MessagesManager
from PySide6.QtWidgets import QListWidget
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from PySide6.QtGui import QResizeEvent
import keyring
from PySide6.QtWidgets import QTextBrowser

# Keyring is cross-platform, e.g: on Windows, it uses the Windows Credential Manager
slack_token = keyring.get_password("slack_native", "access_token")
slack_client = WebClient(slack_token)
messages: List[dict] = []


class MainWindow(QMainWindow):
    def __init__(self, messages_manager: MessagesManager):
        super().__init__()

        self.messages_manager = messages_manager

        self.setWindowTitle("Slack Native")
        self.setWindowIcon(QIcon("assets/slack.png"))
        self.setGeometry(100, 100, 800, 600)

        # Central widget and main layout
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(
            central_widget)  # Use QHBoxLayout for main layout to place sidebar and content side by side

        # Initialize sidebarLayout
        self.sidebarLayout = QVBoxLayout()

        # Initialize QStackedWidget for content
        self.contentStack = QStackedWidget()

        # Define buttons and their corresponding pages
        messages_manager.messages_frame = messages_manager.create_messages_page(channels=None)
        print("t", messages_manager.messages_frame[0])

        # TODO: add actual pages instead of QLabel placeholders
        self.buttons = [
            (QPushButton("Home"), QLabel("Home Page")),
            (QPushButton("Messages"), messages_manager.messages_frame[0]),
            (QPushButton("Profile"), QLabel("Profile Page")),
            (QPushButton("Settings"), QLabel("Settings Page")),
        ]

        # Add pages to the contentStack and buttons to the sidebar
        for i, (button, page) in enumerate(self.buttons):
            self.sidebarLayout.addWidget(button)

            if isinstance(page, QLabel):
                page.setAlignment(Qt.AlignmentFlag.AlignCenter)
                page.setFont(QFont("Arial", 20))

            self.contentStack.addWidget(page)

            button.clicked.connect(lambda _, i=i: self.contentStack.setCurrentIndex(i))

        # Add a stretch to push the buttons to the top
        self.sidebarLayout.addStretch(1)

        # messages_manager.messages_updated.connect(self.update_messages_ui)

        sidebar_container = QWidget()  # Container for the sidebar
        sidebar_container.setLayout(self.sidebarLayout)
        main_layout.addWidget(sidebar_container, 1)  # Add sidebar container to the main layout
        main_layout.addWidget(self.contentStack, 3)  # Add content stack to the main layout

        # Set centralWidget as the central widget of the main window
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.adjust_button_font_size()

    def adjust_button_font_size(self):
        window_height = self.height()
        font_size = window_height // 40  # Change the divisor to adjust the scaling factor

        for i, (button, _) in enumerate(self.buttons):
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)

    def update_messages_ui(self, channel):
        channel_id = channel["id"]
        # Access the specific channel's messages widget based on channel_id
        messages_widget = self.messages_manager.messages_frame[1][channel_id]
        layout = messages_widget.layout()

        # Hide the currently visible channel's messages widget
        self.messages_manager.messages_frame[1][self.messages_manager.selected_channel].setVisible(False)

        show_channel(channel, self.messages_manager, self.messages_manager.messages_frame[1])

        # Clear existing messages in the channel's widget before adding new ones
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new messages to the specific channel's widget
        print(f"Updating messages for channel {channel_id}")
        self.messages_manager.messages_frame[1][channel_id].setVisible(True)
        channel_messages = fetch_messages(channel_id)
        # Add new messages
        for message in channel_messages:
            messages_widget.append(f"\n<p>{message}</p>")
            layout.addWidget(messages_widget)


def enable_dark_mode(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    app.setPalette(dark_palette)


def main():
    messages_manager = MessagesManager()
    app = QApplication(sys.argv)
    enable_dark_mode(app)
    window = MainWindow(messages_manager)
    return app, window, messages_manager
