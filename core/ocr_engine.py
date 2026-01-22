import os
# Cấu hình môi trường
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_mkldnn"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from paddleocr import PaddleOCR
import logging

logging.getLogger("ppocr").setLevel(logging.ERROR)

class OcrEngine:
    def __init__(self):
        print("Đang tải model PaddleOCR...")
        # Sử dụng model cơ bản
        self.ocr = PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=False) 
        print("Model PaddleOCR đã sẵn sàng!")

    def extract_text_and_coords(self, img_np):
        """
        Trả về danh sách các dòng kèm tọa độ:
        [ {'text': 'Start', 'box': (x, y, w, h)}, ... ]
        """
        try:
            result = self.ocr.ocr(img_np, cls=True)
            data_list = []
            
            if result is not None and len(result) > 0 and result[0] is not None:
                for line in result[0]:
                    # line structure: [ [[x1,y1],[x2,y2],...], ("text", conf) ]
                    box_points = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    if confidence > 0.6:
                        # Tính toán hình chữ nhật bao quanh dòng chữ (x, y, w, h)
                        xs = [pt[0] for pt in box_points]
                        ys = [pt[1] for pt in box_points]
                        x_min = min(xs)
                        y_min = min(ys)
                        x_max = max(xs)
                        y_max = max(ys)
                        
                        w = x_max - x_min
                        h = y_max - y_min
                        
                        # Lưu dữ liệu
                        data_list.append({
                            'text': text,
                            'box': (int(x_min), int(y_min), int(w), int(h))
                        })
            
            return data_list
        except Exception as e:
            print(f"Lỗi OCR: {e}")
            return []