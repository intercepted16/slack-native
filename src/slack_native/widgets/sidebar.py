import inspect
from functools import partial
from typing import List, Union

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget
from qt_async_threads import QtAsyncRunner

lazy_loaded = {}


# make a decorator to run when a button is clicked
async def on_button_click(content_stack: QStackedWidget, i, func: callable):
    widget = content_stack.widget(i)

    if lazy_loaded.get(i):
        content_stack.setCurrentIndex(i)
        return

    lazy_loaded[i] = True

    # Run the function if provided
    if inspect.isfunction(func):
        if inspect.iscoroutinefunction(func):
            await func(widget)
        else:
            func(widget)
    else:
        pass

    content_stack.insertWidget(i, widget)
    content_stack.setCurrentIndex(i)


class SideBar(QWidget):
    contentStack = None

    def __init__(
        self, buttons: List[tuple[QPushButton, callable, Union[callable, None]]]
    ):
        super().__init__()
        self.layout = QVBoxLayout()
        self.buttons = buttons
        self.contentStack = QStackedWidget()
        self.runner = QtAsyncRunner()

        for i, (button, widget_resolver, func) in enumerate(self.buttons):
            # add the initial widget
            self.contentStack.insertWidget(i, widget_resolver())
            self.layout.addWidget(button)
            button.clicked.connect(
                partial(
                    self.runner.to_sync(on_button_click), self.contentStack, i, func
                )
            )

        self.layout.addStretch(1)
        self.setLayout(self.layout)
