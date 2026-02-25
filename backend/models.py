"""
models.py — Pydantic request/response models for the ICAN API.
"""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    student_id: str
    question: str
    subject: str
    chapter_id: str


class SubmitAnswerRequest(BaseModel):
    student_id: str
    subject: str
    chapter_id: str
    is_correct: bool
    time_taken: float = 0.0  # Seconds


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------
class SourceMeta(BaseModel):
    subject: str
    chapter_id: str
    lesson_id: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceMeta]
    student_xp: int
    student_level: int
    leveled_up: bool
    difficulty: str


class SubmitAnswerResponse(BaseModel):
    student_xp: int
    student_level: int
    leveled_up: bool
    current_streak: int
    wrong_streak: int
    difficulty: str
    difficulty_changed: bool
    confidence_score: float = 0.5
    learning_momentum: float = 0.0


class WeakTopic(BaseModel):
    topic: str
    correct: int
    total: int
    accuracy: float


# ---------------------------------------------------------------------------
# Quiz Models
# ---------------------------------------------------------------------------
class QuizRequest(BaseModel):
    student_id: str
    subject: str
    chapter_id: str
    num_questions: int = 5


class QuizResponseItem(BaseModel):
    id: int
    question: str
    options: list[str]
    # No correct_answer sent to client


class QuizResponse(BaseModel):
    quiz_id: str
    difficulty: str
    questions: list[QuizResponseItem]


class SubmitQuizRequest(BaseModel):
    student_id: str
    quiz_id: str
    answers: dict[int, str]  # {question_id: selected_option}
    time_taken: float = 0.0


class SubmitQuizResponse(BaseModel):
    score: int
    total: int
    xp_gained: int
    difficulty: str
    confidence_score: float
    learning_momentum: float
    weak_topics: list[str]


class KolibriSyncRequest(BaseModel):
    student_id: str
    kolibri_user_id: str | None = None


class KolibriSyncResponse(BaseModel):
    status: str
    synced_count: int
    total_xp_gained: int
    items: list[dict]
    suggested_quiz: dict | None

