import sys
import time
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QFileDialog, QWidget
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
from pathlib import Path
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import cv2
import numpy as np
from PIL import Image, ImageQt
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input

from sidebar_ui import Ui_MainWindow

class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)
    inicialVmax = 0
    inicialVmin = 0

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
        self.model_classify_binary = load_model('../train_model/model_weights/best_segmented_2_classes.hdf5')
        self.model_classify_multiclass = load_model('../train_model/model_weights/best_segmented_4_classes.hdf5')
        self.previsao = "0"
        self.precisao = "0"
        self.tempo = "0"
        
        # Create Photoviewer
        self.viewer = PhotoViewer(self)
        
        # Create layout for Image Viewer
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        
        self.ui = uic.loadUi("interface.ui", self)
        
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
        self.value_max = 128
        
        # Set values
        self.ui.label_min.setText(str(0))
        self.ui.label_max.setText(str(128))
        self.ui.accuracy.setText(self.previsao)
        self.ui.precision.setText(self.precisao)
        self.ui.f1score.setText(self.tempo)
        
        # Create main pixelmap and original image
        self.pixmap = None
        self.original_image = None
        
        # Reset image to original
        self.ui.reset_image.clicked.connect(self.apply_reset_image)
        
        # Apply widowing
        self.ui.windowing.clicked.connect(self.apply_windowing)
        
        # Apply segmentation
        self.ui.segmentation.clicked.connect(self.apply_segmentation)
        
        # Apply classification binary
        self.ui.classification.clicked.connect(self.apply_classification_binary)
        
        # Apply classification multiclass
        self.ui.classification_2.clicked.connect(self.apply_classification_multiclass)
    
    # Function to open image
    def open_image(self):
        downloads_path = str(Path.home() / "Downloads")
        fname = QFileDialog.getOpenFileName(self, 'Open File', f'''{downloads_path}''', "Image Files (*.png *.tiff *.jpg)")
        self.pixmap = QPixmap(fname[0])
        self.original_image = self.pixmap
        self.viewer.setPhoto(self.pixmap)
    
    # Reset image to initial config
    def apply_reset_image(self):
        self.pixmap = self.original_image
        self.viewer.setPhoto(self.pixmap)
        self.ui.accuracy.setText(self.previsao)
        self.ui.precision.setText(self.precisao)
        self.ui.f1score.setText(self.tempo)
        self.ui.horizontalSlider_min.setValue(0)
        self.ui.horizontalSlider_max.setValue(128)
        self.ui.label_min.setText(str(0))
        self.ui.label_max.setText(str(128))
        
    # Crop the image
    def crop_image(self, image):
        # Get the dimensions of the image
        height, width = image.shape[:2]

        # Define the coordinates of the region of interest (ROI)
        x = 15
        y = 15
        crop_width = width - 30
        crop_height = height - 30
        
        return image[y:y+crop_height, x:x+crop_width]

    # Find the optimal gamma for the image
    def find_optimal_gamma(self, image):
        # Calculate average of pixels
        mean = np.mean(image)

        # Return the optimal gamma number for this image
        return np.log(mean) / np.log(512)

    # Identify the largest object in the image
    def biggest_object(self, image):
        # Perform labeling of connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(image)

        # Find the index of the largest object (excluding the background)
        largest_label = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1

        # Create a mask only for the largest object
        return np.uint8(labels == largest_label) * 255

    # Segment a image
    def segment_image(self, image):
        # Crop image, removing 15 pixels from the edges
        cropped = self.crop_image(image)
        
        # Set the ideal gamma
        gamma = self.find_optimal_gamma(image)
 
        # Apply gamma and Otsu transformation if necessary, otherwise apply only Threhold Binary
        if gamma >= 0.6:
            gamma_corrected = np.power(cropped / 255.0, gamma)
            image_filtered = np.uint8(gamma_corrected * 255)
            _, result = cv2.threshold(image_filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            image_filtered = cropped
            _, result = cv2.threshold(image_filtered, 1, maxval=255, type=cv2.THRESH_BINARY)
            
        # Largest object in the image (breast)
        image_biggest = self.biggest_object(result)
        
        # Match the mask of the largest object with the original cropped image
        return cv2.bitwise_and(cropped, cropped, mask=image_biggest)
    
    # Convert qpixmap to array
    def qpixmap_to_nparray(self, qpixmap):
        # Convert QPixmap to QImage
        qimage = qpixmap.toImage()

        # Convert QImage to PIL Image
        image = Image.fromqpixmap(qimage)

        # Convert PIL Image to NumPy array
        return np.array(image)
    
    # Convert array to pixmap
    def nparray_to_qpixmap(self, image):
        # Convert the NumPy array to a QImage
        height, width = image.shape
        qimage = QImage(image.data, width, height, width, QImage.Format_Grayscale8)

        # Convert the QImage to a QPixmap
        return QPixmap.fromImage(qimage)
    
    # array to cvimage
    def nparray_to_cvimage(self, np_array):
        # Convert NumPy array to OpenCV image
        return cv2.cvtColor(np_array, cv2.COLOR_RGB2GRAY)
    
    # Apply segmentation, if exist a image
    def apply_segmentation(self):
        if self.pixmap != None:
            np_array = self.qpixmap_to_nparray(self.pixmap)
            image = self.nparray_to_cvimage(np_array)
            segmented_image = self.segment_image(image)
            pixmap_segmented = self.nparray_to_qpixmap(segmented_image)
            self.pixmap = pixmap_segmented
            self.viewer.setPhoto(self.pixmap)
    
    # Apply windowing, if exist a image
    def apply_windowing(self):
        if self.pixmap != None:
            image = self.pixmap
            pixmap_window = self.apply_window_level(image)
            self.pixmap = pixmap_window
            self.viewer.setPhoto(self.pixmap)      
    
    # Change min value of windowing
    def number_change_min(self):
        if self.pixmap != None:
            new_value_min = str(self.ui.horizontalSlider_min.value())
            self.ui.label_min.setText(new_value_min)
            self.value_min = new_value_min
    
    # Change max value of windowing
    def number_change_max(self):
        if self.pixmap != None:
            new_value_max = str(self.ui.horizontalSlider_max.value())
            self.ui.label_max.setText(new_value_max)
            self.value_max = new_value_max
    
    # Use binary classifier
    def classify_binary(self, image):
        image = cv2.resize(image, (224, 224))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Converter imagem em escala de cinza para RGB
        image_rgb = np.expand_dims(image_rgb, axis=0)
        image_rgb = preprocess_input(image_rgb)
        
        start_time = time.time()  # Registrar o tempo inicial
        prediction = self.model_classify_binary.predict(image_rgb)
        end_time = time.time()  # Registrar o tempo final
        elapsed_time = end_time - start_time  # Calcular o tempo decorrido
    
        class_names = ['I', 'III']
        predicted_class = np.argmax(prediction[0])
        predicted_label = class_names[predicted_class]
        accuracy = prediction[0][predicted_class]
        
        self.ui.accuracy.setText(predicted_label)
        self.ui.precision.setText(str(f'{round(accuracy * 100, 2)}%'))
        self.ui.f1score.setText(str(f'{round(elapsed_time, 2)}s'))
    
    # Use multiclass classifier
    def classify_multiclass(self, image):
        image = cv2.resize(image, (224, 224))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Converter imagem em escala de cinza para RGB
        image_rgb = np.expand_dims(image_rgb, axis=0)
        image_rgb = preprocess_input(image_rgb)
        
        start_time = time.time()  # Registrar o tempo inicial
        prediction = self.model_classify_multiclass.predict(image_rgb)
        end_time = time.time()  # Registrar o tempo final
        elapsed_time = end_time - start_time  # Calcular o tempo decorrido
    
        class_names = ['I', 'II', 'III', 'IV']
        predicted_class = np.argmax(prediction[0])
        predicted_label = class_names[predicted_class]
        accuracy = prediction[0][predicted_class]
        
        self.ui.accuracy.setText(predicted_label)
        self.ui.precision.setText(str(f'{round(accuracy * 100, 2)}%'))
        self.ui.f1score.setText(str(f'{round(elapsed_time, 2)}s'))
    
    # Apply binary model
    def apply_classification_binary(self):
        if self.pixmap != None:
            np_array = self.qpixmap_to_nparray(self.pixmap)
            image = self.nparray_to_cvimage(np_array)
            self.classify_binary(image)
    
    # Apply multiclass model    
    def apply_classification_multiclass(self):
        if self.pixmap != None:
            np_array = self.qpixmap_to_nparray(self.pixmap)
            image = self.nparray_to_cvimage(np_array)
            self.classify_multiclass(image)
    
    # Change image to windowing
    def apply_window_level(self, pixmap):
        minV = round(self.ui.horizontalSlider_min.value() / 2)
        maxV = round(128 + self.ui.horizontalSlider_max.value() / 2 )
        # Convert the QImage to a numpy array
        qImage = pixmap.toImage()
        QImgem2 = qImage

        # Convert the QImage to a numpy array
        w, h = qImage.width(), qImage.height()
        data = qImage.bits().asarray(w * h * 4)
        arr = np.asarray(data).reshape(h, w, 4)
        # Convert the array to an image object using the Pillow library
        adjusted_image = np.clip(arr, minV, maxV)

        img = Image.fromarray(adjusted_image)

        # Convert the Pillow image to a QImage
        qimg = ImageQt.toqimage(img)

        # Check if the conversion was successful
        if not qimg.isNull():
            pixmap = QPixmap.fromImage(qimg)
        else:
            pixmap = QPixmap.fromImage(QImgem2)
        return pixmap
        
# Main function
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