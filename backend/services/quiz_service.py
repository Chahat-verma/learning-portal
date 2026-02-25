"""
quiz_service.py — Guaranteed quiz generation for hackathon demo.

Strategy:
1. Try LLM-based quiz generation first.
2. If LLM fails → generate deterministic MCQs from chapter text.
3. ALWAYS return ≥ 3 questions.
4. NEVER crash. NEVER return empty.
"""

import json
import uuid
import re
import random
import logging
from datetime import datetime
from typing import Optional

from database import get_db_connection
from services import rag_service, adaptive_service, student_service

logger = logging.getLogger("pipeline")

# ---------------------------------------------------------------------------
# Deterministic Quiz Generation (Fallback)
# ---------------------------------------------------------------------------
def _generate_deterministic_quiz(subject: str, chapter_id: str, num_questions: int = 3, difficulty: str = "medium") -> list[dict]:
    """
    Generate MCQs directly from chapter text without LLM.
    Extracts key sentences and converts them into fill-in-blank or factual MCQs.
    """
    logger.info(f"[QUIZ-FALLBACK] Generating deterministic quiz for {subject}/{chapter_id}")

    # Get lessons from in-memory index
    lessons = rag_service._NCERT_INDEX.get(subject.lower(), {}).get(chapter_id, [])
    if not lessons:
        # Try any chapter in subject
        for ch_id, ch_lessons in rag_service._NCERT_INDEX.get(subject.lower(), {}).items():
            lessons = ch_lessons
            break

    if not lessons:
        # Absolute fallback
        return _emergency_quiz(subject, chapter_id, num_questions)

    # Collect all content text
    all_text = " ".join([l.get("content", "") for l in lessons])

    # Extract candidate sentences (non-trivial, factual)
    sentences = re.split(r'[.!?]\s+', all_text)
    candidates = [s.strip() for s in sentences if 15 < len(s.strip()) < 200 and any(c.isalpha() for c in s)]

    if len(candidates) < 3:
        return _emergency_quiz(subject, chapter_id, num_questions)

    random.shuffle(candidates)
    questions = []

    for i, sentence in enumerate(candidates[:num_questions]):
        # Find a key term to blank out
        words = sentence.split()
        # Pick a meaningful word (>3 chars, not a stop word)
        key_words = [w for w in words if len(w) > 3 and w.isalpha() and w.lower() not in {
            'that', 'this', 'with', 'from', 'have', 'been', 'were', 'they', 'them',
            'their', 'which', 'when', 'where', 'what', 'will', 'also', 'into', 'some'
        }]

        if not key_words:
            key_words = [w for w in words if len(w) > 2 and w.isalpha()]

        if not key_words:
            continue

        answer_word = random.choice(key_words)
        blanked = sentence.replace(answer_word, "______", 1)

        # Generate distractors
        other_words = [w for w in key_words if w != answer_word]
        distractors = random.sample(other_words, min(3, len(other_words)))

        # Pad distractors if needed
        filler_words = ["element", "process", "theorem", "formula", "property", "function", "equation", "constant"]
        while len(distractors) < 3:
            filler = random.choice(filler_words)
            if filler not in distractors and filler != answer_word:
                distractors.append(filler)

        options = distractors[:3] + [answer_word]
        random.shuffle(options)

        questions.append({
            "id": i + 1,
            "question": f"Fill in the blank: {blanked}",
            "options": options,
            "correct_answer": answer_word,
            "explanation": f"The correct answer is '{answer_word}' as stated in the NCERT text.",
            "subtopic": chapter_id.replace("_", " ").title()
        })

    # Ensure minimum 3
    while len(questions) < 3:
        questions.append({
            "id": len(questions) + 1,
            "question": f"Which of these is a key concept in {chapter_id.replace('_', ' ').title()}?",
            "options": ["Definition", "Example", "Theorem", "Summary"],
            "correct_answer": "Definition",
            "explanation": "Definitions are fundamental building blocks of any chapter.",
            "subtopic": chapter_id.replace("_", " ").title()
        })

    return questions[:num_questions]


