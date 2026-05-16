import re


def career_chat(message: str, target_role: str | None = None) -> dict:
    role = target_role or "your target role"
    lower = message.lower()

    if "resume" in lower:
        answer = f"For {role}, make your resume proof-heavy: headline, 3 role-matched skills, 2 projects, and quantified bullets."
        actions = ["Add metrics to 3 bullets", "Mirror keywords from job descriptions", "Remove unrelated tools"]
    elif "interview" in lower:
        answer = f"Practice interviews for {role} with a 4-part answer: context, decision, action, result."
        actions = ["Record one mock answer", "Add one metric", "Prepare 5 STAR stories"]
    elif "roadmap" in lower or "plan" in lower:
        answer = f"Your roadmap to {role} should combine skill gaps, proof projects, networking, and weekly interview practice."
        actions = ["Pick one target job description", "Build one project", "Apply to 5 matching roles"]
    else:
        answer = f"Focus on becoming visibly ready for {role}: skills, proof, communication, and consistent applications."
        actions = ["Define target role", "Analyze current gaps", "Ship one portfolio proof"]

    return {"answer": answer, "recommended_actions": actions}


def advanced_career_chat(
    message: str,
    target_role: str | None = None,
    context: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    role = target_role or context.get("activeTarget") if context else target_role
    role = role or "your target role"
    lower = message.lower()
    context = context or {}
    history = history or []

    plan_score = context.get("careerScore")
    resume_score = context.get("resumeScore")
    interview_score = context.get("interviewScore")
    resume_report = context.get("resumeReport") or {}
    detected_skills = resume_report.get("detected_skills") or context.get("skills") or []
    missing_skills = resume_report.get("missing_skills") or []
    job_matches = resume_report.get("job_matches") or []

    intro = f"I'll think about this like a career coach and product-minded interviewer for a {role} path."
    if history:
        intro = f"Continuing from our last {min(len(history), 6)} messages, here is the cleanest next move for {role}."

    signals = []
    if plan_score is not None:
        signals.append(f"career readiness {round(plan_score)}")
    if resume_score is not None:
        signals.append(f"resume signal {round(resume_score)}")
    if interview_score is not None:
        signals.append(f"interview signal {round(interview_score)}")
    signal_line = f"Current signals: {', '.join(signals)}." if signals else "Current signals are still being built, so I will optimize for proof and clarity."

    if "resume" in lower or "job" in lower or "upload" in lower:
        return build_resume_strategy(intro, signal_line, role, detected_skills, missing_skills, job_matches)
    if "interview" in lower or "answer" in lower or "mock" in lower:
        return build_interview_strategy(intro, signal_line, role, detected_skills, missing_skills)
    if "roadmap" in lower or "plan" in lower or "learn" in lower:
        return build_roadmap_strategy(intro, signal_line, role, detected_skills, missing_skills)
    if "project" in lower or "portfolio" in lower:
        return build_project_strategy(intro, signal_line, role, detected_skills, missing_skills)
    if is_career_adjacent(lower):
        return build_general_strategy(intro, signal_line, role, detected_skills, missing_skills, job_matches)
    return build_general_knowledge_response(message, history)


def is_career_adjacent(lower: str) -> bool:
    keyword_phrases = {
        "full stack", "machine learning", "data science", "system design",
    }
    if any(phrase in lower for phrase in keyword_phrases):
        return True
    keywords = {
        "career", "resume", "cv", "job", "interview", "roadmap", "skill", "project", "portfolio",
        "apply", "linkedin", "salary", "internship", "developer", "engineer", "data", "ai", "ml",
        "frontend", "backend", "full stack", "study", "learn", "course",
    }
    tokens = set(re.findall(r"[a-z0-9+#.]+", lower))
    return bool(tokens.intersection(keywords))


def build_general_knowledge_response(message: str, history: list[dict]) -> str:
    recent = ""
    if history:
        recent = f"\n\nI also remember the recent thread has {min(len(history), 8)} messages, so I will keep continuity where useful."
    return f"""I can help with that too.{recent}

Here is the best local answer I can give without a cloud language model:

You asked: "{message}"

I can reason through general topics, explain concepts, help write code, draft text, plan projects, debug errors, and turn ideas into structured steps. For truly ChatGPT-level open-domain answers on anything, connect an OpenAI API key in the backend `.env`. Once that key is present, this same chat box will stream answers from the real model.

For now, ask me in one of these forms and I will answer as deeply as the local engine can:
1. "Explain this concept..."
2. "Write code for..."
3. "Make a plan for..."
4. "Compare these options..."
5. "Debug this error..."

If your question needs current facts, private knowledge, or broad world knowledge, the OpenAI key path is the right mode."""


def build_resume_strategy(intro: str, signal_line: str, role: str, detected_skills: list, missing_skills: list, job_matches: list) -> str:
    best_job = job_matches[0]["title"] if job_matches else role
    detected = ", ".join(detected_skills[:6]) or "your strongest technical proof"
    missing = ", ".join(missing_skills[:4]) or "clearer metrics and role-specific language"
    return f"""{intro}

{signal_line}

Your resume strategy should be: position yourself for {best_job}, then make every section prove that direction.

What I would change first:
1. Rewrite the headline to say the exact target: {role}.
2. Put your strongest proof in the top third: {detected}.
3. Add missing signals recruiters may search for: {missing}.
4. Convert responsibilities into impact bullets: action, tool, result, number.

Strong bullet format:
Built [system/project] using [tools] to solve [problem], improving [metric] by [number].

Next move: paste 3 resume bullets here and I will rewrite them into interview-ready, recruiter-friendly bullets."""


def build_interview_strategy(intro: str, signal_line: str, role: str, detected_skills: list, missing_skills: list) -> str:
    proof = ", ".join(detected_skills[:4]) or "your best project"
    gap = missing_skills[0] if missing_skills else "tradeoffs"
    return f"""{intro}

{signal_line}

For interviews, your goal is not to sound perfect. Your goal is to sound specific, calm, and technical.

Use this answer structure:
1. Context: what problem you solved.
2. Decision: why you chose your approach.
3. Build: what you actually implemented.
4. Result: what improved.
5. Reflection: what you would improve next.

Your strongest talking points right now are: {proof}.

Practice question:
Tell me about a project where you had to make a technical tradeoff. Include the architecture, one failure point, and the measurable result.

One gap to prepare: {gap}. If asked about it, be honest, then connect it to what you are learning or building next."""


def build_roadmap_strategy(intro: str, signal_line: str, role: str, detected_skills: list, missing_skills: list) -> str:
    missing = missing_skills[:3] or ["portfolio proof", "mock interview practice", "job-specific resume keywords"]
    return f"""{intro}

{signal_line}

Here is a focused 21-day roadmap for {role}:

Week 1: Skill proof
- Pick one target job description.
- Build or improve one project around its top requirements.
- Close these gaps first: {', '.join(missing)}.

Week 2: Resume and portfolio
- Rewrite your top 5 bullets with numbers.
- Add screenshots, architecture notes, and deployment links.
- Create a short case study for your best project.

Week 3: Interview and applications
- Do 3 mock interviews.
- Apply to 15 matched roles.
- Track responses and adjust keywords based on job descriptions.

If you want the fastest improvement, do not study randomly. Build one proof artifact every 2-3 days."""


def build_project_strategy(intro: str, signal_line: str, role: str, detected_skills: list, missing_skills: list) -> str:
    missing = missing_skills[0] if missing_skills else "production polish"
    return f"""{intro}

{signal_line}

Build one flagship project that makes the interviewer say: this person can ship.

Project idea:
AI Career Intelligence Platform
- Resume upload and parsing
- Skill extraction and job matching
- Interview question generation
- Realtime chat coaching
- Dashboard analytics
- API documentation and WebSocket events

To make it impressive, explain the architecture:
React frontend, FastAPI backend, SQLite/Postgres database, ML scoring layer, file parsing service, realtime WebSocket stream.

Add one stretch feature around {missing}. That turns it from a class project into a product demo."""


def build_general_strategy(intro: str, signal_line: str, role: str, detected_skills: list, missing_skills: list, job_matches: list) -> str:
    best = job_matches[0]["title"] if job_matches else role
    skills = ", ".join(detected_skills[:5]) or "your current skills"
    gaps = ", ".join(missing_skills[:3]) or "stronger proof, metrics, and interview stories"
    return f"""{intro}

{signal_line}

My read: you should market yourself toward {best}, while building stronger proof for {role}.

You already have signal around: {skills}.
The biggest improvement areas are: {gaps}.

High-impact next steps:
1. Make one project the centerpiece of your portfolio.
2. Rewrite your resume around results, not tasks.
3. Practice explaining your architecture out loud.
4. Apply to roles where you match at least 55-60 percent, then learn from the gaps.

Ask me something specific like: "rewrite these bullets", "create my 30-day plan", or "mock interview me for AI Engineer" and I will go deeper."""


def stream_chunks(text: str) -> list[str]:
    words = text.split(" ")
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(current) >= 4 or word.endswith((".", ":", "\n")):
            chunks.append(" ".join(current) + " ")
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks
