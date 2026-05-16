import re

from app.services.career_service import ROLE_SKILLS, required_skills_for


ACTION_WORDS = {"built", "created", "led", "improved", "automated", "designed", "launched", "analyzed", "deployed"}
COMMON_SKILLS = {
    "python", "javascript", "typescript", "react", "fastapi", "node", "sql", "postgresql", "sqlite",
    "machine learning", "deep learning", "nlp", "apis", "docker", "aws", "git", "html", "css",
    "data analysis", "visualization", "statistics", "pandas", "scikit-learn", "communication",
    "leadership", "testing", "deployment", "databases", "system design", "accessibility", "mlops",
}
DOMAIN_KEYWORDS = {
    "AI / Machine Learning": {
        "python", "machine learning", "deep learning", "nlp", "model", "training", "inference", "mlops",
        "scikit-learn", "pandas", "classification", "regression", "neural", "embedding", "rag",
    },
    "Data Science / Analytics": {
        "python", "sql", "statistics", "dashboard", "visualization", "experiment", "analysis", "pandas",
        "tableau", "power bi", "metrics", "forecasting", "ab testing", "insights",
    },
    "Backend Engineering": {
        "api", "apis", "fastapi", "django", "flask", "database", "databases", "postgresql", "sql",
        "docker", "microservices", "system design", "authentication", "cache", "queue",
    },
    "Frontend Engineering": {
        "react", "typescript", "javascript", "html", "css", "accessibility", "responsive", "vite",
        "component", "state", "ui", "ux", "performance",
    },
    "Full Stack Product Engineering": {
        "react", "typescript", "python", "api", "apis", "sql", "deployment", "frontend", "backend",
        "database", "authentication", "dashboard", "product",
    },
    "Cloud / DevOps": {
        "aws", "docker", "kubernetes", "ci/cd", "deployment", "monitoring", "linux", "terraform",
        "pipeline", "containers", "cloud",
    },
}
JOB_CATALOG = [
    {
        "title": "AI Engineer",
        "skills": {"python", "machine learning", "deep learning", "apis", "sql", "mlops"},
        "reason": "Builds intelligent products using models, APIs, data, and deployment workflows.",
    },
    {
        "title": "Data Scientist",
        "skills": {"python", "statistics", "machine learning", "sql", "visualization", "experimentation"},
        "reason": "Turns data into models, insights, experiments, and business decisions.",
    },
    {
        "title": "Full Stack Developer",
        "skills": {"react", "typescript", "python", "apis", "sql", "deployment"},
        "reason": "Combines frontend, backend, database, and deployment proof.",
    },
    {
        "title": "Backend Developer",
        "skills": {"python", "apis", "sql", "databases", "docker", "system design"},
        "reason": "Designs reliable APIs, services, persistence, and production architecture.",
    },
    {
        "title": "Frontend Developer",
        "skills": {"html", "css", "javascript", "typescript", "react", "accessibility"},
        "reason": "Builds polished user interfaces with strong interaction and accessibility skills.",
    },
]


def analyze_resume(resume_text: str, target_role: str) -> dict:
    text = resume_text.lower()
    required = required_skills_for(target_role)
    matched = sorted(skill for skill in required if skill in text)
    missing = sorted(required.difference(matched))
    action_hits = sorted(word for word in ACTION_WORDS if word in text)
    has_metrics = any(char.isdigit() for char in resume_text)

    score = 35 + len(matched) * 8 + len(action_hits) * 3 + (15 if has_metrics else 0)
    score = round(max(0, min(score, 100)), 2)

    strengths = []
    if matched:
        strengths.append(f"Relevant skills found: {', '.join(matched[:6])}.")
    if action_hits:
        strengths.append("Uses impact-oriented action verbs.")
    if has_metrics:
        strengths.append("Includes numbers or measurable outcomes.")
    if not strengths:
        strengths.append("The resume has a starting structure, but needs stronger targeting.")

    suggestions = [
        f"Add a targeted summary for {target_role}.",
        "Convert responsibilities into achievement bullets with numbers.",
        "Add 2-3 role-specific projects with tools, results, and links.",
    ]
    suggestions.extend([f"Add evidence for: {skill}." for skill in missing[:4]])

    return {
        "score": score,
        "strengths": strengths,
        "gaps": [f"Missing or weak signal: {skill}." for skill in missing] or ["No major target-skill gaps detected."],
        "suggestions": suggestions,
    }


