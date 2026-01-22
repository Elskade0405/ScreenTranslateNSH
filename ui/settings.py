from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QSlider, 
                             QColorDialog, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class SettingsDialog(QDialog):
    def __init__(self, current_config):
        super().__init__()
        self.setWindowTitle("Cài đặt Giao diện")
        self.setMinimumWidth(400)
        self.new_config = current_config.copy()
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 1. Phím tắt (Giữ nguyên)
        self.txt_translate = QLineEdit(self.new_config.get('hotkey_translate', 'q'))
        form_layout.addRow("Phím Dịch:", self.txt_translate)

        self.txt_toggle = QLineEdit(self.new_config.get('hotkey_toggle', 'h'))
        form_layout.addRow("Phím Ẩn/Hiện:", self.txt_toggle)
        
        # 2. Độ trong suốt (Giữ nguyên)
        self.current_opacity = self.new_config.get('overlay_opacity', 90)
        opacity_layout = QHBoxLayout()
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(self.current_opacity)
        self.slider_opacity.valueChanged.connect(self.update_opacity_label)
        
        self.lbl_opacity_val = QLabel(f"{self.current_opacity}%")
        self.lbl_opacity_val.setFixedWidth(40)
        
        opacity_layout.addWidget(self.slider_opacity)
        opacity_layout.addWidget(self.lbl_opacity_val)
        form_layout.addRow("Độ đậm nền (Opacity):", opacity_layout)

        # 3. [MỚI] Chọn Màu Chữ
        self.current_color = self.new_config.get('text_color', '#ffffff')
        
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("Chọn màu...")
        # Đặt màu nền nút để user dễ hình dung
        self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black; border: 1px solid gray;")
        self.btn_color.clicked.connect(self.choose_color)
        
        color_layout.addWidget(self.btn_color)
        form_layout.addRow("Màu chữ:", color_layout)

        # 4. [MỚI] Chỉnh Cỡ Chữ
        self.spin_font = QSpinBox()
        self.spin_font.setRange(8, 72) # Giới hạn cỡ chữ từ 8 đến 72
        self.spin_font.setValue(int(self.new_config.get('font_size', 13)))
        form_layout.addRow("Cỡ chữ (pt):", self.spin_font)

        layout.addLayout(form_layout)

        # Nút Lưu/Hủy
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Lưu lại")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        
        layout.addLayout(btn_box)
        self.setLayout(layout)

    def update_opacity_label(self, value):
        self.lbl_opacity_val.setText(f"{value}%")

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self, "Chọn màu chữ")
        if color.isValid():
            self.current_color = color.name() # Lưu mã HEX (vd: #ff0000)
            self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black; border: 1px solid gray;")

    def save_settings(self):
        self.new_config['hotkey_translate'] = self.txt_translate.text().strip().lower()
        self.new_config['hotkey_toggle'] = self.txt_toggle.text().strip().lower()
        self.new_config['overlay_opacity'] = self.slider_opacity.value()
        
        # Lưu màu và cỡ chữ mới
        self.new_config['text_color'] = self.current_color
        self.new_config['font_size'] = self.spin_font.value()
        
        self.accept()