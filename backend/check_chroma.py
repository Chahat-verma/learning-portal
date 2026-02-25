import chromadb
import os

try:
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db_test")
    print("ChromaDB Initialized Successfully")
except Exception as e:
    print(f"Error: {e}")
