"""
adaptive_service.py — Handles streaks, difficulty adjustment, and behavioral modeling.
"""

from database import get_db_connection
from services.student_service import update_xp

# Difficulty levels in order
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


def _next_difficulty(current: str) -> str:
    """Move difficulty one step harder."""
    idx = DIFFICULTY_LEVELS.index(current) if current in DIFFICULTY_LEVELS else 0
    return DIFFICULTY_LEVELS[min(idx + 1, len(DIFFICULTY_LEVELS) - 1)]


def _prev_difficulty(current: str) -> str:
    """Move difficulty one step easier."""
    idx = DIFFICULTY_LEVELS.index(current) if current in DIFFICULTY_LEVELS else 0
    return DIFFICULTY_LEVELS[max(idx - 1, 0)]


def get_student_difficulty(student_id: str) -> str:
    """Get the current difficulty level for a student."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_difficulty FROM students WHERE id = ?", (student_id,)
        )
        row = cursor.fetchone()
        if row:
            return row["current_difficulty"] or "easy"
    return "easy"


def update_progress(
    student_id: str, 
    topic: str, 
    is_correct: bool, 
    time_taken: float = 0.0,
    subtopic: str = None
) -> dict:
    """
    Update student progress and behavioral model.
    topic: Subject/Chapter (Broad context)
    subtopic: Specific concept (Optional, for mastery tracking)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Fetch current state
        cursor.execute(
            """
            SELECT current_streak, wrong_streak, current_difficulty, 
                   avg_response_time, total_questions, confidence_score 
            FROM students WHERE id = ?
            """,
            (student_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Student not found"}

        current_streak = row["current_streak"] or 0
        wrong_streak = row["wrong_streak"] or 0
        difficulty = row["current_difficulty"] or "easy"
        avg_time = row["avg_response_time"] or 0.0
        total_qs = row["total_questions"] or 0
        confidence = row["confidence_score"] or 0.5
        
        difficulty_changed = False

        # 2. Update Basic Stats (Streaks)
        if is_correct:
            current_streak += 1
            wrong_streak = 0
            cursor.execute(
                "UPDATE students SET correct_answers = correct_answers + 1 WHERE id = ?",
                (student_id,),
            )
        else:
            wrong_streak += 1
            current_streak = 0
        
        # Increment total_questions locally for avg calculation
        new_total = total_qs + 1
        
        # 3. Update Response Time (Running Average)
        # New Average = ((Old Avg * Old Count) + New Time) / New Count
        if time_taken > 0:
            new_avg_time = ((avg_time * total_qs) + time_taken) / new_total
        else:
            new_avg_time = avg_time

        # 4. Guessing Detection & Confidence Update
        # Rule: Time < 2s AND Wrong -> Guessing -> Reduce confidence
        if time_taken > 0 and time_taken < 2.0 and not is_correct:
            # Guessing penalty
            confidence = max(0.0, confidence * 0.9)
        elif is_correct:
            # Boost confidence slowly
            confidence = min(1.0, confidence + 0.05)
        else:
            # Normal wrong answer
            confidence = max(0.0, confidence - 0.02)

        # 5. Difficulty Adjustment
        new_difficulty = difficulty
        # Influence difficulty by confidence?
        # If High Confidence + Streak -> Promote faster? 
        # For now keep existing rule but maybe act faster?
        
        if current_streak >= 3:
            # If high confidence, maybe jump? (Keep it simple for now)
            new_difficulty = _next_difficulty(difficulty)
            if new_difficulty != difficulty:
                difficulty_changed = True
                current_streak = 0
        elif wrong_streak >= 2:
            new_difficulty = _prev_difficulty(difficulty)
            if new_difficulty != difficulty:
                difficulty_changed = True
                wrong_streak = 0

        # 6. Update Topic Mastery (Subtopic level)
        mastery_score = 0.0
        if subtopic:
            cursor.execute(
                """
                INSERT INTO topic_mastery (student_id, subtopic, attempts, correct_attempts, mastery_score)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(student_id, subtopic) DO UPDATE SET
                attempts = attempts + 1,
                correct_attempts = correct_attempts + ?,
                mastery_score = CAST((correct_attempts + ?) AS REAL) / (attempts + 1)
                """,
                (
                    student_id, subtopic, 
                    1 if is_correct else 0, 
                    1.0 if is_correct else 0.0,  # mastery for new insert
                    1 if is_correct else 0,      # add to correct_attempts
                    1 if is_correct else 0       # add to correct (for calc)
                )
            )
            # Retrieve updated mastery for momentum calc
            cursor.execute("SELECT mastery_score FROM topic_mastery WHERE student_id=? AND subtopic=?", (student_id, subtopic))
            m_row = cursor.fetchone()
            if m_row:
                mastery_score = m_row["mastery_score"]
        else:
            # Fallback: calculate roughly from student_topics (broad topic)
            cursor.execute("SELECT correct, total FROM student_topics WHERE student_id=? AND topic=?", (student_id, topic))
            t_row = cursor.fetchone()
            if t_row and t_row["total"] > 0:
                mastery_score = t_row["correct"] / t_row["total"]

        # 7. Calculate Momentum
        # Formula: (streak * 0.3) + (mastery * 0.4) + (confidence * 0.3)
        momentum = (current_streak * 0.3) + (mastery_score * 0.4) + (confidence * 0.3)

        # 8. Save Metrics to DB
        cursor.execute(
            """
            UPDATE students SET 
                current_streak = ?, wrong_streak = ?, current_difficulty = ?, 
                last_topic = ?, total_questions = ?, avg_response_time = ?,
                confidence_score = ?, learning_momentum = ?
            WHERE id = ?
            """,
            (
                current_streak, wrong_streak, new_difficulty, topic, new_total, 
                new_avg_time, confidence, momentum, student_id
            ),
        )

        # 9. Update Broad Topic Stats (student_topics)
        cursor.execute(
            """
            INSERT INTO student_topics (student_id, topic, correct, total)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(student_id, topic) DO UPDATE SET
            correct = correct + ?, total = total + 1
            """,
            (student_id, topic, 1 if is_correct else 0, 1 if is_correct else 0),
        )

        conn.commit()

    # XP Reward
    xp, level, leveled_up = (0, 1, False)
    if is_correct:
        xp, level, leveled_up = update_xp(student_id, amount=10)
    else:
        # Fetch current XP without updating
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT xp, level FROM students WHERE id = ?", (student_id,))
            r = cursor.fetchone()
            if r:
                xp, level = r["xp"], r["level"]

    return {
        "student_xp": xp,
        "student_level": level,
        "leveled_up": leveled_up,
        "current_streak": current_streak,
        "wrong_streak": wrong_streak,
        "difficulty": new_difficulty,
        "difficulty_changed": difficulty_changed,
        "confidence_score": round(confidence, 2),
        "learning_momentum": round(momentum, 2)
    }


def get_weak_topics(student_id: str) -> list[dict]:
    """
    Return topics where student accuracy is below 60%.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT topic, correct, total FROM student_topics "
            "WHERE student_id = ? AND total >= 3",
            (student_id,),
        )
        weak = []
        for row in cursor.fetchall():
            accuracy = (row["correct"] / row["total"]) * 100 if row["total"] > 0 else 0
            if accuracy < 60:
                weak.append({
                    "topic": row["topic"],
                    "correct": row["correct"],
                    "total": row["total"],
                    "accuracy": round(accuracy, 1),
                })
    return weak


def get_teaching_strategy(student_id: str) -> dict:
    """
    Return strategy modifiers based on behavioral metrics.
    Rules:
    - Low confidence (< 0.4) -> encourage
    - Low mastery (< 0.5) -> simplify/revise
    - High momentum (> 1.5) -> challenge
    - Fast wrong answers (avg_time < 5s and wrong_streak >= 2) -> slow_down
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT confidence_score, learning_momentum, avg_response_time, wrong_streak 
            FROM students WHERE id = ?
            """,
            (student_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"modifier": "standard"}

        confidence = row["confidence_score"] or 0.5
        momentum = row["learning_momentum"] or 0.0
        avg_time = row["avg_response_time"] or 0.0
        wrong_streak = row["wrong_streak"] or 0

        strategy = {
            "modifier": "standard",
            "encourage": confidence < 0.4,
            "revision_mode": momentum < 0.3, # Low momentum/mastery
            "challenge_mode": momentum > 1.5,
            "slow_down": avg_time < 5.0 and wrong_streak >= 1,
        }
        
        if strategy["slow_down"]:
            strategy["modifier"] = "slow_and_detailed"
        elif strategy["challenge_mode"]:
            strategy["modifier"] = "advanced_challenge"
        elif strategy["revision_mode"]:
            strategy["modifier"] = "revision_focus"
            
        return strategy