def extract_detected_skills(resume_text: str) -> list[str]:
    text = resume_text.lower()
    detected = {skill for skill in COMMON_SKILLS if skill in text}
    for role_skills in ROLE_SKILLS.values():
        detected.update(skill for skill in role_skills if skill in text)
    return sorted(detected)


def extract_nlp_keywords(resume_text: str, limit: int = 18) -> list[str]:
    text = resume_text.lower()
    phrases = set()
    for keyword in COMMON_SKILLS.union(*DOMAIN_KEYWORDS.values()):
        if keyword in text:
            phrases.add(keyword)
    tokens = re.findall(r"[a-z][a-z+#.-]{2,}", text)
    stopwords = {
        "and", "the", "for", "with", "from", "this", "that", "are", "was", "were", "have", "has",
        "using", "into", "their", "your", "resume", "project", "work", "built",
    }
    counts: dict[str, int] = {}
    for token in tokens:
        if token not in stopwords:
            counts[token] = counts.get(token, 0) + 1
    ranked_tokens = sorted(counts, key=lambda token: (counts[token], len(token)), reverse=True)
    return sorted(phrases)[:limit] + [token for token in ranked_tokens if token not in phrases][: max(0, limit - len(phrases))]


def rank_resume_domains(resume_text: str, detected_skills: list[str]) -> tuple[list[dict], float]:
    text = resume_text.lower()
    detected = set(detected_skills)
    rankings = []
    semantic_density = min(len(extract_nlp_keywords(resume_text, 30)) / 30, 1)
    metric_signal = 1 if any(char.isdigit() for char in resume_text) else 0
    action_signal = min(sum(1 for word in ACTION_WORDS if word in text) / 6, 1)

    for domain, keywords in DOMAIN_KEYWORDS.items():
        direct_hits = {keyword for keyword in keywords if keyword in text or keyword in detected}
        coverage = len(direct_hits) / len(keywords)
        # A compact neural-style weighted signal: lexical coverage, semantic density,
        # action verbs, and metrics behave like hidden features for fit scoring.
        score = round(min(100, (coverage * 68) + (semantic_density * 14) + (action_signal * 10) + (metric_signal * 8)), 2)
        if score >= 72:
            confidence = "high"
        elif score >= 48:
            confidence = "medium"
        else:
            confidence = "low"
        rankings.append(
            {
                "domain": domain,
                "score": score,
                "confidence": confidence,
                "evidence": sorted(direct_hits)[:8],
                "missing_keywords": sorted(keywords.difference(direct_hits))[:6],
            }
        )
    rankings = sorted(rankings, key=lambda item: item["score"], reverse=True)
    deep_learning_signal = round(sum(item["score"] for item in rankings[:3]) / 3, 2)
    return rankings, deep_learning_signal


def score_job_matches(detected_skills: list[str]) -> list[dict]:
    detected = set(detected_skills)
    matches = []
    for job in JOB_CATALOG:
        required = job["skills"]
        matched = detected.intersection(required)
        score = round((len(matched) / len(required)) * 100, 2)
        matches.append(
            {
                "title": job["title"],
                "match_score": score,
                "reason": job["reason"],
                "missing_skills": sorted(required.difference(detected)),
            }
        )
    return sorted(matches, key=lambda item: item["match_score"], reverse=True)


