"""
ingest.py — Load NCERT JSON chapters, chunk content, store in ChromaDB.

Usage:
    cd backend/
    python ingest.py
"""

import json
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "ncert_chunks"
CHUNK_MIN_WORDS = 500
CHUNK_MAX_WORDS = 700
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_lessons(filepath: str) -> list[dict]:
    """Load a JSON file and return a flat list of lesson dicts."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Skipping invalid/empty JSON: {filepath}")
        return []

    # Format 1: top-level list (maths)
    if isinstance(data, list):
        return data

    # Format 2: dict with nested "lessons" (science)
    if isinstance(data, dict) and "lessons" in data:
        parent_subject = data.get("subject", "").lower()
        parent_chapter_id = data.get("chapter_id", "")
        lessons = []
        for lesson in data["lessons"]:
            lesson.setdefault("subject", parent_subject)
            lesson.setdefault("chapter_id", parent_chapter_id)
            lessons.append(lesson)
        return lessons

    return []


def chunk_text(text: str, min_words: int = CHUNK_MIN_WORDS, max_words: int = CHUNK_MAX_WORDS) -> list[str]:
    """Split text into chunks of min_words–max_words by word boundaries."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end
    return chunks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def ingest():
    print(f"Loading from: {os.path.abspath(RAW_DIR)}")

    # Collect all lessons
    all_lessons: list[dict] = []
    for root, _, files in os.walk(RAW_DIR):
        for fname in sorted(files):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            lessons = load_lessons(fpath)
            print(f"  {fname}: {len(lessons)} lessons")
            all_lessons.extend(lessons)

    print(f"\nTotal lessons loaded: {len(all_lessons)}")

    # Chunk
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    chunk_idx = 0

    for lesson in all_lessons:
        content = lesson.get("content", "")
        if not content.strip():
            continue

        subject = lesson.get("subject", "unknown").lower()
        chapter_id = lesson.get("chapter_id", "unknown")
        lesson_id = lesson.get("lesson_id", "unknown")

        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "subject": subject,
                "chapter_id": chapter_id,
                "lesson_id": lesson_id,
                "chunk_index": i,
            })
            ids.append(f"chunk_{chunk_idx}")
            chunk_idx += 1

    print(f"Total chunks created: {chunk_idx}")

    # Store in ChromaDB
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete old collection if exists (idempotent re-ingestion)
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection.")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    # ChromaDB limits batch size; insert in batches of 100
    BATCH_SIZE = 100
    for i in range(0, len(documents), BATCH_SIZE):
        end = min(i + BATCH_SIZE, len(documents))
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end],
        )
        print(f"  Inserted batch {i // BATCH_SIZE + 1} ({end}/{len(documents)})")

    print(f"\nIngestion complete. Collection '{COLLECTION_NAME}' has {collection.count()} chunks.")
    print(f"ChromaDB persisted at: {os.path.abspath(CHROMA_DIR)}")


if __name__ == "__main__":
    ingest()
