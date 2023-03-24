from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtCore import QTimer, QPointF, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QBrush
from PyQt5 import QtCore

class InteractablePathItem(QGraphicsPathItem):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setPath(path)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self._grabber_size = 20
        self._grabbers = []
        self._snap_threshold = 20
        self._snap_timer = QTimer()
        self._snap_timer.setInterval(200)  # Set the snap interval to 100 milliseconds
        self._snap_timer.timeout.connect(self.snapAndUpdateGrabbers)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setBrush(QBrush(QColor(20, 170, 170)))
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DotLine)
        else:
            pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawPath(self.path())

    def createGrabber(self, pos):
        grabber_rect = QtCore.QRectF(-self._grabber_size / 2, -self._grabber_size / 2, self._grabber_size, self._grabber_size)
        grabber = QGraphicsRectItem(grabber_rect, self)
        grabber.setPen(QPen(QColor(255, 255, 0)))
        # grabber.setBrush(QBrush(QColor(255, 255, 255)))
        grabber.setFlag(QGraphicsItem.ItemIsMovable, True)
        grabber.setFlag(QGraphicsItem.ItemIsSelectable, False)
        grabber.setPos(pos)
        grabber.hide()
        return grabber

    def showGrabbers(self):
        self._grabbers = []
        for i in range(self.path().elementCount()):
            path_elem = self.path().elementAt(i)
            if path_elem.type != QPainterPath.ElementType.MoveToElement:
                grabber = self.createGrabber(QPointF(path_elem.x, path_elem.y))
                self._grabbers.append(grabber)
        if self.isSelected():
            for grabber in self._grabbers:
                grabber.show()

    def hideGrabbers(self):
        for grabber in self._grabbers:
            grabber.hide()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self._snap_timer.isActive():
            self._snap_timer.start()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def snapToClosest(self):
        scene_items = self.scene().items()
        interactable_items = [item for item in scene_items if isinstance(item, InteractablePathItem) and item is not self]

        for grabber1 in self._grabbers:
            closest_item = None
            closest_distance = float('inf')
            closest_point = None

            for item in interactable_items:
                for grabber2 in item._grabbers:
                    distance = (grabber1.scenePos() - grabber2.scenePos()).manhattanLength()
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_item = item
                        closest_point = grabber2.scenePos()

            if closest_distance <= self._snap_threshold:
                delta = closest_point - grabber1.scenePos()
                self.setPos(self.pos() + delta)
                break
            

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.highlightGrabbers()
            else:
                self.hideGrabbers()
        return super().itemChange(change, value)

    def highlightGrabbers(self):
        self.hideGrabbers()
        self.showGrabbers()

    def snapGrabbers(self):
        for grabber1 in self._grabbers:
            for grabber2 in self._grabbers:
                if grabber1 is not grabber2:
                    distance = (grabber1.pos() - grabber2.pos()).manhattanLength()
                    if distance <= self._snap_threshold:
                        grabber1.setPos(grabber2.pos())
                        break

    def snapAndUpdateGrabbers(self):
        self.snapToClosest()
        self.highlightGrabbers()
        self._snap_timer.stop()