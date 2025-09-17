from typing import Dict

# In-memory language preferences (POC). key: user_id -> "es" or "en"
USER_LANG: Dict[int, str] = {}

I18N = {
    "welcome": {
        "en": (
            "👋 Hi! Send me a *voice* or *text* message in English or Spanish and I will return:\n"
            "1) **Transcription / Your text** 📝\n"
            "2) **Translation** 🔁\n"
            "3) **Emotion/intent** 🎭\n\n"
            "Use /help to see options. You can change language with /lang."
        ),
        "es": (
            "👋 ¡Hola! Envíame una *nota de voz* o un *mensaje de texto* en inglés o español y te devolveré:\n"
            "1) **Transcripción / Tu texto** 📝\n"
            "2) **Traducción** 🔁\n"
            "3) **Emoción/Intención** 🎭\n\n"
            "Usa /help para ver opciones. Puedes cambiar el idioma con /lang."
        ),
    },
    "help": {
        "en": (
            "📌 Commands:\n"
            "/start - Welcome\n"
            "/help - This help\n"
            "/about - About this bot\n"
            "/lang - Choose bot language (English/Spanish)\n\n"
            "🎤 Features:\n"
            "- *Voice* (English/Spanish): transcription + translation + emotion.\n"
            "- *Text* (English/Spanish): translation + emotion (emotions computed in English)."
        ),
        "es": (
            "📌 Comandos:\n"
            "/start - Bienvenida\n"
            "/help - Esta ayuda\n"
            "/about - Sobre este bot\n"
            "/lang - Elegir idioma del bot (Español/Inglés)\n\n"
            "🎤 Funciones:\n"
            "- *Voz* (inglés/español): transcripción + traducción + emoción.\n"
            "- *Texto* (inglés/español): traducción + emoción."
        ),
    },
    "about": {
        "en": (
            "🤖 Demo: python-telegram-bot v21 + faster-whisper (ASR) + MarianMT (translation) + "
            "GoEmotions (emotion). Detects language (en/es), transcribes/reads text, translates, and classifies emotions."
        ),
        "es": (
            "🤖 Demo: python-telegram-bot v21 + faster-whisper (ASR) + MarianMT (traducción) + "
            "GoEmotions (emoción). Detecta idioma (es/en), transcribe/lee texto, traduce y clasifica emociones."
        ),
    },
    "choose_lang": {
        "en": "Please choose the bot language:",
        "es": "Elige el idioma del bot:",
    },
    "lang_set": {
        "en": "✅ Language set to English.",
        "es": "✅ Idioma configurado a Español.",
    },
    "unknown_cmd": {
        "en": "Unknown command. Try /help 😉",
        "es": "Comando no reconocido. Prueba /help 😉",
    },
    "no_transcription": {
        "en": "❌ Could not transcribe anything. Please try again.",
        "es": "❌ No pude transcribir nada. Por favor, inténtalo de nuevo.",
    },
    "analysis_skipped": {  # NUEVO: idioma no soportado
        "en": "not processed (analysis skipped).",
        "es": "no procesadas (se omite análisis).",
    },
    "translation_skipped": {
        "en": "ℹ️ Not English/Spanish, translation skipped.",
        "es": "ℹ️ No es inglés/español; se omitió la traducción.",
    },
    "transcription_header": {  # ahora incluye {conf}
        "en": "📝 Transcription {flag} (lang: {lang}, confidence: {conf}%):\n",
        "es": "📝 Transcripción {flag} (idioma: {lang}, confianza: {conf}%):\n",
    },
    "emotion_header": {
        "en": "🎭 Detected emotion(s): {emo}",
        "es": "🎭 Emoción(es) detectada(s): {emo}",
    },
    "you_wrote": {
        "en": "📝 You wrote {flag} ({lang}):\n",
        "es": "📝 Has escrito {flag} (idioma: {lang}):\n",
    },
    "translation_header": {
        "en": "🔁 Translation {flag} ({src}→{tgt}):\n",
        "es": "🔁 Traducción {flag} ({src}→{tgt}):\n",
    },
}


def t(user_id: int, key: str, **kwargs) -> str:
    """
    Resolve template by user language.
    Fallback order: user preference -> Telegram language_code -> English.
    """
    lang_pref = USER_LANG.get(user_id)
    if not lang_pref:
        lang_code = (kwargs.pop("telegram_lang_code", "") or "").lower()
        if lang_code.startswith("es"):
            lang_pref = "es"
        elif lang_code.startswith("en"):
            lang_pref = "en"
        else:
            lang_pref = "en"
    template = I18N.get(key, {}).get(
        lang_pref) or I18N.get(key, {}).get("en", "")
    return template.format(**kwargs)


def get_user_lang(user_id: int, telegram_lang_code: str) -> str:
    """
    Resolve user's preferred UI language ("es" or "en").
    """
    if user_id in USER_LANG:
        return USER_LANG[user_id]
    code = (telegram_lang_code or "").lower()
    if code.startswith("es"):
        return "es"
    if code.startswith("en"):
        return "en"
    return "en"
