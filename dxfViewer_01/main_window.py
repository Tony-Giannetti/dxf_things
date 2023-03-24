from PyQt5.QtWidgets import QMainWindow, QPushButton, QGraphicsView, QGraphicsScene, QLabel, QWidget, QVBoxLayout, QSpinBox, QColorDialog, QFileDialog
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QBrush
from PyQt5.QtCore import Qt
import ezdxf
import shapely.geometry as geom
import shapely.ops as ops
from shapely.affinity import rotate
from custom_graphics_view import CustomGraphicsView
from interactable_path_item import InteractablePathItem



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

        load_dxf_button = QPushButton('Load DXF', self)
        load_dxf_button.move(200, 20)
        load_dxf_button.clicked.connect(self.load_dxf)

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

        # Set view background color
        self.view.setBackgroundBrush(QColor(10, 10, 20))
        
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        window_size = self.size()
        self.view.resize(window_size.width() - 40, window_size.height() - 80)

    def updateCursorPositionLabel(self, x, y):
        # You can convert the cursor position from scene coordinates to DXF coordinates if needed
        self.cursor_position_label.setText(f"X: {x:.2f}, Y: {y:.2f}")