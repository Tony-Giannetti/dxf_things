import sys
import ezdxf
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 1000, 700)
        self.setWindowTitle('DXF Reader')

        # Add open file button
        button = QPushButton('Open File', self)
        button.move(20, 20)
        button.clicked.connect(self.openFile)

        # Create tree widget for displaying entity information
        self.tree_widget = QTreeWidget(self)
        self.tree_widget.move(20, 60)
        self.tree_widget.resize(760, 520)
        self.tree_widget.setHeaderLabels(['Type', 'Start Point', 'End Point', 'Center Point'])

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', "DXF files (*.dxf)")
        if filename:
            print(f"Opening {filename}")
            doc = ezdxf.readfile(filename)

            # Clear tree widget
            self.tree_widget.clear()

            # Loop through entities in DXF file and add to tree widget
            for entity in doc.entities:
                item = QTreeWidgetItem(self.tree_widget)
                item.setText(0, entity.dxftype())
                if entity.dxftype() == 'LINE':
                    item.setText(1, f"{entity.dxf.start}")
                    item.setText(2, f"{entity.dxf.end}")
                elif entity.dxftype() == 'CIRCLE':
                    item.setText(3, f"{entity.dxf.center}")
                elif entity.dxftype() == 'LWPOLYLINE':
                    print("Polyline found!")

            # Expand all items in tree widget
            self.tree_widget.expandAll()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
