import os
import sys
import time
import keyboard
import threading

# --- 1. KHU VỰC CẤU HÌNH FIX LỖI (BẮT BUỘC ĐẶT Ở DÒNG ĐẦU) ---
# Giúp chạy ổn định trên Windows, tránh xung đột thư viện và ép chạy CPU
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_mkldnn"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# -------------------------------------------------------------

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QComboBox, QSystemTrayIcon, QMenu, QMessageBox)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject, Qt

# Import các module nội bộ
from core.ocr_engine import OcrEngine
from core.utils import take_screenshot
from core.worker import TranslationWorker
from core.config import load_config, save_config
from ui.selection import SelectionWindow
from ui.overlay import OverlayWindow
from ui.settings import SettingsDialog

# Class trung gian để nhận tín hiệu từ luồng phím tắt về luồng UI
class HotkeySignal(QObject):
    translate_pressed = pyqtSignal()
    toggle_pressed = pyqtSignal()

class ScreenTransApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Tải cấu hình
        self.config = load_config()
        
        # 2. Khởi tạo OCR Engine (Load 1 lần dùng mãi mãi)
        self.ocr_engine = OcrEngine()
        
        # 3. Quản lý vùng chọn và cửa sổ dịch
        self.region_list = []   # Danh sách toạ độ vùng chọn
        self.overlay_list = []  # Danh sách cửa sổ hiển thị bản dịch
        self.active_workers = [] # Quản lý các luồng đang chạy
        self.overlays_visible = True
        
        # 4. Thiết lập tín hiệu phím tắt
        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.translate_pressed.connect(self.run_translation)
        self.hotkey_signal.toggle_pressed.connect(self.toggle_visibility)
        
        # 5. Khởi tạo giao diện
        self.initUI()
        self.setup_tray()
        self.setup_hotkeys()

    def initUI(self):
        self.setWindowTitle("Screen Translator Tool")
        self.setGeometry(100, 100, 350, 250)
        self.setWindowIcon(QIcon("icon.png")) # Nếu bạn có file icon

        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Label trạng thái
        self.lbl_status = QLabel("Sẵn sàng. Hãy thêm vùng dịch!")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Nút Thêm vùng
        btn_add = QPushButton("+ Thêm vùng dịch")
        btn_add.clicked.connect(self.start_selection)
        layout.addWidget(btn_add)

        # Dropdown chọn Ngôn ngữ (Đã sửa lại theo yêu cầu)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Dịch sang: Tiếng Việt", "vi")
        self.combo_mode.addItem("Dịch sang: English", "en")
        
        # Load ngôn ngữ đã lưu từ config
        saved_lang = self.config.get('target_lang', 'vi')
        index = self.combo_mode.findData(saved_lang)
        if index >= 0:
            self.combo_mode.setCurrentIndex(index)
            
        self.combo_mode.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.combo_mode)

        # Nút Dịch Ngay
        btn_trans = QPushButton(f"Dịch ({self.config.get('hotkey_translate', 'q')})")
        btn_trans.clicked.connect(self.run_translation)
        layout.addWidget(btn_trans)

        # Nút Cài đặt
        btn_setting = QPushButton("Cài đặt")
        btn_setting.clicked.connect(self.open_settings)
        layout.addWidget(btn_setting)
        
        # Nút Xóa tất cả vùng
        btn_clear = QPushButton("Xóa tất cả vùng")
        btn_clear.clicked.connect(self.clear_all_regions)
        layout.addWidget(btn_clear)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png")) # Cần file icon.png hoặc dùng icon mặc định hệ thống
        
        menu = QMenu()
        action_show = QAction("Hiện giao diện", self)
        action_show.triggered.connect(self.show)
        action_quit = QAction("Thoát", self)
        action_quit.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(action_show)
        menu.addAction(action_quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def setup_hotkeys(self):
        # Xóa hotkey cũ trước khi đăng ký mới
        keyboard.unhook_all()
        
        key_trans = self.config.get('hotkey_translate', 'q')
        key_toggle = self.config.get('hotkey_toggle', 'h')
        
        try:
            keyboard.add_hotkey(key_trans, lambda: self.hotkey_signal.translate_pressed.emit())
            keyboard.add_hotkey(key_toggle, lambda: self.hotkey_signal.toggle_pressed.emit())
            print(f"Đã đăng ký phím tắt: Dịch[{key_trans}], Ẩn/Hiện[{key_toggle}]")
        except Exception as e:
            print(f"Lỗi đăng ký phím tắt: {e}")

    def change_language(self):
        # Lưu ngôn ngữ được chọn vào config
        selected_lang = self.combo_mode.currentData()
        self.config['target_lang'] = selected_lang
        save_config(self.config)
        self.lbl_status.setText(f"Đã đổi sang: {self.combo_mode.currentText()}")

    def start_selection(self):
        # Ẩn cửa sổ chính để dễ chọn vùng
        self.hide()
        # Tạo cửa sổ chọn vùng phủ toàn màn hình
        self.selection_window = SelectionWindow()
        self.selection_window.region_selected.connect(self.on_region_added)
        self.selection_window.show()

    def on_region_added(self, region):
        # Hiện lại cửa sổ chính
        self.show()
        
        # Lưu vùng chọn
        self.region_list.append(region)
        
        # Tạo Overlay tương ứng với vùng chọn
        new_overlay = OverlayWindow()
        
        # Áp dụng ngay Style từ config (Màu, Cỡ chữ, Độ đậm)
        opacity = self.config.get('overlay_opacity', 90)
        color = self.config.get('text_color', '#ffffff')
        size = self.config.get('font_size', 12)
        new_overlay.update_visuals(opacity, color, size)
        
        # Đặt vị trí
        new_overlay.update_geometry(region)
        new_overlay.set_text(f"Vùng {len(self.region_list)}") # Text tạm
        
        if self.overlays_visible:
            new_overlay.show()
            
        self.overlay_list.append(new_overlay)
        self.lbl_status.setText(f"Đã thêm Vùng {len(self.region_list)}")

    def run_translation(self):
        if not self.region_list:
            self.lbl_status.setText("Chưa có vùng nào để dịch!")
            return

        print("-> Bắt đầu dịch...")
        self.lbl_status.setText("Đang xử lý...")

        # 1. Tạm ẩn các overlay để chụp màn hình sạch
        for ov in self.overlay_list:
            ov.hide()
        
        # Đợi một chút để UI kịp cập nhật (tránh chụp dính overlay đen)
        QApplication.processEvents()
        time.sleep(0.1) 

        # Lấy ngôn ngữ đích
        target_lang = self.config.get('target_lang', 'vi')

        # 2. Duyệt qua từng vùng và tạo luồng xử lý
        for i, region in enumerate(self.region_list):
            try:
                # Chụp ảnh vùng đó
                img = take_screenshot(region)
                
                # Hiện lại khung (nhưng chưa có chữ mới)
                overlay = self.overlay_list[i]
                if self.overlays_visible:
                    overlay.show()
                
                # Khởi tạo Worker
                # Truyền target_lang vào để Worker biết dịch sang tiếng gì
                worker = TranslationWorker(img, self.ocr_engine, target_lang=target_lang)
                
                # Kết nối tín hiệu trả về dữ liệu (List blocks)
                worker.finished_data_signal.connect(lambda data, ov=overlay: self.handle_translation_result(ov, data))
                
                # Dọn dẹp worker khi xong
                worker.finished.connect(lambda w=worker: self.cleanup_worker(w))
                
                self.active_workers.append(worker)
                worker.start()
                
            except Exception as e:
                print(f"Lỗi vùng {i}: {e}")
                
        self.lbl_status.setText("Đang dịch...")

    def handle_translation_result(self, overlay, data_list):
        # Gọi hàm render thông minh trong Overlay
        overlay.render_blocks(data_list)
        self.lbl_status.setText("Hoàn tất!")

    def cleanup_worker(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def toggle_visibility(self):
        self.overlays_visible = not self.overlays_visible
        for ov in self.overlay_list:
            if self.overlays_visible:
                ov.show()
            else:
                ov.hide()
        state = "Hiện" if self.overlays_visible else "Ẩn"
        self.lbl_status.setText(f"Đã {state} tất cả vùng dịch")

    def clear_all_regions(self):
        for ov in self.overlay_list:
            ov.close()
        self.overlay_list.clear()
        self.region_list.clear()
        self.lbl_status.setText("Đã xóa tất cả vùng chọn.")

    def open_settings(self):
        dialog = SettingsDialog(self.config)
        if dialog.exec():
            # Cập nhật config mới
            self.config = dialog.new_config
            save_config(self.config)
            
            # Cập nhật lại phím tắt
            self.setup_hotkeys()
            
            # Cập nhật ngay lập tức giao diện cho các vùng đang mở
            opacity = self.config.get('overlay_opacity', 90)
            color = self.config.get('text_color', '#ffffff')
            size = self.config.get('font_size', 12)
            
            for ov in self.overlay_list:
                ov.update_visuals(opacity, color, size)
            
            print("Đã lưu cài đặt và cập nhật giao diện.")

    def closeEvent(self, event):
        # Xử lý khi bấm nút X cửa sổ
        reply = QMessageBox.question(self, 'Thoát', 
                                     'Bạn có muốn thu nhỏ xuống khay hệ thống không?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.Yes)
        
        if reply == QMessageBox.StandardButton.Yes:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("Screen Translator", "Ứng dụng đang chạy ngầm", QSystemTrayIcon.MessageIcon.Information)
        else:
            keyboard.unhook_all()
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Thiết lập font chữ hệ thống cho đẹp
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = ScreenTransApp()
    window.show()
    
    sys.exit(app.exec())