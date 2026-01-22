from PIL import ImageGrab

def take_screenshot(region):
    """
    Chụp ảnh màn hình trong vùng chỉ định.
    region: dictionary {'left': x, 'top': y, 'width': w, 'height': h}
    Trả về: PIL Image object
    """
    x = region['left']
    y = region['top']
    w = region['width']
    h = region['height']
    
    # ImageGrab nhận bbox dạng (left, top, right, bottom)
    bbox = (x, y, x + w, y + h)
    
    # all_screens=True để hỗ trợ nhiều màn hình (nếu có)
    return ImageGrab.grab(bbox=bbox, all_screens=True)