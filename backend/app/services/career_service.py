import json

from app.schemas.career import CareerPlanCreate


ROLE_SKILLS = {
    "ai engineer": {"python", "machine learning", "deep learning", "apis", "sql", "mlops"},
    "data scientist": {"python", "statistics", "machine learning", "sql", "visualization", "experimentation"},
    "frontend developer": {"html", "css", "javascript", "typescript", "react", "accessibility"},
    "backend developer": {"python", "apis", "sql", "databases", "docker", "system design"},
    "full stack developer": {"react", "typescript", "python", "apis", "sql", "deployment"},
}


def normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def required_skills_for(target_role: str) -> set[str]:
    role = target_role.lower()
    for key, skills in ROLE_SKILLS.items():
        if key in role:
            return skills
    return {"communication", "problem solving", "projects", "portfolio", "interview practice"}


def skill_match(skills: list[str], target_role: str) -> tuple[float, list[str], list[str]]:
    owned = {normalize_skill(skill) for skill in skills if skill.strip()}
    required = required_skills_for(target_role)
    matched = sorted(owned.intersection(required))
    missing = sorted(required.difference(owned))
    score = round((len(matched) / len(required)) * 100, 2) if required else 0
    return score, matched, missing


def build_roadmap(payload: CareerPlanCreate, readiness_score: float) -> list[str]:
    _, _, missing = skill_match(payload.skills, payload.target_role)
    roadmap = [
        f"Clarify your target: {payload.target_role}. Rewrite your resume headline and portfolio around this role.",
        "Build one proof project that solves a real business or career problem end to end.",
        "Prepare a story bank using the STAR method for leadership, conflict, learning, and impact examples.",
    ]
    roadmap.extend([f"Close skill gap: practice {skill} with a small weekly deliverable." for skill in missing[:5]])
    if readiness_score < 55:
        roadmap.append("Spend 2 weeks on foundations before applying widely.")
    elif readiness_score < 75:
        roadmap.append("Start applying selectively while improving portfolio proof.")
    else:
        roadmap.append("Apply aggressively and schedule mock interviews twice per week.")
    return roadmap


def dumps_list(items: list[str]) -> str:
    return json.dumps(items)


def loads_list(value: str) -> list[str]:
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