def _emergency_quiz(subject: str, chapter_id: str, num_questions: int = 3) -> list[dict]:
    """Absolute last resort — hardcoded generic questions."""
    chapter_name = chapter_id.replace("_", " ").title()
    return [
        {
            "id": 1,
            "question": f"What is the main topic covered in the chapter '{chapter_name}'?",
            "options": [chapter_name, "Trigonometry", "Electricity", "Organic Chemistry"],
            "correct_answer": chapter_name,
            "explanation": f"This chapter is about {chapter_name}.",
            "subtopic": chapter_name
        },
        {
            "id": 2,
            "question": f"Which subject does '{chapter_name}' belong to?",
            "options": [subject.title(), "Geography", "History", "Computer Science"],
            "correct_answer": subject.title(),
            "explanation": f"This chapter belongs to {subject.title()}.",
            "subtopic": chapter_name
        },
        {
            "id": 3,
            "question": "What is the purpose of examples in NCERT textbooks?",
            "options": [
                "To illustrate concepts with practice",
                "To confuse students",
                "To replace theory",
                "To add page count"
            ],
            "correct_answer": "To illustrate concepts with practice",
            "explanation": "Examples help students understand concepts through practical application.",
            "subtopic": "General"
        },
    ][:num_questions]


# ---------------------------------------------------------------------------
# LLM Quiz Prompt
# ---------------------------------------------------------------------------
QUIZ_PROMPT_TEMPLATE = """
You are a professional NCERT quiz setter.
Generate {num} Multiple Choice Questions (MCQs) for the following context.
Difficulty Level: {difficulty} ({difficulty_desc})

STRICT RULES:
1. Return purely valid JSON with no markdown formatting.
2. The JSON must be a list of objects.
3. Each object must have:
   - "id": integer (1 to {num})
   - "question": string
   - "options": list of 4 strings
   - "correct_answer": string (must be exactly one of the options)
   - "explanation": string (short reason for the answer)
   - "subtopic": string (specific concept derived from context)

CONTEXT:
{context}

JSON OUTPUT:
"""

DIFFICULTY_DESCRIPTIONS = {
    "easy": "Direct factual questions, simple language, no trick info.",
    "medium": "Conceptual application, requires understanding relationships.",
    "hard": "Analytical, multi-step reasoning, or 'why/how' questions.",
}


# ---------------------------------------------------------------------------
# Generate Quiz
# ---------------------------------------------------------------------------
def generate_quiz(
    student_id: str, subject: str, chapter_id: str, num_questions: int = 5
) -> dict:
    """
    Generate a quiz. NEVER crashes. NEVER returns empty.
    """
    logger.info(f"[QUIZ] Generating for {student_id}, {subject}/{chapter_id}, n={num_questions}")

    try:
        # 1. Determine difficulty
        difficulty = adaptive_service.get_student_difficulty(student_id)

        # 2. Retrieve Context
        query = f"Key concepts and important facts about {subject} {chapter_id}"
        chunks = rag_service.retrieve(query, subject, chapter_id)

        if not chunks:
            logger.warning("[QUIZ] No chunks. Using deterministic fallback.")
            questions = _generate_deterministic_quiz(subject, chapter_id, num_questions, difficulty)
        else:
            context_text = "\n\n".join([c["content"] for c in chunks])

            # 3. Try LLM
            prompt = QUIZ_PROMPT_TEMPLATE.format(
                num=num_questions,
                difficulty=difficulty,
                difficulty_desc=DIFFICULTY_DESCRIPTIONS.get(difficulty, ""),
                context=context_text[:2000]
            )

            response_text = rag_service.call_ollama(prompt)

            # 4. Parse JSON
            questions = None
            try:
                match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if match:
                    questions = json.loads(match.group(0))
                else:
                    cleaned = response_text.replace("```json", "").replace("```", "").strip()
                    questions = json.loads(cleaned)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"[QUIZ] LLM JSON parse failed: {e}. Using deterministic fallback.")
                questions = None

            # 5. Validate questions
            if not questions or len(questions) < 1:
                logger.warning("[QUIZ] LLM returned no valid questions. Using deterministic fallback.")
                questions = _generate_deterministic_quiz(subject, chapter_id, num_questions, difficulty)

            # Ensure each question has required fields
            validated = []
            for q in questions:
                if all(k in q for k in ("id", "question", "options", "correct_answer")):
                    q.setdefault("explanation", "See NCERT textbook for details.")
                    q.setdefault("subtopic", chapter_id.replace("_", " ").title())
                    validated.append(q)

            if len(validated) < 3:
                logger.warning(f"[QUIZ] Only {len(validated)} valid questions. Padding with deterministic.")
                extra = _generate_deterministic_quiz(subject, chapter_id, 3 - len(validated), difficulty)
                for eq in extra:
                    eq["id"] = len(validated) + 1
                    validated.append(eq)

            questions = validated

        # 6. Store in DB
        quiz_id = str(uuid.uuid4())
        questions_json = json.dumps(questions)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO quizzes (id, student_id, subject, chapter_id, difficulty, questions_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (quiz_id, student_id, subject, chapter_id, difficulty, questions_json),
            )
            conn.commit()

        # 7. Client response (strip answers)
        client_questions = []
        for q in questions:
            client_questions.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"]
            })

        logger.info(f"[QUIZ] Generated {len(client_questions)} questions, quiz_id={quiz_id}")
        return {
            "quiz_id": quiz_id,
            "difficulty": difficulty,
            "questions": client_questions
        }

    except Exception as e:
        logger.error(f"[QUIZ] CRITICAL ERROR: {e}")
        # Emergency: return hardcoded quiz rather than crashing
        questions = _emergency_quiz(subject, chapter_id, num_questions)
        quiz_id = str(uuid.uuid4())

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO quizzes (id, student_id, subject, chapter_id, difficulty, questions_json) VALUES (?, ?, ?, ?, ?, ?)",
                    (quiz_id, student_id, subject, chapter_id, "easy", json.dumps(questions)),
                )
                conn.commit()
        except Exception:
            pass

        return {
            "quiz_id": quiz_id,
            "difficulty": "easy",
            "questions": [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in questions]
        }


