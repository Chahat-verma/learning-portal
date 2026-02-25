"""
test_adaptive.py — End-to-end test for adaptive learning system.

Tests:
1. /ask returns difficulty level
2. /submit_answer correct → XP + streak
3. /submit_answer 3x correct → difficulty promotion
4. /submit_answer 2x incorrect → difficulty demotion
5. /weak_topics returns low-accuracy topics
"""

import requests
import json
import time

URL = "http://localhost:8000"

def test_ask_with_difficulty():
    """Test that /ask returns the difficulty field."""
    print("=== Test 1: /ask returns difficulty ===")
    resp = requests.post(f"{URL}/ask", json={
        "student_id": "adaptive_test_student",
        "question": "What is Euclid's Division Lemma?",
        "subject": "maths",
        "chapter_id": "real_numbers"
    })
    data = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Difficulty: {data.get('difficulty')}")
    print(f"XP: {data.get('student_xp')} | Level: {data.get('student_level')}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "difficulty" in data, "Missing difficulty field"
    print("PASS\n")

def test_submit_correct():
    """Test submitting a correct answer."""
    print("=== Test 2: Submit correct answer ===")
    resp = requests.post(f"{URL}/submit_answer", json={
        "student_id": "adaptive_test_student",
        "subject": "maths",
        "chapter_id": "real_numbers",
        "is_correct": True
    })
    data = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Streak: {data.get('current_streak')} | Wrong: {data.get('wrong_streak')}")
    print(f"Difficulty: {data.get('difficulty')} | Changed: {data.get('difficulty_changed')}")
    print(f"XP: {data.get('student_xp')}")
    assert resp.status_code == 200
    assert data["current_streak"] >= 1
    print("PASS\n")

def test_difficulty_promotion():
    """Test that 3 correct answers in a row promotes difficulty."""
    print("=== Test 3: Difficulty promotion (3 correct → easy→medium) ===")
    # Submit 2 more correct (already have 1 from test 2)
    for i in range(2):
        resp = requests.post(f"{URL}/submit_answer", json={
            "student_id": "adaptive_test_student",
            "subject": "maths",
            "chapter_id": "real_numbers",
            "is_correct": True
        })
    data = resp.json()
    print(f"Streak: {data.get('current_streak')} | Difficulty: {data.get('difficulty')}")
    print(f"Changed: {data.get('difficulty_changed')}")
    assert data["difficulty"] == "medium", f"Expected 'medium', got {data['difficulty']}"
    assert data["difficulty_changed"] == True
    print("PASS\n")

def test_difficulty_demotion():
    """Test that 2 wrong answers in a row demotes difficulty."""
    print("=== Test 4: Difficulty demotion (2 wrong → medium→easy) ===")
    for i in range(2):
        resp = requests.post(f"{URL}/submit_answer", json={
            "student_id": "adaptive_test_student",
            "subject": "maths",
            "chapter_id": "real_numbers",
            "is_correct": False
        })
    data = resp.json()
    print(f"Wrong Streak: {data.get('wrong_streak')} | Difficulty: {data.get('difficulty')}")
    print(f"Changed: {data.get('difficulty_changed')}")
    assert data["difficulty"] == "easy", f"Expected 'easy', got {data['difficulty']}"
    assert data["difficulty_changed"] == True
    print("PASS\n")

def test_weak_topics():
    """Test weak topic detection (need >3 attempts with <60% accuracy)."""
    print("=== Test 5: Weak topic detection ===")
    # Submit 3 more wrong answers for a different topic to trigger weak detection
    for i in range(4):
        requests.post(f"{URL}/submit_answer", json={
            "student_id": "adaptive_test_student",
            "subject": "science",
            "chapter_id": "chemical_reactions",
            "is_correct": False
        })
    resp = requests.get(f"{URL}/weak_topics/adaptive_test_student")
    data = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Weak topics: {json.dumps(data, indent=2)}")
    assert resp.status_code == 200
    # Should have at least one weak topic
    topics = [t["topic"] for t in data]
    assert "science/chemical_reactions" in topics, f"Expected weak topic, got {topics}"
    print("PASS\n")

if __name__ == "__main__":
    print(f"Testing adaptive learning at {URL}...\n")
    try:
        test_ask_with_difficulty()
        test_submit_correct()
        test_difficulty_promotion()
        test_difficulty_demotion()
        test_weak_topics()
        print("=" * 50)
        print("ALL TESTS PASSED!")
    except AssertionError as e:
        print(f"ASSERTION FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
