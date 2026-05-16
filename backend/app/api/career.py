from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.career import CareerPlan
from app.schemas.career import CareerPlanCreate, CareerPlanOut
from app.services.career_service import build_roadmap, dumps_list, loads_list, skill_match
from app.services.ml_service import predict_readiness
from app.services.realtime_service import realtime_hub

router = APIRouter(prefix="/career", tags=["career"])


@router.post("/plan", response_model=CareerPlanOut)
def create_plan(payload: CareerPlanCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    skill_score, _, _ = skill_match(payload.skills, payload.target_role)
    readiness_score, _ = predict_readiness(
        payload.experience_years,
        payload.projects_count,
        skill_score,
        payload.interview_confidence,
    )
    roadmap = build_roadmap(payload, readiness_score)
    plan = CareerPlan(
        name=payload.name,
        current_role=payload.current_role,
        target_role=payload.target_role,
        skills=dumps_list(payload.skills),
        readiness_score=readiness_score,
        roadmap=dumps_list(roadmap),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    background_tasks.add_task(
        realtime_hub.broadcast,
        {
            "type": "career_plan",
            "title": "Career roadmap generated",
            "detail": f"{payload.target_role} plan is ready with {len(roadmap)} roadmap moves.",
            "score": readiness_score,
        },
    )
    return CareerPlanOut(
        id=plan.id,
        name=plan.name,
        current_role=plan.current_role,
        target_role=plan.target_role,
        skills=loads_list(plan.skills),
        readiness_score=plan.readiness_score,
        roadmap=loads_list(plan.roadmap),
    )


@router.get("/plans", response_model=list[CareerPlanOut])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(CareerPlan).order_by(CareerPlan.id.desc()).limit(20).all()
    return [
        CareerPlanOut(
            id=plan.id,
            name=plan.name,
            current_role=plan.current_role,
            target_role=plan.target_role,
            skills=loads_list(plan.skills),
            readiness_score=plan.readiness_score,
            roadmap=loads_list(plan.roadmap),
        )
        for plan in plans
    ]
