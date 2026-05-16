from pydantic import BaseModel, Field


class CareerPlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    current_role: str = Field(min_length=2, max_length=160)
    target_role: str = Field(min_length=2, max_length=160)
    skills: list[str] = Field(default_factory=list)
    experience_years: float = Field(ge=0, le=50)
    projects_count: int = Field(ge=0, le=100)
    interview_confidence: int = Field(ge=1, le=10)


class CareerPlanOut(BaseModel):
    id: int
    name: str
    current_role: str
    target_role: str
    skills: list[str]
    readiness_score: float
    roadmap: list[str]


class ChatMessage(BaseModel):
    message: str = Field(min_length=1)
    target_role: str | None = None


class ChatResponse(BaseModel):
    answer: str
    recommended_actions: list[str]


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=30)
    target_role: str = Field(min_length=2, max_length=160)


class ResumeAnalyzeResponse(BaseModel):
    id: int
    score: float
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]


class JobMatch(BaseModel):
    title: str
    match_score: float
    reason: str
    missing_skills: list[str]


class DomainScore(BaseModel):
    domain: str
    score: float
    confidence: str
    evidence: list[str]
    missing_keywords: list[str]


class ResumeIntelligenceResponse(BaseModel):
    id: int
    file_name: str
    target_role: str
    overall_score: float
    ats_score: float
    seniority_signal: str
    detected_skills: list[str]
    missing_skills: list[str]
    nlp_keywords: list[str]
    domain_ranking: list[DomainScore]
    deep_learning_signal: float
    job_matches: list[JobMatch]
    resume_strengths: list[str]
    priority_fixes: list[str]
    rewritten_bullets: list[str]
    project_recommendations: list[str]
    interview_focus: list[str]
    learning_plan: list[str]


class InterviewQuestionRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    difficulty: str = "mid"


class InterviewQuestionResponse(BaseModel):
    question: str


class InterviewBatchRequest(BaseModel):
    domain: str = "AI / Machine Learning"
    difficulty: str = "mid"
    count: int = Field(default=7, ge=5, le=10)


class InterviewBatchResponse(BaseModel):
    domain: str
    difficulty: str
    questions: list[str]


class InterviewEvaluateRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    question: str = Field(min_length=5)
    answer: str = Field(min_length=5)


class InterviewEvaluateResponse(BaseModel):
    id: int
    score: float
    feedback: str


class ReadinessPredictRequest(BaseModel):
    experience_years: float = Field(ge=0, le=50)
    projects_count: int = Field(ge=0, le=100)
    skill_match_percent: float = Field(ge=0, le=100)
    interview_confidence: int = Field(ge=1, le=10)


class ReadinessPredictResponse(BaseModel):
    readiness_score: float
    label: str
