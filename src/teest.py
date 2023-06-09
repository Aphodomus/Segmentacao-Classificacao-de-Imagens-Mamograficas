import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Carrega a imagem em escala de cinza
        img = cv2.imread('geek.png', cv2.IMREAD_GRAYSCALE)

        # Cria um pixmap a partir da imagem
        qimg = QImage(img, img.shape[1], img.shape[0], QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimg)

        # Cria um QLabel para exibir a imagem original
        self.label_original = QLabel(self)
        self.label_original.setPixmap(pixmap)
        self.label_original.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label_original)

        # Cria um QLabel para exibir a imagem com ajuste de janela
        self.label_window = QLabel(self)
        self.label_window.setAlignment(Qt.AlignCenter)

        # Aplica o ajuste de janela na imagem e atualiza o QLabel correspondente
        pixmap_window = self.apply_window_level(pixmap, 128, 64)
        self.label_window.setPixmap(pixmap_window)

        # Adiciona os QLabel à janela principal
        self.setCentralWidget(self.label_original)
        self.statusBar().addWidget(self.label_window)

    def apply_window_level(self, pixmap, window_center, window_width):
        # Converte o pixmap em uma imagem numpy
        img = QPixmap.toImage(pixmap).convertToFormat(QImage.Format_Grayscale8)
        w, h = img.width(), img.height()
        data = img.bits().asarray(w * h)

        # Reshape e normaliza os valores de pixel para o intervalo [0, 1]
        img_arr = np.asarray(data).reshape(h, w).astype(np.float32)
        img_arr /= 255.

        # Define os valores mínimo e máximo da janela de visualização
        window_min = window_center - (window_width / 2)
        window_max = window_center + (window_width / 2)

        # Aplica a janela de visualização à imagem
        img_arr = np.clip(img_arr, window_min, window_max)
        img_arr = (img_arr - window_min) / (window_max - window_min)
        img_arr *= 255

        # Converte a imagem de volta para um QPixmap
        img = QImage(img_arr.astype(np.uint8), w, h, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(img)

        return pixmap


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()