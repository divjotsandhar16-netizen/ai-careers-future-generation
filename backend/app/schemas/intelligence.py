from pydantic import BaseModel, Field


class EmotionAnalyzeRequest(BaseModel):
    text: str = Field(min_length=2)


class EmotionAnalyzeResponse(BaseModel):
    emotion: str
    sentiment: str
    tone: str
    confidence: float
    scores: dict
    source: str
    recommendation: str


class PersonalityPredictRequest(BaseModel):
    typing_style: str = ""
    interests: list[str] = []
    answers: list[str] = []
    choices: dict = {}


class PersonalityPredictResponse(BaseModel):
    personality_type: str
    communication_style: str
    learning_style: str
    career_matches: list[str]
    best_work_environment: str
    strengths: list[str]
    weaknesses: list[str]
    scores: dict
    report: str
