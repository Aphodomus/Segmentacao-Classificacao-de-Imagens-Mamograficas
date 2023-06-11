import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QFileDialog, QWidget
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
from pathlib import Path
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import cv2
import numpy as np

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
        # Set configuration for main window
        super(MainWindow, self).__init__()
        self.viewer = PhotoViewer(self)
        self.setStyleSheet("QMainWindow::titleBar { background-color: blue; }")
        
        # Create layout for Image Viewer
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        
        self.ui = uic.loadUi("sidebar3.ui", self)
        
        # Hide the slidebar when first init
        self.ui.icon_only_widget.hide()
        self.ui.home_btn_2.setChecked(True)
        
        # Read file when click button folder
        self.button = self.findChild(QPushButton, 'user_btn')
        self.button.clicked.connect(self.open_image)
        
        # Set Image Viewer into widget
        self.widget = self.findChild(QWidget, 'widget_image')
        self.widget.setLayout(VBlayout)
        
        # Slider config min max
        self.ui.horizontalSlider_min.valueChanged.connect(self.number_change_min)
        self.ui.horizontalSlider_max.valueChanged.connect(self.number_change_max)
        self.value_min = 0
        self.value_max = 0
        
        # Create main pixelmap and original image
        self.pixmap = None
        self.original_image = None
        
        # Reset image to original
        self.ui.dashborad_btn_2.clicked.connect(self.reset_image)
        
    def open_image(self):
        downloads_path = str(Path.home() / "Downloads")
        fname = QFileDialog.getOpenFileName(self, 'Open File', f'''{downloads_path}''', "Image Files (*.png *.tiff *.jpg)")
        self.pixmap = QPixmap(fname[0])
        self.original_image = self.pixmap
        self.viewer.setPhoto(self.pixmap)
        
    def reset_image(self):
        self.pixmap = self.original_image
        self.viewer.setPhoto(self.pixmap)
        
    def number_change_min(self):
        if self.pixmap != None:
            new_value_min = str(self.ui.horizontalSlider_min.value())
            self.ui.label_min.setText(new_value_min)
            self.value_min = new_value_min
            pixmap_window = self.apply_window_level(self.pixmap, float(self.value_min), float(self.value_max))
            self.viewer.setPhoto(pixmap_window)
        
    def number_change_max(self):
        if self.pixmap != None:
            new_value_max = str(self.ui.horizontalSlider_max.value())
            self.ui.label_max.setText(new_value_max)
            self.value_max = new_value_max
            pixmap_window = self.apply_window_level(self.pixmap, float(self.value_min), float(self.value_max))
            self.viewer.setPhoto(pixmap_window)
        
    def apply_window_level(self, pixmap, window_center, window_width):
        # Converte o pixmap em um QImage
        image = pixmap.toImage()

        # Converte o QImage em um numpy array
        w, h = image.width(), image.height()
        data = image.bits().asarray(w * h * 4)
        img_arr = np.asarray(data).reshape(h, w, 4)

        # Remove o canal alpha da imagem (se houver)
        if img_arr.shape[-1] == 4:
            img_arr = img_arr[..., :3]

        # Converte a imagem para escala de cinza (se necessário)
        if img_arr.ndim == 3 and img_arr.shape[-1] == 3:
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)

        # Define os valores mínimo e máximo da janela de visualização
        window_min = window_center - (window_width / 2)
        window_max = window_center + (window_width / 2)

        # Verifica se window_min é igual a window_max
        if window_min == window_max:
            img_arr = np.full_like(img_arr, 255, dtype=np.uint8)
        else:
            # Aplica a janela de visualização à imagem
            img_arr = np.clip(img_arr, window_min, window_max)
            img_arr = (img_arr - window_min) / (window_max - window_min)
            img_arr *= 255

        # Converte a imagem de volta para um QPixmap
        image = QImage(img_arr.astype(np.uint8), w, h, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(image)

        return pixmap
        

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
    window.setWindowTitle("Segmentação e Classificação de Imagens Mamográficas")
    window.setWindowIcon(QIcon('raiox.jpg'))
    window.show()
    
    # If exit application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()