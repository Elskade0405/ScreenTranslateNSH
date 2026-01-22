from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
from core.translator import translate_text

class TranslationWorker(QThread):
    finished_data_signal = pyqtSignal(list) 

    def __init__(self, img_pil, ocr_engine, target_lang='vi'):
        super().__init__()
        self.img_pil = img_pil
        self.ocr_engine = ocr_engine
        self.target_lang = target_lang

    def run(self):
        if self.img_pil is None: return

        img_np = np.array(self.img_pil)
        
        # Upscale ảnh nếu quá nhỏ
        height, width = img_np.shape[:2]
        scale_factor = 1.0
        if height < 50: 
            scale_factor = 2.0
            img_np = cv2.resize(img_np, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

        # 1. Lấy dữ liệu OCR thô (Từng dòng lẻ)
        raw_data = self.ocr_engine.extract_text_and_coords(img_np)
        
        # Nếu scale ảnh thì phải chia toạ độ về như cũ
        if scale_factor != 1.0:
            for item in raw_data:
                x, y, w, h = item['box']
                item['box'] = (int(x/scale_factor), int(y/scale_factor), int(w/scale_factor), int(h/scale_factor))

        # 2. GỘP CÁC DÒNG LẺ THÀNH ĐOẠN VĂN (CLUSTERING)
        grouped_data = self.group_lines(raw_data)

        final_results = []
        for item in grouped_data:
            paragraph_text = item['text']
            box = item['box']
            
            # --- QUAN TRỌNG: Truyền ngôn ngữ đích vào hàm dịch ---
            translated = translate_text(paragraph_text, dest_lang=self.target_lang)
            # -----------------------------------------------------
            
            final_results.append({
                'original': paragraph_text,
                'translated': translated,
                'box': box
            })

        self.finished_data_signal.emit(final_results)
        

    def group_lines(self, raw_data):
        """
        Thuật toán gom nhóm:
        - Nếu dòng dưới cách dòng trên một khoảng nhỏ (gap < chiều cao dòng) -> Cùng 1 đoạn.
        - Nếu cách xa -> Đoạn mới.
        """
        if not raw_data:
            return []

        # Sắp xếp các dòng từ trên xuống dưới theo trục Y
        sorted_lines = sorted(raw_data, key=lambda k: k['box'][1])
        
        groups = []
        current_group = [sorted_lines[0]]
        
        for i in range(1, len(sorted_lines)):
            current_line = sorted_lines[i]
            prev_line = current_group[-1]
            
            # Lấy thông số toạ độ
            _, y_curr, _, h_curr = current_line['box']
            _, y_prev, _, h_prev = prev_line['box']
            
            # Tính khoảng cách giữa đáy dòng trên và đỉnh dòng dưới
            gap = y_curr - (y_prev + h_prev)
            
            # Ngưỡng cho phép: Nếu khoảng cách nhỏ hơn 1.2 lần chiều cao dòng -> Gộp
            # (Bạn có thể chỉnh số 1.2 này nếu muốn gom mạnh tay hơn)
            threshold = h_prev * 1.2
            
            if gap < threshold:
                current_group.append(current_line)
            else:
                # Kết thúc nhóm cũ, lưu lại
                groups.append(self.merge_group_to_block(current_group))
                # Tạo nhóm mới
                current_group = [current_line]
        
        # Lưu nhóm cuối cùng
        if current_group:
            groups.append(self.merge_group_to_block(current_group))
            
        return groups

    def merge_group_to_block(self, group_list):
        """Hàm phụ trợ để gộp text và tính toạ độ bao quanh (Bounding Box)"""
        # Gộp text: Nối bằng dấu cách
        combined_text = " ".join([item['text'] for item in group_list])
        
        # Tính toạ độ bao quanh (Min X, Min Y, Max Right, Max Bottom)
        xs = [item['box'][0] for item in group_list]
        ys = [item['box'][1] for item in group_list]
        rights = [item['box'][0] + item['box'][2] for item in group_list]
        bottoms = [item['box'][1] + item['box'][3] for item in group_list]
        
        min_x = min(xs)
        min_y = min(ys)
        max_right = max(rights)
        max_bottom = max(bottoms)
        
        new_w = max_right - min_x
        new_h = max_bottom - min_y
        
        return {
            'text': combined_text,
            'box': (min_x, min_y, new_w, new_h)
        }