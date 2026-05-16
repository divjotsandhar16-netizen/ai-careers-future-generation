import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.career import EmotionEvent, PersonalityReport, User
from app.schemas.intelligence import (
    EmotionAnalyzeRequest,
    EmotionAnalyzeResponse,
    PersonalityPredictRequest,
    PersonalityPredictResponse,
)
from app.services.emotion_service import detect_emotion, dumps_scores
from app.services.personality_service import dumps, predict_personality

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/emotion", response_model=EmotionAnalyzeResponse)
def emotion(payload: EmotionAnalyzeRequest, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    result = detect_emotion(payload.text)
    row = EmotionEvent(
        user_id=user.id if user else None,
        text=payload.text,
        emotion=result["emotion"],
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        scores=dumps_scores(result["scores"]),
    )
    db.add(row)
    db.commit()
    return result


@router.get("/emotion/history")
def emotion_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(EmotionEvent).filter(EmotionEvent.user_id == user.id).order_by(EmotionEvent.id.desc()).limit(30).all()
    return [
        {
            "emotion": row.emotion,
            "sentiment": row.sentiment,
            "confidence": row.confidence,
            "scores": json.loads(row.scores),
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/personality", response_model=PersonalityPredictResponse)
def personality(payload: PersonalityPredictRequest, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    result = predict_personality(payload.model_dump())
    row = PersonalityReport(
        user_id=user.id if user else None,
        personality_type=result["personality_type"],
        communication_style=result["communication_style"],
        learning_style=result["learning_style"],
        career_matches=dumps(result["career_matches"]),
        strengths=dumps(result["strengths"]),
        weaknesses=dumps(result["weaknesses"]),
        scores=dumps(result["scores"]),
    )
    db.add(row)
    db.commit()
    return result
