import pytest
from database import get_db_connection

def test_student_creation(client, unique_student_id):
    """Test that a new student is created upon first interaction."""
    # Use /ask endpoint which triggers get_or_create_student
    # We mock RAG to avoid actual LLM calls if possible, but for now let's just use the endpoint
    # and expect a response. Note: RAG might fail if no documents, but student should be created.
    # To be safer, let's use submit_answer which is lighter.
    
    try:
        response = client.post("/submit_answer", json={
            "student_id": unique_student_id,
            "subject": "maths",
            "chapter_id": "real_numbers",
            "is_correct": True,
            "time_taken": 10.0
        })
    except Exception:
        # Even if it errors (e.g. DB issue), check if student was created
        pass
        
    # Check simple creation via DB
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (unique_student_id,)).fetchone()
        assert row is not None
        assert row["id"] == unique_student_id
        assert row["xp"] >= 0

def test_xp_and_streak_logic(client, unique_student_id):
    """Test XP gain and streak increments."""
    # 1. First correct answer
    resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": True,
        "time_taken": 5.0
    })
    data = resp.json()
    assert data["student_xp"] == 10
    assert data["current_streak"] == 1
    assert data["wrong_streak"] == 0

    # 2. Second correct answer
    resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": True,
        "time_taken": 5.0
    })
    data = resp.json()
    assert data["student_xp"] == 20
    assert data["current_streak"] == 2

    # 3. Wrong answer (Streak reset)
    resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": False,
        "time_taken": 5.0
    })
    data = resp.json()
    assert data["current_streak"] == 0
    assert data["wrong_streak"] == 1
    # XP should not increase
    assert data["student_xp"] == 20 

def test_difficulty_adjustment(client, unique_student_id):
    """Test difficulty increases after streak of 3."""
    # Ensure student starts at easy
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO students (id, current_difficulty) VALUES (?, 'easy')", (unique_student_id,))
        conn.commit()

    # Submit 3 correct answers
    for _ in range(3):
        resp = client.post("/submit_answer", json={
            "student_id": unique_student_id,
            "subject": "math",
            "chapter_id": "ch1",
            "is_correct": True,
            "time_taken": 10.0
        })
        data = resp.json()
    
    # After 3rd correct, difficulty should match expectation (logic says next_diff if streak >=3)
    # The logic in adaptive_service:
    # if current_streak >= 3:
    #    new_difficulty = _next_difficulty(difficulty)
    
    assert data["difficulty"] == "medium"
    assert data["difficulty_changed"] is True

def test_behavioral_metrics_guessing(client, unique_student_id):
    """Test that fast wrong answers (guessing) reduce confidence."""
    # Initial state: confidence 0.5
    
    # Submit fast wrong answer (< 2s)
    resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": False,
        "time_taken": 1.0 # Fast!
    })
    data = resp.json()
    
    # Confidence should drop from 0.5 -> 0.5 * 0.9 = 0.45
    assert data["confidence_score"] < 0.5
    assert data["confidence_score"] > 0.4  # Approx check

def test_behavioral_metrics_momentum(client, unique_student_id):
    """Test momentum calculation."""
    # Momentum = (streak * 0.3) + (mastery * 0.4) + (confidence * 0.3)
    
    # Submit correct answer (1st time - creates topic entry)
    client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": True,
        "time_taken": 10.0
    })

    # Submit 2nd correct answer (Now mastery should be 1.0)
    resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "ch1",
        "is_correct": True,
        "time_taken": 10.0
    })
    data = resp.json()
    
    # Streak 2, Confidence ~0.6, Mastery 1.0
    # Momentum = (2 * 0.3) + (1.0 * 0.4) + (0.6 * 0.3) = 1.18
    assert data["learning_momentum"] > 0.5
