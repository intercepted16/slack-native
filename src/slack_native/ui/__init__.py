from functools import partial
from typing import List

import darkdetect
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QLabel, QPushButton
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QWidget
from qt_async_threads import QtAsyncRunner
from slack_sdk.errors import SlackApiError
import sys

from slack_native.signals import MessagesUpdatedSignal
from slack_native.ui.widgets.messages_page import MessagesPage
from slack_native.ui.widgets.sidebar import SideBar
from slack_native.ui.widgets.tray import Tray
from slack_native.slack_client import slack_client


messages: List[dict] = []


class MainWindow(QMainWindow):
    def __init__(self, messages_manager: MessagesUpdatedSignal):
        super().__init__()
        self.messages_manager = messages_manager

        self.setWindowTitle("Slack Native")
        self.setWindowIcon(QIcon("assets/slack.png"))
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget(self)
        main_layout = QHBoxLayout(
            central_widget)  # Use QHBoxLayout for main layout to place sidebar and content side by side

        self.sidebarLayout = None

        self.contentStack = None

        try:
            response = slack_client.users_conversations()
            channels = response.get("channels")
            channels.sort(key=lambda x: x["name"])
        except SlackApiError as e:
            print(e)
            channels = []

        # TODO: add actual pages instead of QLabel placeholders
        runner = QtAsyncRunner()

        async def on_messages_click(messages_page: MessagesPage):
            await messages_page.init()

        self.buttons = [
            (QPushButton("Home"), partial(QLabel, "Home Page"), None),
            (QPushButton("Messages"), partial(MessagesPage, slack_client, self.messages_manager, channels),
             runner.to_sync(on_messages_click)),
            (QPushButton("Profile"), partial(QLabel, "Profile Page"), None),
            (QPushButton("Settings"), partial(QLabel, "Settings Page"), None),
        ]

        self.sidebar = SideBar(self.buttons)
        self.contentStack = self.sidebar.contentStack

        main_layout.addWidget(self.sidebar, 1)
        main_layout.addWidget(self.contentStack, 3)

        # Set centralWidget as the central widget of the main window
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.adjust_button_font_size()

    def adjust_button_font_size(self):
        window_height = self.height()
        font_size = window_height // 40  # Change the divisor to adjust the scaling factor

        for i, (button, _, _) in enumerate(self.buttons):
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)


class ThemeManager:
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))

    @staticmethod
    def enable_dark(app):
        app.setStyle(QStyleFactory.create("Fusion"))
        app.setPalette(ThemeManager.dark_palette)

    @staticmethod
    def enable_light(app):
        app.setStyle(QStyleFactory.create("Fusion"))

    @staticmethod
    def enable_system(app):
        if darkdetect.isDark():
            ThemeManager.enable_dark(app)
        else:
            ThemeManager.enable_light(app)


def main(show_window_signal):
    messages_manager = MessagesUpdatedSignal(slack_client, QtAsyncRunner())
    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(messages_manager)
    show_window_signal.show_window.connect(lambda: window.show())
    ThemeManager.enable_system(app)
    tray = Tray(window, app)
    tray.show()
    # must keep a reference to tray, otherwise it will be garbage collected
    window.tray = tray
    window.show()
    app.aboutToQuit.connect(lambda: sys.exit(0))
    return app, window, messages_manager
