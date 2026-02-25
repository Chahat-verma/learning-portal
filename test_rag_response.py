import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.services.rag_service import ask

print("\n--- Testing RAG Response for 5-Step Format ---\n")

# Query
q = "What is Euclid's Division Lemma?"
print(f"Question: {q}\n")

try:
    # Force real RAG (ensure CHROMA_AVAILABLE is True if possible, but ask() handles it)
    response = ask(q, "Mathematics", "real_numbers", difficulty="easy")
    
    print("--- RAW RESPONSE ---")
    print(response["answer"])
    print("\n--------------------")
    
    required_steps = ["Step 1:", "Step 2:", "Step 3:", "Step 4:", "Step 5:"]
    missing = [s for s in required_steps if s not in response["answer"]]
    
    if not missing:
        print("\n[SUCCESS] Response follows the 5-Step Teaching Format.")
    else:
        print(f"\n[FAIL] Missing steps: {missing}")
        
except Exception as e:
    print(f"\n[ERROR] {e}")
