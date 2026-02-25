import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama3:8b",
    "prompt": "Why is the sky blue?",
    "stream": False
}

try:
    print(f"Sending request to {url} with model {payload['model']}...")
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