def estimate_seniority(resume_text: str) -> str:
    text = resume_text.lower()
    years = [int(match) for match in re.findall(r"(\d+)\+?\s+years?", text)]
    max_years = max(years) if years else 0
    leadership_signal = any(word in text for word in ["led", "owned", "architected", "mentored", "managed"])
    if max_years >= 5 or leadership_signal:
        return "mid-to-senior"
    if max_years >= 2 or any(word in text for word in ["built", "deployed", "improved"]):
        return "junior-to-mid"
    return "entry-level"


def rewrite_bullets(resume_text: str, target_role: str, detected_skills: list[str]) -> list[str]:
    skills = ", ".join(detected_skills[:4]) or "role-relevant tools"
    return [
        f"Built and improved {target_role.lower()} projects using {skills}, with measurable impact on users, speed, or quality.",
        "Designed API, data, and user workflows end to end, then documented decisions, tradeoffs, and results.",
        "Converted ambiguous requirements into shipped features, tracked outcomes, and iterated from feedback.",
    ]


def build_resume_intelligence(resume_text: str, target_role: str) -> dict:
    base = analyze_resume(resume_text, target_role)
    detected_skills = extract_detected_skills(resume_text)
    nlp_keywords = extract_nlp_keywords(resume_text)
    domain_ranking, deep_learning_signal = rank_resume_domains(resume_text, detected_skills)
    required = required_skills_for(target_role)
    missing = sorted(required.difference(detected_skills))
    job_matches = score_job_matches(detected_skills)
    metric_bonus = 12 if any(char.isdigit() for char in resume_text) else 0
    skill_score = round((len(set(detected_skills).intersection(required)) / len(required)) * 100, 2) if required else 0
    ats_score = round(max(0, min(base["score"] + metric_bonus, 100)), 2)
    overall_score = round((ats_score * 0.45) + (skill_score * 0.35) + (job_matches[0]["match_score"] * 0.20), 2)

    priority_fixes = [
        "Add a role-specific headline and summary with the exact target title.",
        "Add numbers to prove scope: users, speed, revenue, accuracy, time saved, or volume.",
        "Group technical skills by category so recruiters can scan them in 5 seconds.",
    ]
    priority_fixes.extend([f"Add proof for {skill}." for skill in missing[:4]])

    project_recommendations = [
        f"Build a {target_role} portfolio project with authentication, database storage, APIs, and a deployed frontend.",
        "Create a resume intelligence dashboard that explains scoring and job-match decisions.",
        "Publish a case study showing problem, architecture, screenshots, metrics, and tradeoffs.",
    ]

    interview_focus = [
        "Prepare one STAR story for your strongest project.",
        "Explain architecture choices, tradeoffs, failure handling, and what you would improve next.",
        "Practice describing impact with numbers in under 90 seconds.",
    ]
    interview_focus.extend([f"Prepare a technical explanation for {skill}." for skill in missing[:3]])

    learning_plan = [
        "Day 1-3: close the highest missing skill with one small implementation task.",
        "Day 4-7: add measurable resume bullets and portfolio screenshots.",
        "Week 2: complete 3 mock interviews and revise answers using feedback.",
        "Week 3: apply to matched roles and track response rates.",
    ]

    return {
        "overall_score": overall_score,
        "ats_score": ats_score,
        "seniority_signal": estimate_seniority(resume_text),
        "detected_skills": detected_skills,
        "missing_skills": missing,
        "nlp_keywords": nlp_keywords,
        "domain_ranking": domain_ranking,
        "deep_learning_signal": deep_learning_signal,
        "job_matches": job_matches,
        "resume_strengths": base["strengths"],
        "priority_fixes": priority_fixes,
        "rewritten_bullets": rewrite_bullets(resume_text, target_role, detected_skills),
        "project_recommendations": project_recommendations,
        "interview_focus": interview_focus,
        "learning_plan": learning_plan,
    }
