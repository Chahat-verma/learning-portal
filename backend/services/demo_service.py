"""
demo_service.py — Demo student profiles for hackathon presentation.

3 profiles: struggling_student, average_student, advanced_student
Each with distinct XP, mastery, and difficulty levels.
"""

from database import get_db_connection
from services import student_service
import logging

logger = logging.getLogger("pipeline")

DEMO_PROFILES = {
    "struggling_student": {
        "display_name": "Riya (Struggling)",
        "xp": 45,
        "level": 1,
        "current_difficulty": "easy",
        "confidence_score": 0.25,
        "learning_momentum": 0.1,
        "total_questions": 12,
        "correct_answers": 3,
        "mastery_avg": 0.15,
        "description": "Needs extra support. Low confidence, few correct answers."
    },
    "average_student": {
        "display_name": "Arjun (Average)",
        "xp": 480,
        "level": 5,
        "current_difficulty": "medium",
        "confidence_score": 0.65,
        "learning_momentum": 1.0,
        "total_questions": 45,
        "correct_answers": 28,
        "mastery_avg": 0.55,
        "description": "Steady learner. Building confidence with consistent practice."
    },
    "advanced_student": {
        "display_name": "Priya (Advanced)",
        "xp": 2200,
        "level": 22,
        "current_difficulty": "hard",
        "confidence_score": 0.92,
        "learning_momentum": 2.3,
        "total_questions": 180,
        "correct_answers": 168,
        "mastery_avg": 0.88,
        "description": "Top performer. Ready for challenging problems."
    }
}


def init_demo_students():
    """
    Ensure demo students exist with known baseline stats.
    Called at startup. Idempotent: resets to baseline every restart.
    """
    print("[DEMO] Initializing demo students...")
    logger.info("[DEMO] Initializing 3 demo student profiles")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            for s_id, stats in DEMO_PROFILES.items():
                # 1. Ensure existence
                cursor.execute("INSERT OR IGNORE INTO students (id) VALUES (?)", (s_id,))

                # 2. Force stats to known baseline
                cursor.execute(
                    """
                    UPDATE students SET
                        xp = ?, level = ?, current_difficulty = ?,
                        confidence_score = ?, learning_momentum = ?,
                        total_questions = ?, correct_answers = ?
                    WHERE id = ?
                    """,
                    (
                        stats["xp"], stats["level"], stats["current_difficulty"],
                        stats["confidence_score"], stats["learning_momentum"],
                        stats["total_questions"], stats["correct_answers"],
                        s_id
                    )
                )

                # 3. Seed topic mastery
                cursor.execute("DELETE FROM topic_mastery WHERE student_id = ?", (s_id,))
                cursor.execute(
                    """
                    INSERT INTO topic_mastery (student_id, subtopic, mastery_score, attempts, correct_attempts)
                    VALUES (?, 'general_concepts', ?, 10, ?)
                    """,
                    (s_id, stats["mastery_avg"], int(10 * stats["mastery_avg"]))
                )

            conn.commit()
        print("[DEMO] Demo students initialized successfully.")
    except Exception as e:
        logger.error(f"[DEMO] Failed to init demo students: {e}")
        print(f"[DEMO] WARNING: Failed to init demo students: {e}")


def get_demo_students():
    """Return list of demo student profiles for frontend dropdown."""
    students = []
    for s_id, profile in DEMO_PROFILES.items():
        students.append({
            "student_id": s_id,
            "display_name": profile["display_name"],
            "difficulty": profile["current_difficulty"],
            "xp": profile["xp"],
            "level": profile["level"],
            "description": profile["description"]
        })
    return students


def get_demo_stats():
    """Return detailed stats for all demo students from DB."""
    results = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            for s_id in DEMO_PROFILES.keys():
                cursor.execute(
                    """
                    SELECT id, xp, level, current_difficulty, confidence_score, learning_momentum
                    FROM students WHERE id = ?
                    """,
                    (s_id,)
                )
                row = cursor.fetchone()
                if row:
                    cursor.execute(
                        "SELECT AVG(mastery_score) as avg_mastery FROM topic_mastery WHERE student_id = ?",
                        (s_id,)
                    )
                    m_row = cursor.fetchone()
                    avg_mastery = m_row["avg_mastery"] if m_row and m_row["avg_mastery"] else 0.0

                    results.append({
                        "student_id": row["id"],
                        "display_name": DEMO_PROFILES[s_id]["display_name"],
                        "xp": row["xp"],
                        "level": row["level"],
                        "difficulty": row["current_difficulty"],
                        "mastery_average": round(avg_mastery, 2),
                        "confidence_score": round(row["confidence_score"], 2),
                        "learning_momentum": round(row["learning_momentum"], 2)
                    })
    except Exception as e:
        logger.error(f"[DEMO] Stats fetch error: {e}")
        # Return static profile data as fallback
        for s_id, p in DEMO_PROFILES.items():
            results.append({
                "student_id": s_id,
                "display_name": p["display_name"],
                "xp": p["xp"],
                "level": p["level"],
                "difficulty": p["current_difficulty"],
                "mastery_average": p["mastery_avg"],
                "confidence_score": p["confidence_score"],
                "learning_momentum": p["learning_momentum"]
            })

    return results
