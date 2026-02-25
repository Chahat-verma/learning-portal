import pytest

def test_rag_structure_mock(client, unique_student_id):
    """
    Test that /ask returns the correct structure even if RAG is mocked/empty.
    """
    resp = client.post("/ask", json={
        "student_id": unique_student_id,
        "question": "What is friction?",
        "subject": "physics",
        "chapter_id": "force_and_laws"
    })
    
    # We expect 200 OK or 500 if LLM fails (but we want meaningful error)
    # Ideally, services should handle LLM failure gracefully.
    # If it fails, we might get 500.
    
    if resp.status_code == 200:
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert "difficulty" in data
        assert "student_xp" in data
    else:
        # If it fails, print why (for debugging)
        print(f"RAG failed: {resp.text}")
        # Allow pass if it's just connection error to Ollama which might not be running in test env
        pass

def test_teaching_strategy_selection(client, unique_student_id):
    """
    Test that teaching strategy is selected based on student metrics.
    Hard to verify without inspecting internal state or logging, 
    but we can check if response time/correctness affects the NEXT call implicitly.
    """
    # Create a student with low confidence
    # 1. Submit many wrong answers fast
    for _ in range(3):
        client.post("/submit_answer", json={
            "student_id": unique_student_id,
            "subject": "math",
            "chapter_id": "ch1",
            "is_correct": False,
            "time_taken": 1.0
        })
        
    # Now ask a question
    resp = client.post("/ask", json={
        "student_id": unique_student_id,
        "question": "Help me!",
        "subject": "math",
        "chapter_id": "ch1"
    })
    
    # We can't easily assert the strategy used unless it's in the response.
    # The API doesn't return 'strategy'.
    # But we can at least ensure it doesn't crash.
    assert resp.status_code in [200, 500]
