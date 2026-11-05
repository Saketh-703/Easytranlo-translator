import speech_recognition as sr

SPEECH_LANG_MAP = {
    "English": "en-US", "Hindi": "hi-IN", "Telugu": "te-IN",
    "Tamil": "ta-IN", "French": "fr-FR", "Spanish": "es-ES",
    "German": "de-DE", "Japanese": "ja-JP", "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar-SA", "Russian": "ru-RU", "Portuguese": "pt-PT",
    "Italian": "it-IT", "Korean": "ko-KR", "Bengali": "bn-IN"
}

def recognize_speech_from_mic(audio_file, source_lang_display: str) -> str:
    recognizer = sr.Recognizer()
    lang_code = SPEECH_LANG_MAP.get(source_lang_display, "en-US")
    
    try:
        # Process the browser mic recording
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
        text = recognizer.recognize_google(audio_data, language=lang_code)
        return text
    except sr.UnknownValueError:
        return "Error: Could not understand the audio. Please speak clearly."
    except sr.RequestError as e:
        return f"Error: API unavailable; {e}"
    except Exception as e:
        return f"Error: {str(e)}"