from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QBrush


class RoundedImage(QImage):
    def __init__(self, source_path: str | bytes, radius: int):
        """Return a rounded version of the image."""
        if isinstance(source_path, str):
            super().__init__(source_path)
        else:
            super().__init__()
            super().loadFromData(source_path)
        self.source_path: str | None = None
        self.radius = radius
        self.image = super()
        image = self.image
        width, height = image.width(), image.height()

        # Create a mask image with rounded corners
        mask = QImage(width, height, QImage.Format.Format_Alpha8)
        mask.fill(Qt.GlobalColor.transparent)

        # Draw the rounded rectangle
        painter = QPainter(mask)
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.setPen(Qt.GlobalColor.transparent)
        painter.drawRoundedRect(0, 0, width, height, self.radius, self.radius)
        painter.end()

        # Apply the mask to the original image
        image.setAlphaChannel(mask)
