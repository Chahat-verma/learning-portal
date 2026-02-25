"""
student_service.py — Student CRUD, XP management, and session logging.
"""

import logging
from datetime import datetime
from database import get_db_connection

logger = logging.getLogger("pipeline")


def get_or_create_student(student_id: str):
    """
    Get student details or create a new student if not exists.
    Returns a dict with student info.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()

        if not student:
            logger.info(f"[STUDENT] Creating new student: {student_id}")
            cursor.execute(
                "INSERT INTO students (id, created_at) VALUES (?, ?)",
                (student_id, datetime.now())
            )
            conn.commit()

            # Fetch the newly created student
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            student = cursor.fetchone()

    return dict(student)


def update_xp(student_id: str, amount: int = 10):
    """
    Add XP to a student and check for level up (every 100 XP).
    Transaction-wrapped with explicit commit and logging.
    Returns (new_xp, new_level, leveled_up_bool)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT xp, level FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"[XP] Student {student_id} not found. Skipping XP update.")
                return 0, 1, False

            current_xp = row['xp']
            current_level = row['level']

            new_xp = current_xp + amount
            new_level = current_level
            leveled_up = False

            # Simple level up logic: every 100 XP
            if new_xp >= new_level * 100:
                new_level += 1
                leveled_up = True

            cursor.execute(
                "UPDATE students SET xp = ?, level = ? WHERE id = ?",
                (new_xp, new_level, student_id)
            )
            conn.commit()

        logger.info(f"[XP] XP updated successfully for {student_id}: {current_xp} → {new_xp} (level {new_level})")
        return new_xp, new_level, leveled_up
    except Exception as e:
        logger.error(f"[XP] FAILED to update XP for {student_id}: {e}")
        return 0, 1, False


def log_interaction(student_id: str, subject: str, chapter_id: str):
    """Log a session interaction."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Update sessions table
        cursor.execute(
            "INSERT INTO sessions (student_id, last_topic, last_interaction) VALUES (?, ?, ?)",
            (student_id, f"{subject}/{chapter_id}", datetime.now())
        )

        # Increment total questions count
        cursor.execute(
            "UPDATE students SET total_questions = total_questions + 1 WHERE id = ?",
            (student_id,)
        )

        conn.commit()
