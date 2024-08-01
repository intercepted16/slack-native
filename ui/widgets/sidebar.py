import inspect
from functools import partial
from typing import List, Union
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget
from qt_async_threads import QtAsyncRunner


# make a decorator to run when a button is clicked
async def on_button_click(contentStack: QStackedWidget, i, widget_resolver: callable, func: callable):
    if inspect.iscoroutinefunction(widget_resolver):
        widget = await widget_resolver()
    else:
        widget = widget_resolver()
    if inspect.iscoroutinefunction(func):
        await func(widget)
    else:
        func(widget)
    contentStack.setCurrentIndex(i)


class SideBar(QWidget):
    contentStack = None

    def __init__(self, buttons: List[tuple[QPushButton, callable, Union[callable, None]]]):
        super().__init__()
        self.layout = QVBoxLayout()
        self.buttons = buttons
        self.contentStack = QStackedWidget()
        self.runner = QtAsyncRunner()

        for i, (button, widget_resolver, func) in enumerate(self.buttons):
            # self.contentStack.addWidget(func)
            self.layout.addWidget(button)
            # add_to_sidebar(self.contentStack, func)
            button.clicked.connect(
                partial(self.runner.to_sync(on_button_click), self.contentStack, i, widget_resolver, func))

        self.layout.addStretch(1)
        self.setLayout(self.layout)
