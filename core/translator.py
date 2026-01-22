from deep_translator import GoogleTranslator

# Thêm tham số dest_lang, mặc định là 'vi'
def translate_text(text, dest_lang='vi'):
    try:
        if not text or len(text.strip()) == 0:
            return ""
        
        # Truyền dest_lang vào đây
        translator = GoogleTranslator(source='auto', target=dest_lang)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Lỗi dịch: {e}")
        return text # Nếu lỗi thì trả về text gốc