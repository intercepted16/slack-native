from ui import main
from oauth import main as flask_app
import threading
import requests
from signals import ShowWindowSignal
import socket


def instance_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', 5000)) == 0


if __name__ == '__main__':
    show_window_signal = ShowWindowSignal()

    if instance_running():
        print("Another instance is already running")
        # make a request to the Flask server, to bring the existing window to the front
        response = requests.post("http://127.0.0.1:5000/ipc", json={"action": {"window": "show"}})
        if response.status_code != 200:
            print("Error bringing the existing window to the front")
        exit(0)

    app, window, messages_manager = main(show_window_signal)

    flask_thread = threading.Thread(target=flask_app, args=[messages_manager, show_window_signal])
    flask_thread.start()
    app.exec_()
