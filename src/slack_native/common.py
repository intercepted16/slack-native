import os
import platform

CURRENT_SYSTEM = platform.system()
if CURRENT_SYSTEM == "Windows":
    APP_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA"), "slack_native")
elif CURRENT_SYSTEM == "Linux":
    APP_DATA_DIR = os.path.join(os.environ.get("HOME"), ".config", "slack_native")
elif CURRENT_SYSTEM == "Darwin":
    # not tested on macOS
    APP_DATA_DIR = os.path.join(
        os.environ.get("HOME"), "Library", "Application Support", "slack_native"
    )
