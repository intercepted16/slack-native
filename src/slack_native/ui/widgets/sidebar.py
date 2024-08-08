import inspect
from functools import partial
from typing import List, Union

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget
from qt_async_threads import QtAsyncRunner

lazy_loaded = {}


# make a decorator to run when a button is clicked
async def on_button_click(contentStack: QStackedWidget, i, func: callable):
    # Print debug information about current widget and index
    print(f"Index: {i}")
    widget = contentStack.widget(i)
    print(f"Widget at index {i}: {widget}")

    if lazy_loaded.get(i):
        print("Widget already loaded")
        contentStack.setCurrentIndex(i)
        return

    lazy_loaded[i] = True

    # Run the function if provided
    if inspect.isfunction(func):
        if inspect.iscoroutinefunction(func):
            await func(widget)
        else:
            func(widget)
    else:
        print("No function to run")

    # Print debug information before inserting the widget
    print(f"Inserting widget at index {i}")
    print(f"Widget to insert: {widget}")
    index = contentStack.insertWidget(i, widget)
    print(f"Inserted widget at index {index}")
    contentStack.setCurrentIndex(i)

    # Print all widgets in contentStack for verification
    print("Current widgets in contentStack:")
    for index in range(contentStack.count()):
        print(f"Index {index}: {contentStack.widget(index)}")


class SideBar(QWidget):
    contentStack = None

    def __init__(self, buttons: List[tuple[QPushButton, callable, Union[callable, None]]]):
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
                partial(self.runner.to_sync(on_button_click), self.contentStack, i, func))

        self.layout.addStretch(1)
        self.setLayout(self.layout)
