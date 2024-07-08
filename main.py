from app import main
from oauth import main as flask_app
import threading
import sys

if __name__ == '__main__':
    app, window, messages_manager = main()
    flask_thread = threading.Thread(target=flask_app, args=[messages_manager])
    flask_thread.start()
    window.show()
    sys.exit(app.exec())