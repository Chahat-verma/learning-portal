"""
test_stabilization.py — Final verification for hackathon demo stability.
Hits all critical endpoints and confirms no crashes.
"""

import requests
import json
import sys

BASE = "http://localhost:8000"

def test(name, method, url, **kwargs):
    try:
        resp = getattr(requests, method)(f"{BASE}{url}", **kwargs, timeout=30)
        status = "✔" if resp.status_code < 400 else "✖"
        print(f"  {status} [{resp.status_code}] {name}")
        if resp.status_code >= 400:
            print(f"    Error: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  ✖ [ERR] {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("HACKATHON STABILIZATION VERIFICATION")
    print("=" * 60)
    results = []

    # 1. Health
    print("\n--- Health Check ---")
    r = test("GET /health", "get", "/health")
    results.append(r)
    if r:
        resp = requests.get(f"{BASE}/health")
        data = resp.json()
        print(f"    RAG Index: {data.get('rag_index_loaded')}")
        print(f"    ChromaDB: {data.get('chroma_available')}")

    # 2. Demo Students
    print("\n--- Demo Students ---")
    r = test("GET /demo/students", "get", "/demo/students")
    results.append(r)
    if r:
        students = requests.get(f"{BASE}/demo/students").json()
        for s in students:
            print(f"    • {s['display_name']} (Lv.{s['level']}, {s['difficulty']})")

    # 3. Demo Stats
    r = test("GET /demo/stats", "get", "/demo/stats")
    results.append(r)

    # 4. Subjects
    print("\n--- Content ---")
    r = test("GET /subjects", "get", "/subjects")
    results.append(r)

    r = test("GET /subjects/maths/chapters", "get", "/subjects/maths/chapters")
    results.append(r)

    # 5. Chat (RAG)
    print("\n--- Chat (RAG Pipeline) ---")
    r = test("POST /ask (Euclid)", "post", "/ask", json={
        "student_id": "average_student",
        "question": "What is Euclid's Division Lemma?",
        "subject": "maths",
        "chapter_id": "real_numbers"
    })
    results.append(r)
    if r:
        resp = requests.post(f"{BASE}/ask", json={
            "student_id": "average_student",
            "question": "What is Euclid's Division Lemma?",
            "subject": "maths",
            "chapter_id": "real_numbers"
        })
        data = resp.json()
        answer = data.get("answer", "")
        has_steps = any(f"Step {i}" in answer for i in range(1, 6))
        print(f"    Answer length: {len(answer)} chars")
        print(f"    Has 5-step format: {has_steps}")
        print(f"    Sources: {len(data.get('sources', []))}")

    # 6. Not in NCERT test
    r = test("POST /ask (Not in NCERT)", "post", "/ask", json={
        "student_id": "average_student",
        "question": "What is quantum computing?",
        "subject": "maths",
        "chapter_id": "NONEXISTENT_CHAPTER"
    })
    results.append(r)
    if r:
        resp = requests.post(f"{BASE}/ask", json={
            "student_id": "average_student",
            "question": "What is quantum computing?",
            "subject": "maths",
            "chapter_id": "NONEXISTENT_CHAPTER"
        })
        data = resp.json()
        print(f"    Answer: {data.get('answer', '')[:80]}")

    # 7. Quiz Generation
    print("\n--- Quiz ---")
    r = test("POST /quiz/generate", "post", "/quiz/generate", json={
        "student_id": "average_student",
        "subject": "maths",
        "chapter_id": "real_numbers",
        "num_questions": 3
    })
    results.append(r)
    if r:
        resp = requests.post(f"{BASE}/quiz/generate", json={
            "student_id": "average_student",
            "subject": "maths",
            "chapter_id": "real_numbers",
            "num_questions": 3
        })
        data = resp.json()
        print(f"    Quiz ID: {data.get('quiz_id', 'N/A')[:8]}...")
        print(f"    Questions: {len(data.get('questions', []))}")
        print(f"    Difficulty: {data.get('difficulty')}")

    # 8. Kolibri Demo Sync
    print("\n--- Kolibri ---")
    r = test("GET /kolibri/demo-sync", "get", "/kolibri/demo-sync?student_id=average_student")
    results.append(r)
    if r:
        resp = requests.get(f"{BASE}/kolibri/demo-sync?student_id=average_student")
        data = resp.json()
        print(f"    Status: {data.get('status')}")
        print(f"    XP Added: {data.get('xp_added')}")

    # 9. Weak Topics
    print("\n--- Adaptive ---")
    r = test("GET /weak_topics", "get", "/weak_topics/average_student")
    results.append(r)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"RESULTS: {passed}/{total} passed")
    if passed == total:
        print("🎉 ALL CHECKS PASSED — DEMO READY!")
    else:
        print(f"⚠️  {total - passed} checks failed. Review above.")
    print("=" * 60)

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
