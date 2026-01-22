from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QApplication
from PyQt6.QtCore import Qt

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.current_style = {'opacity': 100, 'color': '#ffffff', 'size': 12}
        self.child_labels = []
        
        # Lấy kích thước màn hình để làm giới hạn
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()

    def update_geometry(self, region):
        self.setGeometry(region['left'], region['top'], region['width'], region['height'])
        self.show()

    def update_visuals(self, opacity, text_color, font_size):
        self.current_style['opacity'] = opacity
        self.current_style['color'] = text_color
        self.current_style['size'] = font_size
        self.refresh_labels_style()

    def set_text(self, text):
        for lbl in self.child_labels: lbl.deleteLater()
        self.child_labels.clear()
        lbl = QLabel(self.central_widget)
        lbl.setText(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lbl.setGeometry(0, 0, self.width(), self.height())
        lbl.show()
        self.child_labels.append(lbl)
        self.refresh_labels_style()

    def render_blocks(self, data_list):
        for lbl in self.child_labels: lbl.deleteLater()
        self.child_labels.clear()

        for item in data_list:
            text = item['translated']
            x, y, w, h = item['box']
            
            lbl = QLabel(self.central_widget)
            lbl.setText(text)
            # Căn lề trái cho đoạn văn dễ đọc
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) 
            # BẮT BUỘC xuống dòng
            lbl.setWordWrap(True) 

            # --- TÍNH TOÁN KÍCH THƯỚC AN TOÀN ---
            # 1. Chiều rộng: Mở rộng thêm chút xíu so với gốc
            final_w = w + 30
            
            # 2. Đặt vị trí và chiều rộng để tính chiều cao
            # Đảm bảo không bị tràn ra ngoài lề phải màn hình
            final_x = min(x - 10, self.screen_width - final_w - 5)
            final_x = max(0, final_x) # Cũng không được âm

            lbl.setGeometry(final_x, y, final_w, 50) # Chiều cao tạm
            lbl.adjustSize() # Yêu cầu tính toán lại
            
            req_h = lbl.height()
            
            # 3. Chiều cao cuối cùng: Lấy cái lớn hơn (gốc vs mới) + padding
            final_h = max(h, req_h) + 15
            
            # Cập nhật lại lần cuối
            lbl.setGeometry(final_x, y - 5, final_w, final_h)
            
            lbl.show()
            self.child_labels.append(lbl)

        self.refresh_labels_style()

    def refresh_labels_style(self):
        opacity = self.current_style['opacity']
        color = self.current_style['color']
        size = self.current_style['size']
        opacity = max(0, min(100, opacity))
        alpha = int(opacity * 255 / 100)
        bg_color = f"rgba(20, 20, 20, {alpha})"

        style = f"""
            QLabel {{
                background-color: {bg_color};
                color: {color};
                font-family: 'Segoe UI', sans-serif;
                font-size: {size}pt;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px; /* Padding lớn để chữ không sát mép */
            }}
        """
        for lbl in self.child_labels:
            lbl.setStyleSheet(style)