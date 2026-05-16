from fastapi import APIRouter, BackgroundTasks

from app.schemas.career import ChatMessage, ChatResponse
from app.services.ai_service import career_chat
from app.services.realtime_service import realtime_hub

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatMessage, background_tasks: BackgroundTasks):
    result = career_chat(payload.message, payload.target_role)
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "coach",
            "title": "AI coach responded",
            "detail": f"{len(result['recommended_actions'])} recommended actions created.",
            "score": None,
        },
    )
    return result
