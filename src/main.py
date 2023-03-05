import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
from pathlib import Path
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets

from sidebar_ui import Ui_MainWindow

class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.icon_only_widget.hide()
        self.ui.home_btn_2.setChecked(True)
        
        # Read file when click button folder
        self.button = self.findChild(QPushButton, 'user_btn')
        self.button.clicked.connect(self.open_image)
        
        # Load default image
        self.current_file = "default.png"
        self.pixmap = QPixmap(self.current_file)
        self.pixmap = self.pixmap.scaled(self.width(), self.height())
        self.label = self.findChild(QLabel, 'label')
        self.label.setPixmap(self.pixmap)
        self.label.setMinimumSize(1, 1)
        
    def resizeEvent(self, event):
        try:
            self.pixmap = QPixmap(self.current_file)
        except Exception:
            self.pixmap = QPixmap('default.png')

        self.pixmap = self.pixmap.scaled(self.width(), self.height())
        self.label.setPixmap(self.pixmap)
        self.label.resize(self.width(), self.height())
        
    def open_image(self):
        downloads_path = str(Path.home() / "Downloads")
        filename, _ = QFileDialog.getOpenFileName(self, 'Open File', f'''{downloads_path}''', "Image Files (*.png *.tiff *.jpg)")
        
        if filename != "":
            self.current_file = filename
            self.pixmap = QPixmap(self.current_file)
            self.pixmap = self.pixmap.scaled(self.width(), self.height())
            self.label.setPixmap(self.pixmap)
    
    # Read image
    # def clicker(self):
    #     downloads_path = str(Path.home() / "Downloads")
    #     fname = QFileDialog.getOpenFileName(self, 'Open File', f'''{downloads_path}''', "Image Files (*.png *.tiff *.jpg)")
    #     self.current_file = fname[0]
    #     
    #     self.pixmap = QPixmap(fname[0])
    #     self.pixmap = self.pixmap.scaled(self.width(), self.height())
    #     # Add picture to label
    #     self.label.setPixmap(self.pixmap)
    #     self.label.setMinimumSize(1, 1)
    #     self.label.setMaximumSize(1200, 700)
        

def main():
    # Start Application
    app = QApplication(sys.argv)
    
    # Load Style
    style_file = QFile("style/style.qss")
    style_file.open(QFile.ReadOnly | QFile.Text)
    style_stream = QTextStream(style_file)
    app.setStyleSheet(style_stream.readAll())
    
    # Call main window
    window = MainWindow()
    window.show()
    
    # If exit application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()