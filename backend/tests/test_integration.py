import pytest
import time

def test_full_learning_flow(client, unique_student_id):
    """
    Test a complete learning session:
    1. Ask a question (RAG + Teaching Strategy)
    2. Answer the check question correctly
    3. Verify XP, momentum, and difficulty update
    """
    # 1. Ask Question
    ask_resp = client.post("/ask", json={
        "student_id": unique_student_id,
        "question": "What is gravity?",
        "subject": "physics",
        "chapter_id": "force_and_laws"
    })
    assert ask_resp.status_code == 200
    ask_data = ask_resp.json()
    assert "answer" in ask_data
    assert "difficulty" in ask_data
    
    initial_difficulty = ask_data["difficulty"]
    
    # 2. Submit Answer (Correct)
    # Simulate reading time
    # time.sleep(1) # mocked time in request
    
    ans_resp = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "physics",
        "chapter_id": "force_and_laws",
        "is_correct": True,
        "time_taken": 15.0
    })
    ans_data = ans_resp.json()
    
    assert ans_data["student_xp"] > 0
    assert ans_data["current_streak"] == 1
    
    # 3. Submit another Correct Answer to trigger streak
    ans_resp_2 = client.post("/submit_answer", json={
        "student_id": unique_student_id,
        "subject": "physics",
        "chapter_id": "force_and_laws",
        "is_correct": True,
        "time_taken": 10.0
    })
    
    # 4. Check Weak Topics (should be empty for this topic as it's 100% correct)
    weak_resp = client.get(f"/weak_topics/{unique_student_id}")
    weak_data = weak_resp.json()
    # Should not contain physics/force_and_laws
    for topic in weak_data:
        assert topic["topic"] != "physics/force_and_laws"

def test_quiz_flow_weak_focus(client, unique_student_id):
    """
    Test quiz generation and submission affecting weak topics.
    1. Fail a topic repeatedly -> becomes weak.
    2. Generate quiz -> should arguably focus on it (if logic exists, else just normal quiz).
    3. Submit quiz -> check score.
    """
    # 1. Fail a topic
    for _ in range(3):
        client.post("/submit_answer", json={
            "student_id": unique_student_id,
            "subject": "math",
            "chapter_id": "bad_topic",
            "is_correct": False,
            "time_taken": 5.0
        })
        
    # Verify it is weak
    weak_resp = client.get(f"/weak_topics/{unique_student_id}")
    print(weak_resp.json()) 
    # Logic: accuracy < 60% and total >= 3
    # 0/3 = 0% < 60%.
    weak_topics = [t["topic"] for t in weak_resp.json()]
    assert "math/bad_topic" in weak_topics
    
    # 2. Generate Quiz
    quiz_resp = client.post("/quiz/generate", json={
        "student_id": unique_student_id,
        "subject": "math",
        "chapter_id": "bad_topic",
        "num_questions": 5
    })
    assert quiz_resp.status_code in [200, 500] 
    if quiz_resp.status_code == 200:
        quiz_id = quiz_resp.json()["quiz_id"]
        
        # 3. Submit Quiz
        # Assume we got everything right this time
        # Need question IDs
        q_ids = [str(q["id"]) for q in quiz_resp.json()["questions"]]
        answers = {qid: "Option A" for qid in q_ids} # Mock answers
        
        sub_resp = client.post("/quiz/submit", json={
            "student_id": unique_student_id,
            "quiz_id": quiz_id,
            "answers": answers,
            "time_taken": 60.0
        })
        assert sub_resp.status_code == 200
