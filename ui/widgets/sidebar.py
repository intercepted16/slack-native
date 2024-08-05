import inspect
from functools import partial
from typing import List, Union

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget
from qt_async_threads import QtAsyncRunner


# make a decorator to run when a button is clicked
async def on_button_click(contentStack: QStackedWidget, i, widget_resolver: callable, func: callable):
    # Print debug information about current widget and index
    print(f"Index: {i}")
    widget_at_index = contentStack.widget(i)
    print(f"Widget at index {i}: {widget_at_index}")

    # Check if the widget exists at the specified index
    if widget_at_index is not None:
        print("Widget already exists")
        contentStack.setCurrentIndex(i)
        return

    # Resolve and add the widget
    if inspect.iscoroutinefunction(widget_resolver):
        widget = await widget_resolver()
    else:
        widget = widget_resolver()

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
    contentStack.setCurrentIndex(i)
    contentStack.addWidget(widget)
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
            self.layout.addWidget(button)
            button.clicked.connect(
                partial(self.runner.to_sync(on_button_click), self.contentStack, i, widget_resolver, func))

        self.layout.addStretch(1)
        self.setLayout(self.layout)
