import requests
import json
import time

URL = "http://localhost:8000/ask"
HEADERS = {"Content-Type": "application/json"}

TEST_CASES = [
    {
        "name": "Maths - Euclidean Geometry",
        "payload": {
            "student_id": "student_A",
            "question": "What is Euclid's Division Lemma?",
            "subject": "maths",
            "chapter_id": "real_numbers"
        }
    },
    {
        "name": "Science - Combination Reaction",
        "payload": {
            "student_id": "student_B",
            "question": "Explain combination reaction with an example.",
            "subject": "science",
            "chapter_id": "chemical_reactions_and_equations"
        }
    },
    {
        "name": "Hallucination Check - Out of Scope",
        "payload": {
            "student_id": "student_A",
            "question": "Who is the Prime Minister of India?",
            "subject": "maths",
            "chapter_id": "real_numbers"
        }
    }
]

def run_tests():
    print(f"Running {len(TEST_CASES)} tests against {URL}...\n")
    
    results = []
    
    for test in TEST_CASES:
        print(f"--- Running: {test['name']} ---")
        try:
            start_time = time.time()
            resp = requests.post(URL, json=test['payload'], headers=HEADERS)
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "No answer field found")
                sources = data.get("sources", [])
                
                print(f"Status: {resp.status_code} (in {elapsed:.2f}s)")
                print(f"Student: {data.get('student_xp', 0)} XP | Level {data.get('student_level', 1)}")
                print(f"Sources found: {len(sources)}")
                print("\nANSWER:")
                print(answer)
                print("\n" + "="*60 + "\n")
                
                results.append({
                    "name": test['name'],
                    "status": "PASS",
                    "answer_preview": answer[:100] + "..."
                })
            else:
                print(f"FAILED. Status: {resp.status_code}")
                print(resp.text)
                results.append({"name": test['name'], "status": "FAIL"})
                
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"name": test['name'], "status": "ERROR"})

    print("\nSummary:")
    for r in results:
        print(f"- {r['name']}: {r['status']}")

if __name__ == "__main__":
    run_tests()
