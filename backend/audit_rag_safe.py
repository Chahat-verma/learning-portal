import os
import json
import sys

# ---------------------------------------------------------------------------
# Config (Mirrored from rag_service.py)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "ncert_chunks"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_DISTANCE = 0.6

def size_fmt(num):
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}TB"

print("\n=== RAG DIAGNOSTIC REPORT ===\n")

# 1. Source Data Audit
print(f"1. Source Data Audit")
print(f"   Directory: {RAW_DIR}")
if os.path.exists(RAW_DIR):
    json_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if not json_files:
        print("   [!] No JSON files found in raw directory.")
    else:
        for f in json_files:
            fpath = os.path.join(RAW_DIR, f)
            size = os.path.getsize(fpath)
            print(f"   - {f} ({size_fmt(size)})")
            try:
                with open(fpath, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    count = len(data) if isinstance(data, list) else len(data.get("lessons", []))
                    print(f"     -> Contains {count} lessons/items")
            except Exception as e:
                print(f"     -> [!] Read Error: {e}")
else:
    print("   [!] Raw directory does not exist.")

print("\n2. Vector Database Storage")
print(f"   Path: {CHROMA_DIR}")
if os.path.exists(CHROMA_DIR):
    print("   [OK] Directory exists.")
    # Check for sqlite file
    sqlite_path = os.path.join(CHROMA_DIR, "chroma.sqlite3")
    if os.path.exists(sqlite_path):
        print(f"   [OK] Database file found ({size_fmt(os.path.getsize(sqlite_path))})")
    else:
        print("   [!] chroma.sqlite3 not found (DB might be empty or using different backend)")
else:
    print("   [!] ChromaDB directory NOT found. (Ingestion likely never ran)")

print("\n3. Runtime Inspection")
try:
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    print(f"   [OK] ChromaDB {chromadb.__version__} imported successfully.")
    
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    try:
        coll = client.get_collection(COLLECTION_NAME)
        count = coll.count()
        print(f"   Collection: '{COLLECTION_NAME}'")
        print(f"   Total Documents: {count}")
        
        if count > 0:
            print("\n   --- Example Chunks (Top 3) ---")
            results = coll.get(limit=3, include=["documents", "metadatas"])
            for i in range(len(results["ids"])):
                print(f"   [{i+1}] ID: {results['ids'][i]}")
                print(f"       Metadata: {results['metadatas'][i]}")
                print(f"       Content: {results['documents'][i][:100]}...") # Truncate
                print("")
        else:
            print("   [!] Collection is empty.")
            
    except ValueError: # Collection not found
        print(f"   [!] Collection '{COLLECTION_NAME}' does not exist.")
    except Exception as e:
        print(f"   [!] Error accessing collection: {e}")

except ImportError:
    print("   [FAIL] Could not import 'chromadb'.")
    print("   Analysis: The current Python environment likely cannot run ChromaDB.")
    print("   Configured Fallback: System is likely running in MOCK MODE.")
except Exception as e:
    print(f"   [FAIL] Runtime Error: {e}")

print("\n4. Configuration (Static Audit)")
print(f"   Embedding Model: {EMBEDDING_MODEL}")
print(f"   Similarity Threshold: {MAX_DISTANCE} (L2)")
print("==============================\n")