# ---------------------------------------------------------------------------
# Submit Quiz (unchanged logic, wrapped in safety)
# ---------------------------------------------------------------------------
def submit_quiz(student_id: str, quiz_id: str, answers: dict[int, str], time_taken: float = 0.0) -> dict:
    """Grade a quiz submission. Never crashes."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
            quiz = cursor.fetchone()

        if not quiz:
            return {"error": "Quiz not found"}

        original_questions = json.loads(quiz["questions_json"])
        score = 0
        total = len(original_questions)
        time_per_question = time_taken / total if total > 0 else 0.0

        results_summary = []
        for q in original_questions:
            q_id = q["id"]
            selected = answers.get(q_id) or answers.get(str(q_id))
            is_correct = (str(selected).strip() == str(q["correct_answer"]).strip()) if selected else False

            if is_correct:
                score += 1

            results_summary.append({
                "topic": f"{quiz['subject']}/{quiz['chapter_id']}",
                "subtopic": q.get("subtopic", "General"),
                "is_correct": is_correct
            })

        # Update adaptive stats
        difficulty_changed = False
        for res in results_summary:
            try:
                outcome = adaptive_service.update_progress(
                    student_id, res["topic"], res["is_correct"],
                    time_taken=time_per_question, subtopic=res["subtopic"]
                )
                if outcome.get("difficulty_changed"):
                    difficulty_changed = True
            except Exception as e:
                logger.error(f"[QUIZ] Adaptive update error: {e}")

        # Record attempt
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quiz_attempts (quiz_id, student_id, score, total_questions, timestamp) VALUES (?, ?, ?, ?, ?)",
                (quiz_id, student_id, score, total, datetime.now())
            )
            conn.commit()

        new_difficulty = adaptive_service.get_student_difficulty(student_id)
        weak_topics = adaptive_service.get_weak_topics(student_id)
        weak_topic_names = [t["topic"] for t in weak_topics]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT confidence_score, learning_momentum FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            confidence = row["confidence_score"] if row else 0.5
            momentum = row["learning_momentum"] if row else 0.0

        return {
            "score": score,
            "total": total,
            "xp_gained": score * 10,
            "difficulty": new_difficulty,
            "confidence_score": round(confidence, 2),
            "learning_momentum": round(momentum, 2),
            "weak_topics": weak_topic_names
        }

    except Exception as e:
        logger.error(f"[QUIZ] Submit error: {e}")
        return {
            "score": 0, "total": 0, "xp_gained": 0,
            "difficulty": "easy", "confidence_score": 0.5,
            "learning_momentum": 0.0, "weak_topics": []
        }
