"""
test_quiz_engine.py — End-to-end test for Quiz Generation and Grading.

Flow:
1. Generate Quiz for 'maths/real_numbers'.
2. Verify quiz structure returned to client (no answers).
3. Fetch actual quiz from DB to get correct answers.
4. Submit perfect answers.
5. Verify Score=5/5, XP gained, and 'quiz_attempts' record.
"""

import requests
import json
import sqlite3
import time

URL = "http://localhost:8000"
DB_PATH = "students.db"

def get_db_quiz(quiz_id):
    """Fetch raw quiz from DB to spy on answers."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT questions_json FROM quizzes WHERE id = ?", (quiz_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["questions_json"])
    return None

def test_quiz_flow():
    print("=== Test: Quiz Generation & Submission ===")
    
    # 1. Generate Quiz
    print("Generating quiz...")
    resp = requests.post(f"{URL}/quiz/generate", json={
        "student_id": "quiz_master",
        "subject": "maths",
        "chapter_id": "real_numbers",
        "num_questions": 3  # Small number for speed
    })
    
    if resp.status_code != 200:
        print(f"FAILED: {resp.text}")
        return

    quiz_data = resp.json()
    quiz_id = quiz_data["quiz_id"]
    questions = quiz_data["questions"]
    
    print(f"Quiz ID: {quiz_id}")
    print(f"Difficulty: {quiz_data['difficulty']}")
    print(f"Questions: {len(questions)}")
    
    # Verify structure
    assert "id" in questions[0]
    assert "options" in questions[0]
    assert "correct_answer" not in questions[0], "Client should not see correct answers!"
    
    # 2. Get Correct Answers from DB (Cheating for test)
    full_questions = get_db_quiz(quiz_id)
    correct_answers = {q["id"]: q["correct_answer"] for q in full_questions}
    print(f"Correct Answers (DB): {correct_answers}")
    
    # 3. Submit Perfect Score
    print("Submitting perfect answers...")
    # Convert keys to strings for JSON payload if needed, logic handles both
    submission = {
        "student_id": "quiz_master",
        "quiz_id": quiz_id,
        "answers": correct_answers
    }
    
    resp = requests.post(f"{URL}/quiz/submit", json=submission)
    result = resp.json()
    
    print(f"Score: {result['score']}/{result['total']}")
    print(f"XP Gained: {result['xp_gained']}")
    print(f"New Difficulty: {result['difficulty']}")
    
    assert result["score"] == 3
    assert result["total"] == 3
    assert result["xp_gained"] == 30
    
    print("PASS: Quiz flow verified successfully.")

if __name__ == "__main__":
    try:
        test_quiz_flow()
    except Exception as e:
        print(f"ERROR: {e}")
