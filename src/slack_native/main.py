import faulthandler
import socket
import threading

import requests
from qt_async_threads import QtAsyncRunner

from oauth import main as flask_app
from slack_native.slack_client import slack_client
from slack_native.ui.signals import ShowWindowSignal, MessagesUpdatedSignal
from ui import main


class App:
    """A singleton class to hold the *entire*; not the GUI `App` application instance,
    sharing signals and other objects."""

    def __init__(self):
        self.app = None
        self.window = None
        self.messages_manager = MessagesUpdatedSignal(slack_client, QtAsyncRunner())
        self.show_window_signal = ShowWindowSignal()

    def run(self):
        self.app, self.window, self.messages_manager = main(self)
        flask_thread = threading.Thread(target=flask_app, args=[self])
        flask_thread.start()
        self.app.exec_()


def instance_running():
    """Returns a boolean indicating whether another instance of the application
    is running."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", 5000)) == 0


# The main entry point for the application
if __name__ == "__main__":
    faulthandler.enable()

    if instance_running():
        # make a request to the Flask server, to bring the existing window to the front
        response = requests.post(
            "http://127.0.0.1:5000/ipc", json={"action": {"window": "show"}}
        )
        if response.status_code != 200:
            pass
        exit(0)
    app = App()
    app.run()
