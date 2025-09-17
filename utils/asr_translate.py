from typing import Tuple
from faster_whisper import WhisperModel
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect, DetectorFactory
from lingua import Language, LanguageDetectorBuilder
DetectorFactory.seed = 0  # deterministic results


def detect_lang_text(text: str) -> str:
    """
    Detect language of input text restricted to English/Spanish.
    Returns: 'en' | 'es' | 'other'
    """
    if not text or not text.strip():
        return "other"

    # 1) Try Lingua (recommended)
    try:

        detector = LanguageDetectorBuilder.from_languages(
            Language.ENGLISH, Language.SPANISH
        ).build()

        lang = detector.detect_language_of(text)
        if lang == Language.ENGLISH:
            return "en"
        if lang == Language.SPANISH:
            return "es"

        # Optional: confidence-based decision
        confidences = detector.compute_language_confidence_values(
            text)  # list of ConfidenceValue
        if confidences:
            best = max(confidences, key=lambda c: c.value)
            if best.value >= 0.70:  # tighten threshold for short/noisy texts
                if best.language == Language.ENGLISH:
                    return "en"
                if best.language == Language.SPANISH:
                    return "es"
        return "other"

    except Exception:
        # 2) Fallback to langdetect if Lingua is unavailable
        try:
            code = (detect(text) or "").lower()
            if code.startswith("en"):
                return "en"
            if code.startswith("es"):
                return "es"
            return "other"
        except Exception:
            return "other"


# --- Whisper model (loaded once) ---
# Adjust device/compute if you have GPU: device="cuda", compute_type="float16"
_whisper = WhisperModel("small", device="cpu", compute_type="int8")

# --- MarianMT models (loaded once) ---
_EN_ES_MODEL = "Helsinki-NLP/opus-mt-en-es"
_ES_EN_MODEL = "Helsinki-NLP/opus-mt-es-en"

_tok_en_es = MarianTokenizer.from_pretrained(_EN_ES_MODEL)
_mod_en_es = MarianMTModel.from_pretrained(_EN_ES_MODEL)

_tok_es_en = MarianTokenizer.from_pretrained(_ES_EN_MODEL)
_mod_es_en = MarianMTModel.from_pretrained(_ES_EN_MODEL)


def transcribe_file(file_path) -> Tuple[str, str, float]:
    """
    Transcribe an audio file with automatic language detection.
    Returns (text, lang_code, confidence).
    """
    segments, info = _whisper.transcribe(
        str(file_path),
        language=None,  # auto-detect
        vad_filter=True,
        beam_size=5,
    )
    text = " ".join(seg.text.strip()
                    for seg in segments if getattr(seg, "text", None))
    return (
        text.strip(),
        (info.language or "unknown"),
        float(info.language_probability or 0.0),
    )


def translate_text(detected_lang: str, text: str) -> tuple[str, str]:
    """
    Translate en→es or es→en based on detected language.
    Returns (translated_text, target_lang) or (original, "same") if not es/en.
    """
    if not text:
        return "", "same"
    code = (detected_lang or "").lower()
    try:
        if code.startswith("en"):
            tok, model, target = _tok_en_es, _mod_en_es, "es"
        elif code.startswith("es"):
            tok, model, target = _tok_es_en, _mod_es_en, "en"
        else:
            return text, "same"

        inputs = tok([text], return_tensors="pt",
                     padding=True, truncation=True)
        gen = model.generate(**inputs, max_new_tokens=512)
        out = tok.batch_decode(gen, skip_special_tokens=True)[0]
        return out.strip(), target
    except Exception:
        # If translation fails, return original text
        return text, "same"


def flag_for_lang(code: str) -> str:
    """
    Return a flag emoji for language code.
    """
    code = (code or "").lower()
    if code.startswith("en"):
        return "🇬🇧"
    if code.startswith("es"):
        return "🇪🇸"
    return "🌐"
