from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt
from interactable_path_item import InteractablePathItem

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_panning = False
        self._mouse_pressed_pos = None
        self.cursor_position_callback = None
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def wheelEvent(self, event):
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._mouse_pressed_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif self.itemAt(event.pos()):
            self.setCursor(Qt.OpenHandCursor)
            super().mousePressEvent(event)
        else:
            self.setCursor(Qt.ArrowCursor)
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning and self._mouse_pressed_pos is not None:
            delta = event.pos() - self._mouse_pressed_pos
            self._mouse_pressed_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def updateSnapPoints(self):
        for item in self.scene.items():
            if isinstance(item, InteractablePathItem):
                item.snapAndUpdateGrabbers()