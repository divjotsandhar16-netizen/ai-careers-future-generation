import json


def predict_personality(payload: dict) -> dict:
    interests = " ".join(payload.get("interests", [])).lower()
    answers = " ".join(payload.get("answers", [])).lower()
    typing = payload.get("typing_style", "").lower()
    choices = payload.get("choices", {})
    text = f"{interests} {answers} {typing}"

    analytical = score(text, ["data", "logic", "systems", "math", "debug", "architecture", "research"])
    creative = score(text, ["design", "story", "visual", "creative", "writing", "content", "brand"])
    social = score(text, ["team", "people", "mentor", "communicate", "help", "lead", "community"])
    practical = score(text, ["build", "ship", "execute", "organize", "reliable", "process", "plan"])

    technical = min(100, 42 + analytical * 11 + practical * 6)
    creativity = min(100, 38 + creative * 12 + social * 3)
    leadership = min(100, 35 + social * 10 + practical * 5 + int(choices.get("leadership", 3)) * 5)
    communication = min(100, 40 + social * 8 + creative * 4 + int(choices.get("communication", 3)) * 6)

    if analytical >= creative and technical >= 65:
        personality_type = "Analytical Builder"
        careers = ["AI Engineer", "Backend Developer", "Data Scientist", "ML Engineer"]
        environment = "Structured teams with complex problems, strong mentorship, and room to build systems."
    elif creative > analytical and communication >= 65:
        personality_type = "Creative Communicator"
        careers = ["Product Designer", "Frontend Developer", "Content Strategist", "Product Manager"]
        environment = "Collaborative product teams with visual, storytelling, and user-facing work."
    elif leadership >= 70:
        personality_type = "Strategic Leader"
        careers = ["Product Manager", "Tech Lead", "Solutions Architect", "Founder"]
        environment = "Ownership-heavy environments where you coordinate people, priorities, and outcomes."
    else:
        personality_type = "Adaptive Generalist"
        careers = ["Full Stack Developer", "Business Analyst", "AI Product Builder", "Technical Consultant"]
        environment = "Fast-moving teams where learning, communication, and execution matter together."

    learning_style = "Project-first learner" if "project" in text or practical > analytical else "Concept-first learner"
    communication_style = "Direct and structured" if "clear" in text or analytical >= social else "Warm and collaborative"

    return {
        "personality_type": personality_type,
        "communication_style": communication_style,
        "learning_style": learning_style,
        "career_matches": careers,
        "best_work_environment": environment,
        "strengths": strengths_for(personality_type),
        "weaknesses": weaknesses_for(personality_type),
        "scores": {
            "technical": technical,
            "creative": creativity,
            "leadership": leadership,
            "communication": communication,
            "analytical": min(100, analytical * 18),
            "practical": min(100, practical * 18),
        },
        "report": (
            f"You look like an {personality_type}. Your best growth path is to build proof projects, "
            f"practice communication, and target roles where your {learning_style.lower()} style is an advantage."
        ),
    }


def score(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def strengths_for(personality_type: str) -> list[str]:
    strengths = {
        "Analytical Builder": ["systems thinking", "technical depth", "debugging", "structured learning"],
        "Creative Communicator": ["storytelling", "user empathy", "presentation", "visual thinking"],
        "Strategic Leader": ["ownership", "prioritization", "team communication", "decision making"],
        "Adaptive Generalist": ["learning agility", "cross-functional thinking", "execution", "flexibility"],
    }
    return strengths[personality_type]


def weaknesses_for(personality_type: str) -> list[str]:
    weaknesses = {
        "Analytical Builder": ["may over-optimize", "needs more storytelling practice"],
        "Creative Communicator": ["may need deeper technical proof", "should quantify impact more"],
        "Strategic Leader": ["may need sharper technical details", "should avoid vague strategy"],
        "Adaptive Generalist": ["needs clearer specialization", "should build deeper portfolio proof"],
    }
    return weaknesses[personality_type]


def dumps(value: dict | list) -> str:
    return json.dumps(value)
