from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class SelectionWindow(QWidget):
    # Signal gửi về Main khi chọn xong: trả về dictionary toạ độ
    region_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        # Cấu hình cửa sổ phủ toàn màn hình, không viền, luôn ở trên cùng
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3) # Độ mờ nền (0.3 = mờ 30%)
        
        # Lấy kích thước toàn bộ màn hình (hỗ trợ đa màn hình)
        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geometry)
        
        self.setCursor(Qt.CursorShape.CrossCursor) # Con trỏ hình chữ thập

        self.start_point = None
        self.end_point = None
        self.is_drawing = False

    def paintEvent(self, event):
        # Vẽ hình chữ nhật vùng chọn
        if self.start_point and self.end_point:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2)) # Viền đỏ
            painter.setBrush(QColor(255, 255, 255, 50)) # Bên trong trắng mờ
            
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        # Bắt đầu vẽ
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        # Đang kéo chuột
        if self.is_drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        # Thả chuột -> Kết thúc chọn
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.end_point = event.pos()
            self.is_drawing = False
            self.close() # Đóng cửa sổ chọn

            # Tính toán vùng chọn
            rect = QRect(self.start_point, self.end_point).normalized()
            
            # Chỉ lấy nếu vùng chọn đủ lớn (>10px)
            if rect.width() > 10 and rect.height() > 10:
                region = {
                    'left': rect.x(),
                    'top': rect.y(),
                    'width': rect.width(),
                    'height': rect.height()
                }
                self.region_selected.emit(region) # Gửi toạ độ về Main

    def keyPressEvent(self, event):
        # Bấm ESC để hủy chọn
        if event.key() == Qt.Key.Key_Escape:
            self.close()