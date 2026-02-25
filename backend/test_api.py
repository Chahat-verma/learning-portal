import requests
import json

url = "http://localhost:8000/ask"
payload = {
    "question": "What is Euclid's Division Lemma?",
    "subject": "maths",
    "chapter_id": "real_numbers"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    with open("response_log.txt", "w", encoding="utf-8") as f:
        f.write(f"Status: {response.status_code}\n")
        f.write(f"Answer: {data.get('answer', 'No answer key')}\n")
        f.write(f"Full JSON: {json.dumps(data, indent=2)}")
    print("Logged to response_log.txt")
except Exception as e:
    print(f"Error: {e}")
