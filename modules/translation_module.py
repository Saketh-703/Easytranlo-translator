import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator

SUPPORTED_LANGUAGES = {
    "English": "en", "Hindi": "hi", "Telugu": "te", "Tamil": "ta",
    "French": "fr", "Spanish": "es", "German": "de", "Japanese": "ja",
    "Chinese (Simplified)": "zh-CN", "Arabic": "ar", "Russian": "ru",
    "Portuguese": "pt", "Italian": "it", "Korean": "ko", "Bengali": "bn"
}

MYMEMORY_LANGUAGES = {
    "English": "en-US", "Hindi": "hi-IN", "Telugu": "te-IN",
    "Tamil": "ta-IN", "French": "fr-FR", "Spanish": "es-ES",
    "German": "de-DE", "Japanese": "ja-JP", "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar-SA", "Russian": "ru-RU", "Portuguese": "pt-PT",
    "Italian": "it-IT", "Korean": "ko-KR", "Bengali": "bn-IN"
}

def translate_text(text: str, source_lang_display: str, target_lang_display: str) -> str:
    if not text.strip():
        return ""
    
    # If user selects the same language, just return the text
    if source_lang_display == target_lang_display:
        return text

    src_code = SUPPORTED_LANGUAGES.get(source_lang_display, "en")
    tgt_code = SUPPORTED_LANGUAGES.get(target_lang_display, "en")
    
    # --- METHOD 1: Direct Google API (Fastest & Most Reliable) ---
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_code}&tl={tgt_code}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            translated = "".join([sentence[0] for sentence in data[0] if sentence[0]])
            if translated and translated.strip().lower() != text.strip().lower():
                return translated
    except Exception as e:
        print(f"Direct API failed: {e}")
    
    # --- METHOD 2: deep-translator (Backup 1) ---
    try:
        translator = GoogleTranslator(source=src_code, target=tgt_code)
        result = translator.translate(text)
        if result and result.strip().lower() != text.strip().lower():
            return result
    except Exception as e:
        print(f"Deep Translator failed: {e}")
        
    # --- METHOD 3: MyMemory (Backup 2) ---
    try:
        src_mm = MYMEMORY_LANGUAGES.get(source_lang_display, "en-US")
        tgt_mm = MYMEMORY_LANGUAGES.get(target_lang_display, "en-US")
        translator_mm = MyMemoryTranslator(source=src_mm, target=tgt_mm)
        result = translator_mm.translate(text)
        if result and result.strip().lower() != text.strip().lower():
            return result
    except Exception as e:
        print(f"MyMemory failed: {e}")

    return "⚠️ Translation Failed. Please check your internet connection and try again."