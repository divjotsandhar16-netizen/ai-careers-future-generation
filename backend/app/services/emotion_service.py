import json
from functools import lru_cache

EMOTION_KEYWORDS = {
    "happy": ["happy", "good", "great", "proud", "grateful", "calm"],
    "stressed": ["stressed", "pressure", "overwhelmed", "busy", "deadline", "panic"],
    "anxious": ["anxious", "worried", "nervous", "scared", "afraid", "uncertain"],
    "motivated": ["motivated", "focused", "ready", "discipline", "grind", "improve"],
    "confused": ["confused", "lost", "stuck", "unclear", "don't understand", "idk"],
    "excited": ["excited", "awesome", "amazing", "can't wait", "love", "interesting"],
    "sad": ["sad", "tired", "hopeless", "down", "upset", "hurt"],
}


@lru_cache(maxsize=1)
def get_emotion_pipeline():
    try:
        from transformers import pipeline

        return pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
    except Exception:
        return None


def detect_emotion(text: str) -> dict:
    hf_result = run_hugging_face_emotion(text)
    if hf_result:
        return hf_result
    return fallback_emotion(text)


def run_hugging_face_emotion(text: str) -> dict | None:
    pipeline = get_emotion_pipeline()
    if pipeline is None:
        return None
    try:
        raw = pipeline(text[:1500])
        rows = raw[0] if raw and isinstance(raw[0], list) else raw
        scores = {row["label"].lower(): round(float(row["score"]), 4) for row in rows}
        label, confidence = max(scores.items(), key=lambda item: item[1])
        return normalize_emotion(label, confidence, scores, "huggingface-transformers")
    except Exception:
        return None


def fallback_emotion(text: str) -> dict:
    lower = text.lower()
    scores = {emotion: 0.05 for emotion in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower:
                scores[emotion] += 0.25
    label, confidence = max(scores.items(), key=lambda item: item[1])
    confidence = min(confidence, 0.96)
    return normalize_emotion(label, confidence, scores, "local-keyword-fallback")


def normalize_emotion(label: str, confidence: float, scores: dict, source: str) -> dict:
    mapping = {
        "joy": "happy",
        "anger": "stressed",
        "fear": "anxious",
        "sadness": "sad",
        "surprise": "excited",
        "neutral": "motivated",
    }
    emotion = mapping.get(label.lower(), label.lower())
    sentiment = "positive" if emotion in {"happy", "motivated", "excited"} else "negative" if emotion in {"stressed", "anxious", "sad"} else "neutral"
    tone = "supportive" if emotion in {"sad", "anxious", "stressed", "confused"} else "energetic" if emotion in {"happy", "excited", "motivated"} else "balanced"
    return {
        "emotion": emotion,
        "sentiment": sentiment,
        "tone": tone,
        "confidence": round(confidence, 4),
        "scores": scores,
        "source": source,
        "recommendation": recommendation_for(emotion),
    }


def recommendation_for(emotion: str) -> str:
    if emotion in {"anxious", "stressed"}:
        return "Use a calmer coaching tone, break work into smaller steps, and suggest one immediate action."
    if emotion == "confused":
        return "Explain with simpler structure, examples, and checkpoints."
    if emotion == "sad":
        return "Respond with encouragement first, then suggest a lightweight recovery step."
    if emotion in {"motivated", "excited"}:
        return "Give a more ambitious plan and momentum-based challenge."
    return "Use a balanced professional coaching style."


def dumps_scores(scores: dict) -> str:
    return json.dumps(scores)
