import asyncio
import httpx
import time
import random
import sys
import json
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"
NUM_STUDENTS = 3
SUBJECT = "maths"
CHAPTER_ID = "real_numbers"

COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}

def log(message, level="INFO"):
    color = COLORS["OKBLUE"]
    if level == "SUCCESS": color = COLORS["OKGREEN"]
    elif level == "WARNING": color = COLORS["WARNING"]
    elif level == "ERROR": color = COLORS["FAIL"]
    elif level == "HEADER": color = COLORS["HEADER"]
    
    print(f"{color}[{level}] {message}{COLORS['ENDC']}")

async def test_health(client: httpx.AsyncClient) -> bool:
    try:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            log("Backend is reachable (Health Check Passed)", "SUCCESS")
            return True
        else:
            log(f"Backend returned {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"Backend connection failed: {e}", "ERROR")
        return False

async def simulate_student_flow(student_id: int):
    student_id_str = f"validation_student_{student_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        log(f"Student {student_id}: Starting session", "INFO")
        
        # 1. Chat Interaction (RAG) - /ask
        log(f"Student {student_id}: Asking Chatbot", "INFO")
        try:
            resp = await client.post(f"{BASE_URL}/ask", json={
                "student_id": student_id_str,
                "question": "What is Euclid's Division Lemma?",
                "subject": SUBJECT,
                "chapter_id": CHAPTER_ID
            })
            if resp.status_code != 200:
                 log(f"Student {student_id}: Chat failed ({resp.status_code}) - {resp.text}", "ERROR")
            else:
                 chat_resp = resp.json()
                 if "answer" in chat_resp:
                     log(f"Student {student_id}: Chat response received. Difficulty: {chat_resp.get('difficulty')}", "SUCCESS")
                 else:
                     log(f"Student {student_id}: Chat response missing answer", "WARNING")
        except Exception as e:
            log(f"Student {student_id}: Chat API error - {e}", "ERROR")

        # 2. Start Quiz (Generate) - /quiz/generate
        log(f"Student {student_id}: Generating quiz for {CHAPTER_ID}", "INFO")
        quiz_id = None
        questions = []
        try:
            resp = await client.post(f"{BASE_URL}/quiz/generate", json={
                "student_id": student_id_str,
                "subject": SUBJECT,
                "chapter_id": CHAPTER_ID,
                "num_questions": 5
            })
            if resp.status_code != 200:
                log(f"Student {student_id}: Quiz generation failed ({resp.status_code}) - {resp.text}", "ERROR")
                return
            
            quiz_data = resp.json()
            quiz_id = quiz_data.get("quiz_id")
            questions = quiz_data.get("questions", [])
            log(f"Student {student_id}: Quiz generated with {len(questions)} questions. Difficulty: {quiz_data.get('difficulty')}", "SUCCESS")
            
            if not questions:
                log(f"Student {student_id}: No questions returned", "ERROR")
                return
        except Exception as e:
             log(f"Student {student_id}: Quiz generation API error - {e}", "ERROR")
             return

        # 3. Submit Quiz (Submit) - /quiz/submit
        log(f"Student {student_id}: Submitting quiz {quiz_id}", "INFO")
        try:
            # Create answers dict {question_id: "Option A"}
            answers = {q["id"]: q["options"][0] for q in questions} 
            
            # Simulate random delay to test concurrency
            await asyncio.sleep(random.uniform(0.5, 2.0))

            resp = await client.post(f"{BASE_URL}/quiz/submit", json={
                "student_id": student_id_str,
                "quiz_id": quiz_id,
                "answers": answers,
                "time_taken": 120.5
            })
            if resp.status_code != 200:
                log(f"Student {student_id}: Quiz submission failed ({resp.status_code}) - {resp.text}", "ERROR")
            else:
                result = resp.json()
                log(f"Student {student_id}: Quiz submitted. Score: {result.get('score')}/{result.get('total')}. XP Gained: {result.get('xp_gained')}", "SUCCESS")
                
        except Exception as e:
            log(f"Student {student_id}: Quiz submission API error - {e}", "ERROR")

        # 4. Check Progress (Weak Topics)
        try:
            resp = await client.get(f"{BASE_URL}/weak_topics/{student_id_str}")
            if resp.status_code == 200:
                log(f"Student {student_id}: Weak topics checked", "SUCCESS")
            else:
                log(f"Student {student_id}: Weak topics check failed ({resp.status_code})", "WARNING")
        except Exception as e:
             log(f"Student {student_id}: Weak topics API error - {e}", "ERROR")

async def main():
    log("STARTING SYSTEM VALIDATION", "HEADER")
    
    # Wait for server to be fully ready
    async with httpx.AsyncClient() as client:
        retries = 5
        while retries > 0:
            if await test_health(client):
                break
            log("Waiting for backend...", "WARNING")
            await asyncio.sleep(2)
            retries -= 1
        
        if retries == 0:
            log("Backend not reachable after retries. Aborting.", "FAIL")
            return

    log(f"Simulating {NUM_STUDENTS} concurrent students...", "HEADER")
    
    tasks = [simulate_student_flow(i) for i in range(1, NUM_STUDENTS + 1)]
    start_time = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    log(f"Simulation completed in {duration:.2f} seconds", "HEADER")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Validation stopped by user", "WARNING")
