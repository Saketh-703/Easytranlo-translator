from gtts import gTTS
import io
from modules.translation_module import SUPPORTED_LANGUAGES

def generate_audio(text: str, target_lang_display: str) -> bytes:
    if not text.strip():
        return None
        
    # Get the standard ISO code (e.g., 'hi' for Hindi, 'te' for Telugu)
    lang_code = SUPPORTED_LANGUAGES.get(target_lang_display, "en")
    
    try:
        # gTTS perfectly accepts standard ISO codes
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        return audio_bytes.getvalue()
    except Exception as e:
        print(f"TTS Error: {e}")
        return None