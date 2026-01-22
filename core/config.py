import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    'hotkey_translate': 'q',
    'hotkey_toggle': 'h',
    'overlay_opacity': 90,     # Mặc định nền đậm (90%) để che chữ cũ
    'text_color': '#ffffff',   # Mặc định chữ Trắng
    'font_size': 13,            # Mặc định cỡ chữ 13
    'target_lang': 'vi'
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge để đảm bảo luôn có đủ các key mới nếu file cũ thiếu
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)