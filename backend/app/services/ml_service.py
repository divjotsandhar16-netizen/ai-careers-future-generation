import json
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "readiness_model.json"


def heuristic_score(experience_years: float, projects_count: int, skill_match_percent: float, interview_confidence: int) -> float:
    score = (
        min(experience_years, 8) * 6
        + min(projects_count, 8) * 4
        + skill_match_percent * 0.35
        + interview_confidence * 4
    )
    return round(max(0, min(score, 100)), 2)


def label_for(score: float) -> str:
    if score >= 75:
        return "job-ready"
    if score >= 55:
        return "nearly ready"
    return "foundation building"


def predict_readiness(experience_years: float, projects_count: int, skill_match_percent: float, interview_confidence: int) -> tuple[float, str]:
    if MODEL_PATH.exists():
        model = json.loads(MODEL_PATH.read_text())
        weights = model["weights"]
        score = (
            model["bias"]
            + weights["experience_years"] * experience_years
            + weights["projects_count"] * projects_count
            + weights["skill_match_percent"] * skill_match_percent
            + weights["interview_confidence"] * interview_confidence
        )
        score = round(float(score), 2)
        score = max(0, min(score, 100))
    else:
        score = heuristic_score(experience_years, projects_count, skill_match_percent, interview_confidence)
    return score, label_for(score)
