from typing import List
from PyQt6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QLabel, QPushButton, QVBoxLayout  # Add QVBoxLayout import
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont
from PyQt6.QtCore import Qt
import sys
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QHBoxLayout, QStackedWidget, QScrollArea
from common import MessagesManager
from PyQt6.QtWidgets import QListWidget
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import keyring

# Keyring is cross-platform, e.g: on Windows, it uses the Windows Credential Manager
slack_token = keyring.get_password("slack_native", "access_token")
slack_client = WebClient(slack_token)
messages = []


def create_messages_page(channels: List[object] | None = None):
    if not channels:
        try:
            response = slack_client.conversations_list()
            channels = response.get("channels")
        except SlackApiError as e:
            print(e.response['error'])
            # TODO: Make a global handler that shows the error message in the UI
            channels = []

    mainWidget = QWidget()  # Main widget that holds everything
    mainLayout = QHBoxLayout(mainWidget)  # Main layout to arrange widgets horizontally
    
    # Messages area
    messagesWidget = QWidget()
    scrollWidget = QScrollArea()
    scrollWidget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scrollWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scrollWidget.setWidgetResizable(True)
    scrollWidget.setWidget(messagesWidget)
    
    messagesLayout = QVBoxLayout(messagesWidget)
    label = QLabel("Messages Page")
    label.setFont(QFont("Arial", 20))
    label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    messagesLayout.addWidget(label)
    messagesWidget.setLayout(messagesLayout)
    
    # Channels list area
    channelsListWidget = QListWidget()
    for channel in channels:
        channelsListWidget.addItem(channel["name"])
    
    # Adding both the scroll area and the channels list to the main layout
    mainLayout.addWidget(scrollWidget, 3)  # Messages area takes more space
    mainLayout.addWidget(channelsListWidget, 1)  # Channels list takes less space
    
    return mainWidget, messagesLayout  # Return the main widget that contains everything


class MainWindow(QMainWindow):
    def __init__(self, messages_manager: MessagesManager):
        super().__init__()

        self.messages_manager = messages_manager

        self.setWindowTitle("Slack Native")
        self.setWindowIcon(QIcon("assets/slack.png"))
        self.setGeometry(100, 100, 800, 600)

        # Central widget and main layout
        centralWidget = QWidget(self)
        mainLayout = QHBoxLayout(centralWidget)  # Use QHBoxLayout for main layout to place sidebar and content side by side

        # Initialize sidebarLayout
        self.sidebarLayout = QVBoxLayout()

        # Initialize QStackedWidget for content
        self.contentStack = QStackedWidget()

        # Define buttons and their corresponding pages
        messages_manager.messages_frame = create_messages_page()
        print(messages_manager.messages_frame)

        # TODO: add actual pages instead of QLabel placeholders
        self.buttons = [
            (QPushButton("Home"), QLabel("Home Page")),
            (QPushButton("Messages"), messages_manager.messages_frame[0]),
            (QPushButton("Profile"), QLabel("Profile Page")),
            (QPushButton ("Settings"), QLabel("Settings Page")),
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

        messages_manager.messages_updated.connect(self.update_messages_ui)


        # Add sidebarLayout and contentStack to the mainLayout
        sidebarContainer = QWidget()  # Container for the sidebar
        sidebarContainer.setLayout(self.sidebarLayout)
        mainLayout.addWidget(sidebarContainer, 1)  # Add sidebar container to the main layout
        mainLayout.addWidget(self.contentStack, 3)  # Add content stack to the main layout

        # Set centralWidget as the central widget of the main window
        self.setCentralWidget(centralWidget)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustButtonFontSize()

    def adjustButtonFontSize(self):
        window_height = self.height()
        font_size = window_height // 40  # Change the divisor to adjust the scaling factor

        for i, (button, _) in enumerate(self.buttons):
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)
    def update_messages_ui(self, messages):
        # This method will now run in the main GUI thread
        for message in messages:
            label = QLabel(message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_manager.messages_frame[1].layout().addWidget(label) 

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