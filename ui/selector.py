from PyQt6.QtWidgets import QWidget, QRubberBand
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize # <--- Thêm QSize

class SelectorWindow(QWidget):
    # Tín hiệu bắn ra tọa độ khi chọn xong
    selection_made = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3)
        self.showFullScreen()
        
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        rect = self.rubberBand.geometry()
        selection = {
            "top": rect.y(), 
            "left": rect.x(), 
            "width": rect.width(), 
            "height": rect.height()
        }
        self.selection_made.emit(selection)
        self.close()