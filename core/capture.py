import mss
import numpy as np
from PIL import Image

def take_screenshot(region):
    """
    Chụp màn hình tại vùng chỉ định.
    region: dict {'top', 'left', 'width', 'height'}
    Trả về: PIL Image
    """
    with mss.mss() as sct:
        # MSS chụp ảnh trả về định dạng BGRA
        sct_img = sct.grab(region)
        
        # Convert sang PIL Image (RGB) để MangaOCR dùng được
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img