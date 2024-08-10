from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QSystemTrayIcon


class Tray(QSystemTrayIcon):
    def __init__(self, window, app):
        super().__init__()
        icon = QIcon("assets/slack.png")
        # due to Python's garbage collection, the icon, menu & action(s) must be stored in a persistent object
        self.setIcon(icon)
        menu = QMenu()
        self.menu = menu
        quit_action = QAction("Quit")
        quit_action.triggered.connect(app.quit)
        self.quit_action = quit_action
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        # if single click, show the window
        self.activated.connect(
            lambda reason: window.show()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
