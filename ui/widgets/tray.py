from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QSystemTrayIcon


class Tray(QSystemTrayIcon):
    def __init__(self, window, app):
        super().__init__()
        icon = QIcon("assets/slack.png")

        tray = QSystemTrayIcon()
        tray.setIcon(icon)
        tray.setVisible(True)

        menu = QMenu()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        # if single click, show the window
        tray.activated.connect(lambda reason: window.show() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)

