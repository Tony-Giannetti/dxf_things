import sys
from math import sin, cos
import ezdxf
from PyQt5.QtGui import QPen, QColor, QPainter
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QGraphicsScene, QGraphicsView
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPathItem


class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def wheelEvent(self, event):
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

class InteractableLine(QGraphicsLineItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

class InteractableCircle(QGraphicsEllipseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

class InteractableArc(QGraphicsPathItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(1500, 100, 1000, 700)
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
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setInteractive(True)
        self.view.move(20, 60)
        self.view.resize(960, 620)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)


    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', "DXF files (*.dxf)")
        if filename:
            print(f"Opening {filename}")
            doc = ezdxf.readfile(filename)

            # Clear scene
            self.scene.clear()

            # Loop through entities in DXF file and add to scene
            for entity in doc.entities:
                if entity.dxftype() == 'LINE':
                    start_point = entity.dxf.start
                    end_point = entity.dxf.end
                    pen = QPen(QColor(0, 0, 0))
                    line_item = InteractableLine(start_point[0], start_point[1], end_point[0], end_point[1])
                    line_item.setPen(pen)
                    self.scene.addItem(line_item)
                elif entity.dxftype() == 'CIRCLE':
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    pen = QPen(QColor(0, 0, 0))
                    circle_item = InteractableCircle(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
                    circle_item.setPen(pen)
                    self.scene.addItem(circle_item)
                # elif entity.dxftype() == 'ARC':
                #     # Rest of the code for creating arc items
                #     arc_item = InteractableArc(path)
                #     arc_item.setPen(pen)
                #     self.scene.addItem(arc_item)

            # Set view background color
            self.view.setBackgroundBrush(QColor(220, 220, 220))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
