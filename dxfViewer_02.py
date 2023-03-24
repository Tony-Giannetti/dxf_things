import sys
from math import sin, cos
import ezdxf

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtGui import QPen, QColor, QPainter, QPainterPath, QBrush
from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QGraphicsScene, QGraphicsView, QLabel, QWidget, QVBoxLayout, QSpinBox, QColorDialog
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsItemGroup

import shapely.geometry as geom
import shapely.ops as ops
from shapely.affinity import rotate


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

        # cursor_position_scene = self.mapToScene(event.pos())
        # if self.cursor_position_callback:
        #     self.cursor_position_callback(cursor_position_scene.x(), cursor_position_scene.y())


    def updateSnapPoints(self):
        for item in self.scene.items():
            if isinstance(item, InteractablePathItem):
                item.snapAndUpdateGrabbers()

    # def viewportEvent(self, event):
    #     if event.type() == QtCore.QEvent.HoverMove:
    #         item_under_cursor = self.itemAt(event.pos())
    #         if item_under_cursor and not self._is_panning:
    #             self.setCursor(Qt.OpenHandCursor)
    #         else:
    #             self.setCursor(Qt.ArrowCursor)
    #     return super().viewportEvent(event)
    

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
        self._snap_timer.setInterval(100)  # Set the snap interval to 100 milliseconds
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 100, 1600, 1000)
        self.setWindowTitle('DXF Viewer')
        
        # Add open file button
        button = QPushButton('Open File', self)
        button.move(20, 20)
        button.clicked.connect(self.openFile)

        # Create graphics view for displaying drawing
        self.view = CustomGraphicsView(self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.view.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setInteractive(True)
        self.view.move(20, 60)
        # self.view.resize(960, 620)
        self.view.setTransform(self.view.transform().scale(1, -1))
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self.cursor_position_label = QLabel(self)
        self.cursor_position_label.move(120, 20)
        self.cursor_position_label.resize(200, 20)

        # Set the callback for cursor position updates
        self.view.cursor_position_callback = self.updateCursorPositionLabel


        # Add the column of options on the right-hand side
        options_widget = QWidget(self)
        options_layout = QVBoxLayout(options_widget)
        options_widget.setGeometry(self.width() - 200, 60, 180, 300)

        # Pen thickness option
        pen_thickness_label = QLabel("Pen Thickness", options_widget)
        options_layout.addWidget(pen_thickness_label)
        self.pen_thickness_spinbox = QSpinBox(options_widget)
        self.pen_thickness_spinbox.setRange(1, 20)
        options_layout.addWidget(self.pen_thickness_spinbox)

        # Pen color option
        pen_color_label = QLabel("Pen Color", options_widget)
        options_layout.addWidget(pen_color_label)
        self.pen_color_button = QPushButton("Choose color", options_widget)
        options_layout.addWidget(self.pen_color_button)

        # Connect signals to slots
        self.pen_thickness_spinbox.valueChanged.connect(self.set_pen_thickness)
        self.pen_color_button.clicked.connect(self.choose_pen_color)

    def set_pen_thickness(self, thickness):
        for item in self.scene.items():
            if isinstance(item, InteractablePathItem):
                pen = item.pen()
                pen.setWidth(thickness)
                item.setPen(pen)

    def choose_pen_color(self):
        all_items = [item for item in self.scene.items() if isinstance(item, InteractablePathItem)]
        if all_items:
            initial_color = all_items[0].pen().color()
            color = QColorDialog.getColor(initial_color, self, "Choose Pen Color")
            if color.isValid():
                for item in all_items:
                    pen = item.pen()
                    pen.setColor(color)
                    item.setPen(pen)


    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', "DXF files (*.dxf)")
        if filename:
            print(f"Opening {filename}")
            doc = ezdxf.readfile(filename)

            # Clear scene
            self.scene.clear()

        # Buffer distance for closed profile detection
        buffer_distance = 1e-3

        # Collect all entities in a list
        entities = []

        for entity in doc.entities:
            if entity.dxftype() == 'LINE':
                start_point = entity.dxf.start
                end_point = entity.dxf.end
                entities.append(geom.LineString([(start_point[0], start_point[1]), (end_point[0], end_point[1])]))
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                entities.append(geom.Point(center).buffer(radius))
            elif entity.dxftype() == 'ARC':
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                if end_angle < start_angle:
                    end_angle += 360
                entities.append(rotate(geom.Point(center).buffer(radius), start_angle, 'center').boundary)
                entities.append(rotate(geom.Point(center).buffer(radius), end_angle, 'center').boundary)
            elif entity.dxftype() == 'LWPOLYLINE':
                vertices = list(entity.vertices())
                if entity.closed:
                    vertices.append(vertices[0])
                entities.append(geom.LineString([(v[0], v[1]) for v in vertices]))

        # Find closed profiles
        entities = [entity.buffer(buffer_distance) for entity in entities]
        filled_profiles = ops.unary_union(entities)

        # Draw closed profiles
        if isinstance(filled_profiles, geom.Polygon):
            filled_profiles = [filled_profiles]

        for profile in filled_profiles:
            path = QPainterPath()
            path.moveTo(*profile.exterior.coords[0])
            for coords in profile.exterior.coords[1:]:
                path.lineTo(*coords)
            path.closeSubpath()

            item = InteractablePathItem(path)
            item.setPen(QPen(QColor(255, 255, 255)))
            item.setBrush(QBrush(QColor(255, 0, 255, 127)))
            self.scene.addItem(item)

        # Set view background color
        self.view.setBackgroundBrush(QColor(10, 10, 20))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        window_size = self.size()
        self.view.resize(window_size.width() - 40, window_size.height() - 80)

    def updateCursorPositionLabel(self, x, y):
        # You can convert the cursor position from scene coordinates to DXF coordinates if needed
        self.cursor_position_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
