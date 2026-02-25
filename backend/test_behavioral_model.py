"""
test_behavioral_model.py — Verify behavioral intelligence logic (guessing, confidence, momentum).
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
STUDENT_ID = "behavior_test_student"

def test_behavioral_flow():
    print("--- 1. Initial State ---")
    # Health check
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Health: {resp.status_code}")

    print("\n--- 2. Simulate Guessing (Fast Wrong Answer) ---")
    data = {
        "student_id": STUDENT_ID,
        "subject": "science",
        "chapter_id": "nutrition_in_plants",
        "is_correct": False,
        "time_taken": 1.5  # < 2 seconds
    }
    resp = requests.post(f"{BASE_URL}/submit_answer", json=data)
    result = resp.json()
    print(f"Confidence score (expected < 0.5): {result.get('confidence_score')}")
    print(f"Learning momentum: {result.get('learning_momentum')}")

    print("\n--- 3. Simulate Normal Learning (Slow Correct Answer) ---")
    data = {
        "student_id": STUDENT_ID,
        "subject": "science",
        "chapter_id": "nutrition_in_plants",
        "is_correct": True,
        "time_taken": 30.0
    }
    resp = requests.post(f"{BASE_URL}/submit_answer", json=data)
    result = resp.json()
    print(f"Confidence score (should increase): {result.get('confidence_score')}")
    print(f"Learning momentum: {result.get('learning_momentum')}")

    print("\n--- 4. Verify Streak Influence ---")
    # Add 2 more correct answers to get streak of 3
    for _ in range(2):
        requests.post(f"{BASE_URL}/submit_answer", json=data)
    
    resp = requests.post(f"{BASE_URL}/submit_answer", json=data)
    result = resp.json()
    print(f"Streak: {result.get('current_streak')}")
    print(f"Learning momentum (should be high): {result.get('learning_momentum')}")
    print(f"Difficulty: {result.get('difficulty')}")

    print("\n--- 5. Verify Teaching Strategy via /ask ---")
    # If momentum is high (>1.5), strategy should be "advanced_challenge"
    # We might need more correct answers to push momentum > 1.5
    # momentum = (streak * 0.3) + (mastery * 0.4) + (confidence * 0.3)
    # If streak 4, mastery 1.0, conf 0.6 -> 1.2 + 0.4 + 0.18 = 1.78
    
    ask_data = {
        "student_id": STUDENT_ID,
        "question": "What is photosynthesis?",
        "subject": "science",
        "chapter_id": "nutrition_in_plants"
    }
    resp = requests.post(f"{BASE_URL}/ask", json=ask_data)
    print(f"Ask Response (check for advanced difficulty indicators):")
    print(resp.json().get("answer")[:200] + "...")

if __name__ == "__main__":
    try:
        test_behavioral_flow()
    except Exception as e:
        print(f"Test failed: {e}")
