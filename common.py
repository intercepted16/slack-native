import os
import platform

current_system = platform.system()
if current_system == "Windows":
    APP_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA"), "slack_native")
elif current_system == "Linux":
    APP_DATA_DIR = os.path.join(os.environ.get("HOME"), ".config", "slack_native")
elif current_system == "Darwin":
    # not tested on macOS
    APP_DATA_DIR = os.path.join(os.environ.get("HOME"), "Library", "Application Support", "slack_native")