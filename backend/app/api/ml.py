from fastapi import APIRouter, BackgroundTasks

from app.schemas.career import ReadinessPredictRequest, ReadinessPredictResponse
from app.services.ml_service import predict_readiness
from app.services.realtime_service import realtime_hub

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/readiness", response_model=ReadinessPredictResponse)
def readiness(payload: ReadinessPredictRequest, background_tasks: BackgroundTasks):
    score, label = predict_readiness(
        payload.experience_years,
        payload.projects_count,
        payload.skill_match_percent,
        payload.interview_confidence,
    )
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "ml_readiness",
            "title": "ML readiness refreshed",
            "detail": f"Prediction says {label}.",
            "score": score,
        },
    )
    return {"readiness_score": score, "label": label}
