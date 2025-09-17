from typing import List, Tuple
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TextClassificationPipeline,
)

# --- Emotion model (GoEmotions, loaded once) ---
_EMOTION_MODEL = "SamLowe/roberta-base-go_emotions"
_emo_tokenizer = AutoTokenizer.from_pretrained(_EMOTION_MODEL)
_emo_model = AutoModelForSequenceClassification.from_pretrained(_EMOTION_MODEL)
_emotion_pipe = TextClassificationPipeline(
    model=_emo_model,
    tokenizer=_emo_tokenizer,
    return_all_scores=True,
    function_to_apply="sigmoid",  # multilabel
)

# Emojis per GoEmotions label
EMOJI_MAP = {
    "admiration": "👏",
    "amusement": "😄",
    "anger": "😠",
    "annoyance": "😒",
    "approval": "👍",
    "caring": "🤗",
    "confusion": "😕",
    "curiosity": "🤔",
    "desire": "😍",
    "disappointment": "😞",
    "disapproval": "👎",
    "disgust": "🤢",
    "embarrassment": "😳",
    "excitement": "🤩",
    "fear": "😨",
    "gratitude": "🙏",
    "grief": "😢",
    "joy": "😊",
    "love": "❤️",
    "nervousness": "😬",
    "optimism": "🌤️",
    "pride": "🦁",
    "realization": "💡",
    "relief": "😮‍💨",
    "remorse": "😔",
    "sadness": "😢",
    "surprise": "😮",
    "neutral": "😐",
}

# Labels ES/EN (mapped from GoEmotions' English keys)
EMOTION_LABELS_ES = {
    "admiration": "admiración",
    "amusement": "diversión",
    "anger": "ira",
    "annoyance": "molestia",
    "approval": "aprobación",
    "caring": "afecto",
    "confusion": "confusión",
    "curiosity": "curiosidad",
    "desire": "deseo",
    "disappointment": "decepción",
    "disapproval": "desaprobación",
    "disgust": "asco",
    "embarrassment": "vergüenza",
    "excitement": "entusiasmo",
    "fear": "temor",
    "gratitude": "gratitud",
    "grief": "duelo",
    "joy": "alegría",
    "love": "amor",
    "nervousness": "nerviosismo",
    "optimism": "optimismo",
    "pride": "orgullo",
    "realization": "revelación",
    "relief": "alivio",
    "remorse": "remordimiento",
    "sadness": "tristeza",
    "surprise": "sorpresa",
    "neutral": "neutral",
}
EMOTION_LABELS_EN = {
    "admiration": "admiration",
    "amusement": "amusement",
    "anger": "anger",
    "annoyance": "annoyance",
    "approval": "approval",
    "caring": "caring",
    "confusion": "confusion",
    "curiosity": "curiosity",
    "desire": "desire",
    "disappointment": "disappointment",
    "disapproval": "disapproval",
    "disgust": "disgust",
    "embarrassment": "embarrassment",
    "excitement": "excitement",
    "fear": "fear",
    "gratitude": "gratitude",
    "grief": "grief",
    "joy": "joy",
    "love": "love",
    "nervousness": "nervousness",
    "optimism": "optimism",
    "pride": "pride",
    "realization": "realization",
    "relief": "relief",
    "remorse": "remorse",
    "sadness": "sadness",
    "surprise": "surprise",
    "neutral": "neutral",
}


def detect_emotions(
    text: str, top_k: int = 3, threshold: float = 0.30
) -> List[Tuple[str, float]]:
    """
    Detect emotions (multilabel). Return top-k labels above threshold (or top-1 fallback).
    """
    if not text:
        return []
    scores = _emotion_pipe(text)[0]
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)
    picked = [
        (s["label"], float(s["score"])) for s in scores if s["score"] >= threshold
    ]
    if not picked:
        picked = [(scores[0]["label"], float(scores[0]["score"]))]
    return picked[:top_k]


def format_emotions(emolist, ui_lang: str) -> str:
    """
    Format emotions using user's chosen UI language ("es" or "en").
    Example: "joy 😊 (0.91)" or "alegría 😊 (0.91)"
    """
    labels = EMOTION_LABELS_ES if ui_lang == "es" else EMOTION_LABELS_EN
    parts = []
    for label, score in emolist:
        text_label = labels.get(label, label)
        emoji = EMOJI_MAP.get(label, "🎭")
        parts.append(f"{text_label} {emoji} ({score:.2f})")
    return ", ".join(parts)
