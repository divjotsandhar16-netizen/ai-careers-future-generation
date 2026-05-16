import random


QUESTION_BANK = {
    "AI / Machine Learning": [
        "Explain a machine learning project you built, including the data, model choice, evaluation, and deployment plan.",
        "How would you reduce hallucinations in an AI assistant for career guidance?",
        "Describe the difference between supervised fine-tuning and retrieval augmented generation.",
        "How would you detect overfitting and improve generalization?",
        "Design a RAG system for resume analysis. What components are needed?",
        "Explain embeddings and how you would use them for job matching.",
        "How would you monitor model quality after deployment?",
        "What metrics would you use for a classification model and why?",
        "How would you handle biased or incomplete training data?",
        "Explain the tradeoff between latency, cost, and accuracy in AI products.",
    ],
    "Frontend Engineering": [
        "How do you design a React component so it stays reusable without becoming too abstract?",
        "Explain how you would improve performance in a slow dashboard.",
        "What accessibility checks do you perform before shipping a page?",
        "How do you manage state across a complex frontend workflow?",
        "Explain how you would design a responsive layout for mobile and desktop.",
        "How do you debug a production UI bug that only happens for some users?",
        "What makes a form experience professional and reliable?",
        "How would you structure API error handling in a React app?",
        "Explain code splitting and when you would use it.",
        "How do you test important frontend behavior?",
    ],
    "Backend Engineering": [
        "Design an API for a resume analyzer. What endpoints, models, and failure states would you include?",
        "How do you handle database migrations and schema changes safely?",
        "Explain authentication and authorization in a production API.",
        "How would you design rate limiting for a public API?",
        "Explain how you would structure service, schema, and database layers.",
        "How do you handle background jobs and long-running tasks?",
        "What logs and metrics would you add to debug production issues?",
        "How would you design a file upload API safely?",
        "Explain transactions and when you need them.",
        "How do you version APIs without breaking clients?",
    ],
    "Data Science / Analytics": [
        "How would you turn messy resume data into useful job-match insights?",
        "Explain how you validate whether an analytics dashboard is trustworthy.",
        "What is the difference between correlation and causation?",
        "How would you choose metrics for a career readiness product?",
        "Explain how you would detect outliers in application response data.",
        "How would you communicate uncertain model results to non-technical users?",
        "What would you include in an experiment to test resume improvements?",
        "How do you avoid misleading visualizations?",
        "Explain a time-series forecasting use case for hiring trends.",
        "How would you clean a dataset before modeling?",
    ],
    "Full Stack Product Engineering": [
        "Walk through the full architecture of a resume intelligence platform.",
        "How do you decide what belongs on the frontend versus backend?",
        "Design a real-time AI chat feature with WebSockets.",
        "How would you store and retrieve user career plans?",
        "What would you deploy first for an MVP and why?",
        "How would you handle failed API calls in the product experience?",
        "Explain how you would secure resume uploads and user data.",
        "How do you measure whether this product is helping users?",
        "What tradeoffs did you make between speed and quality?",
        "How would you scale this app from one user to thousands?",
    ],
    "Cloud / DevOps": [
        "How would you deploy a FastAPI and React application?",
        "Explain CI/CD for this project.",
        "How would you monitor uptime and API latency?",
        "What environment variables are needed for a production AI app?",
        "How do containers help deployment consistency?",
        "How would you handle secrets safely?",
        "Design a rollback plan for a broken deployment.",
        "How would you separate dev, staging, and production?",
        "What is the difference between horizontal and vertical scaling?",
        "How would you store model artifacts in production?",
    ],
    "Behavioral / HR": [
        "Tell me about a difficult project and how you handled tradeoffs.",
        "Describe a time you learned a skill quickly to solve a real problem.",
        "Why are you interested in this role, and what proof can you show?",
        "Tell me about a time you received feedback and changed your approach.",
        "Describe a conflict in a team and how you handled it.",
        "What is your biggest weakness and how are you improving it?",
        "Tell me about a project you are proud of.",
        "Why should we hire you?",
        "Describe a time you failed and what you learned.",
        "Where do you want to grow in the next year?",
    ],
}


def next_question(target_role: str, difficulty: str = "mid") -> str:
    role = target_role.lower()
    key = "Behavioral / HR"
    if "ai" in role or "machine" in role or "data" in role:
        key = "AI / Machine Learning"
    elif "front" in role or "react" in role:
        key = "Frontend Engineering"
    elif "back" in role or "api" in role:
        key = "Backend Engineering"
    return f"[{difficulty.title()}] {random.choice(QUESTION_BANK[key])}"


def domain_questions(domain: str, difficulty: str = "mid", count: int = 7) -> list[str]:
    key = domain if domain in QUESTION_BANK else "Behavioral / HR"
    questions = QUESTION_BANK[key][:]
    random.shuffle(questions)
    return [f"[{difficulty.title()}] {question}" for question in questions[:count]]


def evaluate_answer(answer: str) -> tuple[float, str]:
    words = answer.split()
    score = 40
    if len(words) >= 60:
        score += 20
    elif len(words) >= 30:
        score += 10
    if any(token in answer.lower() for token in ["result", "impact", "metric", "%", "reduced", "increased"]):
        score += 20
    if any(token in answer.lower() for token in ["challenge", "tradeoff", "learned", "improved"]):
        score += 10
    if any(char.isdigit() for char in answer):
        score += 10
    score = round(min(score, 100), 2)

    feedback = "Strong answer. Keep it structured with context, action, result, and reflection."
    if score < 70:
        feedback = "Good start. Add a clearer situation, specific actions you took, measurable results, and what you learned."
    return score, feedback
