import requests
import json

def check_ollama():
    try:
        # Check tags
        print("Checking Ollama tags...")
        resp = requests.get("http://localhost:11434/api/tags")
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"Ollama is up. Found {len(models)} models.")
            for m in models:
                print(f" - {m.get('name')}")
        else:
            print(f"Ollama returned status {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")

if __name__ == "__main__":
    check_ollama()
