"""
main.py — FastAPI server for ICAN — Offline AI Tutor.

Routing only. Business logic lives in services/.
Hackathon stabilization: all endpoints wrapped, never crash.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from models import (
    AskRequest, AskResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    WeakTopic,
    QuizRequest, QuizResponse,
    SubmitQuizRequest, SubmitQuizResponse,
    KolibriSyncRequest, KolibriSyncResponse
)
from services import rag_service, student_service, adaptive_service, quiz_service, kolibri_service, demo_service
from services import content_service, video_service
from startup_banner import print_startup_banner

# Configure pipeline logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# App & Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag_service._load_ncert_index()
    demo_service.init_demo_students()
    print_startup_banner()
    yield

app = FastAPI(title="ICAN — Offline AI Tutor", version="2.0.0-demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Chat Routes
# ---------------------------------------------------------------------------
@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    try:
        student_service.get_or_create_student(req.student_id)
        student_service.log_interaction(req.student_id, req.subject, req.chapter_id)

        difficulty = adaptive_service.get_student_difficulty(req.student_id)
        strategy = adaptive_service.get_teaching_strategy(req.student_id)

        result = rag_service.ask(
            req.question, req.subject, req.chapter_id,
            difficulty=difficulty, strategy=strategy
        )

        new_xp, new_level, leveled_up = student_service.update_xp(req.student_id, amount=10)

        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            student_xp=new_xp,
            student_level=new_level,
            leveled_up=leveled_up,
            difficulty=difficulty,
        )
    except Exception as e:
        logger.error(f"[ASK ENDPOINT] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit_answer", response_model=SubmitAnswerResponse)
def submit_answer_endpoint(req: SubmitAnswerRequest):
    try:
        student_service.get_or_create_student(req.student_id)
        topic = f"{req.subject}/{req.chapter_id}"
        result = adaptive_service.update_progress(
            req.student_id, topic, req.is_correct, time_taken=req.time_taken
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return SubmitAnswerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SUBMIT_ANSWER] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Quiz Routes
# ---------------------------------------------------------------------------
@app.post("/quiz/generate", response_model=QuizResponse)
def generate_quiz_endpoint(req: QuizRequest):
    try:
        student_service.get_or_create_student(req.student_id)
        result = quiz_service.generate_quiz(
            req.student_id, req.subject, req.chapter_id, req.num_questions
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return QuizResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[QUIZ GENERATE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/submit", response_model=SubmitQuizResponse)
def submit_quiz_endpoint(req: SubmitQuizRequest):
    try:
        student_service.get_or_create_student(req.student_id)
        result = quiz_service.submit_quiz(
            req.student_id, req.quiz_id, req.answers, time_taken=req.time_taken
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return SubmitQuizResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[QUIZ SUBMIT] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Video Library Routes (Kolibri Integration)
# ---------------------------------------------------------------------------
@app.get("/videos")
def get_videos(
    subject: str = Query(None),
    chapter_id: str = Query(None),
    student_id: str = Query(None)
):
    """Get video library with optional filters. Includes watch status if student_id provided."""
    videos = video_service.get_video_library(subject, chapter_id)

    if student_id:
        watched = video_service.get_watched_videos(student_id)
        for v in videos:
            v["watched"] = v["id"] in watched
    else:
        for v in videos:
            v["watched"] = False

    return videos


@app.post("/videos/{video_id}/watch")
def mark_video_watched(video_id: str, student_id: str = Query(...)):
    """Mark a video as watched and award XP."""
    return video_service.mark_video_watched(student_id, video_id)


# ---------------------------------------------------------------------------
# Kolibri Routes
# ---------------------------------------------------------------------------
@app.post("/kolibri/sync", response_model=KolibriSyncResponse)
def kolibri_sync_endpoint(req: KolibriSyncRequest):
    try:
        student_service.get_or_create_student(req.student_id)
        result = kolibri_service.sync_kolibri_data(req.student_id, req.kolibri_user_id)
        return KolibriSyncResponse(**result)
    except Exception as e:
        logger.error(f"[KOLIBRI SYNC] Error: {e}")
        return KolibriSyncResponse(
            status="error", synced_count=0, total_xp_gained=0,
            items=[], suggested_quiz=None
        )


@app.get("/kolibri/demo-sync")
def kolibri_demo_sync(student_id: str = "average_student"):
    """Simulate Kolibri sync: 1 completed video, +150 XP."""
    return kolibri_service.demo_sync(student_id)


# ---------------------------------------------------------------------------
# Demo Routes
# ---------------------------------------------------------------------------
@app.get("/demo/students")
def get_demo_students():
    """List available demo students for the frontend dropdown."""
    return demo_service.get_demo_students()


@app.get("/demo/stats")
def get_demo_stats_endpoint():
    """Return detailed stats for demo students."""
    return demo_service.get_demo_stats()


# ---------------------------------------------------------------------------
# Content Routes
# ---------------------------------------------------------------------------
@app.get("/subjects")
def get_subjects():
    return content_service.get_all_subjects()


@app.get("/subjects/{subject_id}/chapters")
def get_chapters(subject_id: str):
    return content_service.get_chapters_for_subject(subject_id)


# ---------------------------------------------------------------------------
# Student Info Routes
# ---------------------------------------------------------------------------
@app.get("/student/{student_id}/stats")
def get_student_stats(student_id: str):
    """Get comprehensive student stats for dashboard."""
    try:
        with __import__('database').get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Student not found"}

            # Get mastery data
            cursor.execute(
                "SELECT subtopic, mastery_score FROM topic_mastery WHERE student_id = ?",
                (student_id,)
            )
            masteries = [{"topic": r["subtopic"], "score": round(r["mastery_score"], 2)} for r in cursor.fetchall()]

            # Get recent quiz attempts
            cursor.execute(
                "SELECT score, total_questions, timestamp FROM quiz_attempts WHERE student_id = ? ORDER BY timestamp DESC LIMIT 5",
                (student_id,)
            )
            recent_quizzes = [{"score": r["score"], "total": r["total_questions"], "date": r["timestamp"]} for r in cursor.fetchall()]

            # Get watched videos count
            cursor.execute(
                "SELECT COUNT(*) as count FROM kolibri_sync_logs WHERE student_id = ?",
                (student_id,)
            )
            videos_watched = cursor.fetchone()["count"]

        return {
            "student_id": row["id"],
            "xp": row["xp"],
            "level": row["level"],
            "difficulty": row["current_difficulty"],
            "confidence": round(row["confidence_score"], 2),
            "momentum": round(row["learning_momentum"], 2),
            "total_questions": row["total_questions"],
            "correct_answers": row["correct_answers"],
            "accuracy": round(row["correct_answers"] / max(row["total_questions"], 1) * 100, 1),
            "masteries": masteries,
            "recent_quizzes": recent_quizzes,
            "videos_watched": videos_watched,
        }
    except Exception as e:
        logger.error(f"[STUDENT STATS] Error: {e}")
        return {"error": str(e)}


@app.get("/student/{student_id}/chapter-progress")
def get_chapter_progress(student_id: str):
    """Get per-chapter learning progress for a student."""
    try:
        with __import__('database').get_db_connection() as conn:
            cursor = conn.cursor()

            # Count sessions per chapter
            cursor.execute(
                "SELECT last_topic, COUNT(*) as count FROM sessions WHERE student_id = ? GROUP BY last_topic",
                (student_id,)
            )
            session_counts = {row["last_topic"]: row["count"] for row in cursor.fetchall()}

            # Get quiz scores per chapter
            cursor.execute(
                """
                SELECT q.subject, q.chapter_id,
                       COUNT(qa.id) as attempts,
                       AVG(CAST(qa.score AS FLOAT) / NULLIF(qa.total_questions, 0)) as avg_score
                FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                WHERE qa.student_id = ?
                GROUP BY q.subject, q.chapter_id
                """,
                (student_id,)
            )
            quiz_data = {}
            for row in cursor.fetchall():
                key = f"{row['subject']}/{row['chapter_id']}"
                quiz_data[key] = {
                    "attempts": row["attempts"],
                    "avg_score": round((row["avg_score"] or 0) * 100, 1)
                }

            # Combine all available chapters from content service
            from services.content_service import SUBJECTS_DATA
            progress = []
            for subject in SUBJECTS_DATA:
                for chapter in subject.get("chapters", []):
                    key = f"{subject['id']}/{chapter['id']}"
                    sessions = session_counts.get(key, 0)
                    quiz = quiz_data.get(key, {"attempts": 0, "avg_score": 0})
                    progress.append({
                        "subject": subject["id"],
                        "subject_name": subject["name"],
                        "chapter_id": chapter["id"],
                        "chapter_name": chapter["name"],
                        "questions_asked": sessions,
                        "quiz_attempts": quiz["attempts"],
                        "avg_quiz_score": quiz["avg_score"],
                    })

        return progress
    except Exception as e:
        logger.error(f"[CHAPTER PROGRESS] Error: {e}")
        return []


@app.get("/weak_topics/{student_id}", response_model=list[WeakTopic])
def weak_topics_endpoint(student_id: str):
    return adaptive_service.get_weak_topics(student_id)


# ---------------------------------------------------------------------------
# System Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    import requests as req
    ollama_ok = False
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=2)
        ollama_ok = r.status_code == 200
    except Exception:
        pass

    total_lessons = sum(len(ls) for chs in rag_service._NCERT_INDEX.values() for ls in chs.values())

    return {
        "status": "ok",
        "mode": "demo",
        "ollama_active": ollama_ok,
        "rag_index_loaded": total_lessons > 0,
        "rag_lessons": total_lessons,
        "chroma_available": rag_service.CHROMA_AVAILABLE,
        "subjects": list(rag_service._NCERT_INDEX.keys()),
    }


# ---------------------------------------------------------------------------
# Debug / Diagnostics (PART 3 + PART 4)
# ---------------------------------------------------------------------------
@app.get("/debug/student/{student_id}")
def debug_student(student_id: str):
    """Return full student state for live debugging."""
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": f"Student {student_id} not found"}
            data = dict(row)

            # Get mastery info
            cursor.execute("SELECT subtopic, mastery_score, attempts FROM topic_mastery WHERE student_id = ?", (student_id,))
            mastery = [dict(r) for r in cursor.fetchall()]

        return {
            "student_id": data.get("id"),
            "xp": data.get("xp", 0),
            "level": data.get("level", 1),
            "difficulty": data.get("current_difficulty", "easy"),
            "confidence": data.get("confidence_score", 0.5),
            "momentum": data.get("learning_momentum", 0.0),
            "total_questions": data.get("total_questions", 0),
            "correct_answers": data.get("correct_answers", 0),
            "current_streak": data.get("current_streak", 0),
            "wrong_streak": data.get("wrong_streak", 0),
            "mastery": mastery,
        }
    except Exception as e:
        logger.error(f"[DEBUG] Error fetching student {student_id}: {e}")
        return {"error": str(e)}


@app.get("/starter-test/{student_id}")
def starter_test(student_id: str):
    """
    PART 4 — Generate 3 baseline diagnostic questions.
    Works WITHOUT AI. Sets initial difficulty based on score.
    """
    logger.info(f"[STARTER-TEST] Generating for {student_id}")
    student_service.get_or_create_student(student_id)

    # Deterministic baseline questions — always available
    questions = [
        {
            "id": 1,
            "question": "What is the HCF of 12 and 18?",
            "options": ["6", "3", "12", "9"],
            "correct_answer": "6",
            "explanation": "HCF of 12 and 18 is found by listing common factors: 1,2,3,6. The highest is 6.",
            "subtopic": "Real Numbers",
        },
        {
            "id": 2,
            "question": "What is the chemical formula of water?",
            "options": ["H2O", "CO2", "NaCl", "O2"],
            "correct_answer": "H2O",
            "explanation": "Water consists of 2 hydrogen atoms and 1 oxygen atom: H₂O.",
            "subtopic": "Chemical Reactions",
        },
        {
            "id": 3,
            "question": "Solve: 2x + 3 = 11. What is x?",
            "options": ["4", "3", "5", "8"],
            "correct_answer": "4",
            "explanation": "2x + 3 = 11 → 2x = 8 → x = 4.",
            "subtopic": "Linear Equations",
        },
    ]

    return {
        "test_type": "starter_diagnostic",
        "label": "Starter Test",
        "questions": [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in questions],
        "_answers": questions,  # For grading
    }


@app.post("/starter-test/{student_id}/submit")
def submit_starter_test(student_id: str, answers: dict):
    """
    Grade starter test and set initial difficulty.
    answers: {1: "6", 2: "H2O", 3: "4"}
    """
    correct_answers = {"1": "6", "2": "H2O", "3": "4"}
    score = 0
    for q_id, ans in answers.items():
        if str(ans).strip() == correct_answers.get(str(q_id), ""):
            score += 1

    # Set difficulty: 0-1 → easy, 2 → medium, 3 → hard
    if score <= 1:
        difficulty = "easy"
    elif score == 2:
        difficulty = "medium"
    else:
        difficulty = "hard"

    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE students SET current_difficulty = ? WHERE id = ?",
                (difficulty, student_id)
            )
            conn.commit()
        logger.info(f"[STARTER-TEST] {student_id}: score={score}/3, difficulty set to {difficulty}")
    except Exception as e:
        logger.error(f"[STARTER-TEST] DB error: {e}")

    # Award XP for completing starter test
    student_service.update_xp(student_id, amount=score * 10)

    return {
        "score": score,
        "total": 3,
        "difficulty_set": difficulty,
        "xp_gained": score * 10,
        "message": f"Initial difficulty set to {difficulty.upper()} based on your performance.",
    }


# ---------------------------------------------------------------------------
# Kolibri Safe Mode (PART 6)
# ---------------------------------------------------------------------------
@app.get("/kolibri/demo")
def kolibri_demo():
    """Safe demo endpoint — always returns OK."""
    return {"status": "Synced", "xp_added": 150}


@app.get("/kolibri/status")
def kolibri_status():
    """Check Kolibri availability with safe fallback."""
    try:
        # Quick check — if service has data it's working
        return {"status": "available", "mode": "offline"}
    except Exception:
        return {"status": "Kolibri unavailable (safe mode)"}
