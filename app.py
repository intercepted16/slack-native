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


def create_messages_page(messages_manager: MessagesManager, channels: List[dict] | None = None):
    if not channels:
        try:
            response = slack_client.users_conversations()
            channels = response.get("channels")
            channels.sort(key=lambda x: x["name"])
        except SlackApiError as e:
            print(e.response['error'])
            channels = []

    main_widget = QWidget()  # Main widget that holds everything
    main_layout = QHBoxLayout(main_widget)  # Main layout to arrange widgets horizontally

    # Dictionary to store scrollable widgets for each channel
    channel_messages_widgets = {}

    # Channels list area
    channels_list_widget = QListWidget()
    if channels:
        for channel in channels:
            item = QListWidgetItem(channel["name"])
            item.setData(Qt.ItemDataRole.UserRole, channel)
            channels_list_widget.addItem(item)

            # Create a text browser widget to display messages for each channel
            scroll_widget = QTextBrowser()
            scroll_widget.setOpenExternalLinks(True)
            scroll_widget.setVisible(False)  # Initially hidden

            messages_layout = QVBoxLayout(scroll_widget)
            label = QLabel(f"Messages for {channel['name']}")
            label.setFont(QFont("Arial", 20))
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            messages_layout.addWidget(label)
            # scroll_widget.setLayout(messages_layout)

            # Store the scrollable widget in the dictionary
            channel_messages_widgets[channel["id"]] = scroll_widget

    # Connect the itemPressed signal to a lambda that calls on_channel_selected and passes the channel_messages_widgets
    channels_list_widget.itemPressed.connect(
        lambda item: on_channel_selected(item, messages_manager, channel_messages_widgets))

    # Add the first channel's messages widget to the layout, or handle the default case
    for channel_id, widget in channel_messages_widgets.items():
        main_layout.addWidget(widget, 3)
        widget.setVisible(False)

    if channels:
        first_channel_id = channels[0]["id"]
        channel_messages_widgets[first_channel_id].setVisible(True)

    main_layout.addWidget(channels_list_widget, 1)  # Channels list takes less space

    return main_widget, channel_messages_widgets  # Return the main widget and the dictionary of message widgets


def show_channel(channel: dict, messages_manager: MessagesManager, messages_widgets: dict):
    # Hide the previously selected channel's messages widget
    if messages_manager.selected_channel in messages_widgets:
        messages_widgets[messages_manager.selected_channel].setVisible(False)

    # Reassign the selected channel
    messages_manager.selected_channel = channel["id"]

    # Show the selected channel's messages widget
    if channel:
        messages_widgets[channel["id"]].setVisible(True)


def on_channel_selected(item: QListWidgetItem, messages_manager: MessagesManager, messages_widgets: dict):
    channel = item.data(Qt.ItemDataRole.UserRole)
    print(f"Channel selected: {channel['name']}")

    if messages_manager.selected_channel == channel["id"]:
        print("Channel already selected")
        return

    show_channel(channel, messages_manager, messages_widgets)

    # Fetch the messages for the selected channel
    try:
        response = slack_client.conversations_history(channel=channel["id"], limit=10)
        channel_messages = response.get("messages")
        # compile the messages into one before rendering
        for message in channel_messages:
            print(type(message["text"]))
        channel_messages = [parse.render_message(message["text"]) for message in channel_messages if "text" in message]

        # Assuming messages_manager has a method to update the UI with new messages
        messages_manager.messages_updated.emit(channel["id"], channel_messages)

        # Update the UI of the selected channel's messages widget
        messages_widget = messages_widgets[channel["id"]]
        layout = messages_widget.layout()

        # Clear existing messages
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new messages
        for message in channel_messages:
            messages_widget.append(f"\n<p>{message}</p>")
            layout.addWidget(messages_widget)

    except SlackApiError as e:
        print(e.response['error'])


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
        messages_manager.messages_frame = create_messages_page(messages_manager)
        print(messages_manager.messages_frame)

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

        messages_manager.messages_updated.connect(self.update_messages_ui)

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

    def update_messages_ui(self, channel_id):
        # Access the specific channel's messages widget based on channel_id
        messages_widget = self.messages_manager.messages_frame[1][channel_id]
        layout = messages_widget.layout()

        # Hide the currently visible channel's messages widget
        self.messages_manager.messages_frame[1][self.messages_manager.selected_channel].setVisible(False)

        # Clear existing messages in the channel's widget before adding new ones
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new messages to the specific channel's widget
        for message in messages:
            label = QLabel(message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        self.messages_manager.messages_frame[1][channel_id].setVisible(True)


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
