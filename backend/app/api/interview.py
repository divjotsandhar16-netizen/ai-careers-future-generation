from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.career import InterviewSession
from app.schemas.career import (
    InterviewBatchRequest,
    InterviewBatchResponse,
    InterviewEvaluateRequest,
    InterviewEvaluateResponse,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
)
from app.services.interview_service import domain_questions, evaluate_answer, next_question
from app.services.realtime_service import realtime_hub

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/question", response_model=InterviewQuestionResponse)
def question(payload: InterviewQuestionRequest, background_tasks: BackgroundTasks):
    generated = next_question(payload.target_role, payload.difficulty)
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "interview_question",
            "title": "Interview question generated",
            "detail": f"{payload.difficulty.title()} {payload.target_role} practice is ready.",
            "score": None,
        },
    )
    return {"question": generated}


@router.post("/questions", response_model=InterviewBatchResponse)
def questions(payload: InterviewBatchRequest, background_tasks: BackgroundTasks):
    generated = domain_questions(payload.domain, payload.difficulty, payload.count)
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "interview_batch",
            "title": "Interview question set generated",
            "detail": f"{len(generated)} {payload.domain} questions are ready.",
            "score": None,
        },
    )
    return {"domain": payload.domain, "difficulty": payload.difficulty, "questions": generated}


@router.post("/evaluate", response_model=InterviewEvaluateResponse)
def evaluate(payload: InterviewEvaluateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    score, feedback = evaluate_answer(payload.answer)
    row = InterviewSession(
        target_role=payload.target_role,
        question=payload.question,
        answer=payload.answer,
        feedback=feedback,
        score=score,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "interview_score",
            "title": "Interview answer scored",
            "detail": f"{payload.target_role} answer received {round(row.score)}.",
            "score": row.score,
        },
    )
    return {"id": row.id, "score": row.score, "feedback": row.feedback}
