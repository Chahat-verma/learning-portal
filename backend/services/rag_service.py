"""
rag_service.py — Guaranteed RAG pipeline for hackathon demo.

Strategy:
1. Load ALL NCERT JSONs into memory at import time.
2. Try ChromaDB embeddings first.
3. Fallback to keyword search on in-memory index.
4. NEVER return empty context.
5. Enforce 5-step teaching format.
"""

import os
import json
import re
import requests
import logging

logger = logging.getLogger("pipeline")

# ---------------------------------------------------------------------------
# In-Memory NCERT Index (loaded at import time)
# Structure: { subject -> { chapter_id -> [{ lesson_id, content, ... }] } }
# ---------------------------------------------------------------------------
# Path: services/rag_service.py → services/ → backend/ → ICAN/ → raw/
_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)                # ICAN/
RAW_DIR = os.path.join(_PROJECT_DIR, "raw")

# Fallback: also check backend/raw in case raw is copied there
if not os.path.isdir(RAW_DIR):
    RAW_DIR = os.path.join(_BACKEND_DIR, "raw")
_NCERT_INDEX: dict[str, dict[str, list[dict]]] = {}

def _load_ncert_index():
    """Load all JSON files from raw/ into the in-memory index.
    Handles two JSON formats:
      1. Nested dict: {"chapter_id": "...", "lessons": [{...}, ...]}
      2. Flat array:  [{"chapter_id": "...", "content": "..."}, ...]
    """
    global _NCERT_INDEX
    if _NCERT_INDEX:
        return  # Already loaded

    print(f"[RAG] Looking for raw data at: {RAW_DIR}")
    print(f"[RAG] Directory exists: {os.path.isdir(RAW_DIR)}")

    if not os.path.isdir(RAW_DIR):
        logger.warning(f"Raw data directory not found: {RAW_DIR}")
        print(f"[RAG] ERROR: Raw data directory not found at {RAW_DIR}")
        return

    count = 0
    for subject_dir in os.listdir(RAW_DIR):
        subject_path = os.path.join(RAW_DIR, subject_dir)
        if not os.path.isdir(subject_path):
            continue
        for fname in os.listdir(subject_path):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(subject_path, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = json.load(f)

                # --- Handle both JSON formats ---
                if isinstance(raw, dict):
                    # Nested format: {"chapter_id": "...", "lessons": [...]}
                    ch_id = raw.get("chapter_id", "unknown")
                    subj = raw.get("subject", subject_dir).lower()
                    lessons_list = raw.get("lessons", [])
                    for lesson in lessons_list:
                        lesson.setdefault("subject", subj)
                        lesson.setdefault("chapter_id", ch_id)
                        lesson.setdefault("chapter_name", raw.get("chapter_name", ""))
                        _NCERT_INDEX.setdefault(subj, {}).setdefault(ch_id, []).append(lesson)
                        count += 1
                elif isinstance(raw, list):
                    # Flat array format: [{"chapter_id": "...", ...}, ...]
                    for lesson in raw:
                        subj = lesson.get("subject", subject_dir).lower()
                        ch_id = lesson.get("chapter_id", "unknown")
                        _NCERT_INDEX.setdefault(subj, {}).setdefault(ch_id, []).append(lesson)
                        count += 1
                else:
                    logger.warning(f"Unexpected JSON format in {fpath}")
            except Exception as e:
                logger.error(f"Failed to load {fpath}: {e}")

    logger.info(f"NCERT Index loaded: {count} lessons across {len(_NCERT_INDEX)} subjects")
    print(f"[RAG] NCERT Index loaded: {count} lessons across {len(_NCERT_INDEX)} subjects")
    for subj, chapters in _NCERT_INDEX.items():
        ch_list = list(chapters.keys())
        print(f"[RAG]   {subj}: {ch_list} ({sum(len(v) for v in chapters.values())} lessons)")

# Load at import time
_load_ncert_index()


def _resolve_chapter_id(subject: str, chapter_id: str) -> str:
    """Fuzzy-match a chapter_id against available chapters in the subject.
    Returns the best matching chapter_id or the original if no match found.
    """
    subject_lower = subject.lower()
    available = _NCERT_INDEX.get(subject_lower, {})
    if not available:
        return chapter_id

    # Exact match
    if chapter_id in available:
        return chapter_id

    # Substring match: check if chapter_id is a substring of any available key
    ch_lower = chapter_id.lower().replace("-", "_")
    for avail_id in available:
        if ch_lower in avail_id or avail_id in ch_lower:
            logger.info(f"[RAG] Fuzzy matched '{chapter_id}' → '{avail_id}'")
            return avail_id

    # Token overlap match: split into words and find best overlap
    ch_tokens = set(ch_lower.split("_"))
    best_match = None
    best_score = 0
    for avail_id in available:
        avail_tokens = set(avail_id.lower().split("_"))
        overlap = len(ch_tokens & avail_tokens)
        if overlap > best_score:
            best_score = overlap
            best_match = avail_id

    if best_match and best_score >= 1:
        logger.info(f"[RAG] Token-matched '{chapter_id}' → '{best_match}' (score={best_score})")
        return best_match

    # No match — return first available chapter as absolute fallback
    fallback = list(available.keys())[0]
    logger.warning(f"[RAG] No match for '{chapter_id}', falling back to '{fallback}'")
    return fallback


# ---------------------------------------------------------------------------
# ChromaDB (optional — graceful fallback)
# ---------------------------------------------------------------------------
CHROMA_AVAILABLE = False
chromadb = None
SentenceTransformerEmbeddingFunction = None

try:
    import chromadb as _chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction as _STEF
    chromadb = _chromadb
    SentenceTransformerEmbeddingFunction = _STEF
    CHROMA_AVAILABLE = True
    print("[RAG] ChromaDB available.")
except Exception as e:
    print(f"[RAG] ChromaDB unavailable ({e}). Using keyword fallback only.")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "ncert_chunks"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:8b"
TOP_K = 5
MAX_DISTANCE = 0.6

_collection = None
_session = requests.Session()


def _get_collection():
    global _collection
    if not CHROMA_AVAILABLE:
        return None
    if _collection is None:
        try:
            embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            _collection = client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn,
            )
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}")
            return None
    return _collection


# ---------------------------------------------------------------------------
# Keyword Search (Fallback)
# ---------------------------------------------------------------------------
def _keyword_search(question: str, subject: str, chapter_id: str, top_k: int = 5) -> list[dict]:
    """
    Simple keyword-based retrieval from in-memory NCERT index.
    Scores each lesson block by counting matching words from the question.
    NEVER returns empty if the chapter exists.
    """
    # Resolve chapter_id via fuzzy matching
    resolved_id = _resolve_chapter_id(subject, chapter_id)
    logger.info(f"[KEYWORD] Searching: subject={subject}, chapter={chapter_id} (resolved={resolved_id})")

    # Normalize
    subject_lower = subject.lower()
    question_lower = question.lower()
    keywords = set(re.findall(r'\w+', question_lower))
    # Remove stop words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why',
                  'when', 'which', 'who', 'do', 'does', 'did', 'can', 'could', 'will',
                  'would', 'should', 'of', 'in', 'on', 'at', 'to', 'for', 'with',
                  'and', 'or', 'but', 'not', 'it', 'its', 'this', 'that', 'these',
                  'those', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she',
                  'they', 'them', 'about', 'explain', 'tell', 'describe'}
    keywords = keywords - stop_words

    # Get chapter lessons using resolved ID
    chapter_lessons = _NCERT_INDEX.get(subject_lower, {}).get(resolved_id, [])

    if not chapter_lessons:
        # Try broader search across all chapters in subject
        all_lessons = []
        for ch_id, lessons in _NCERT_INDEX.get(subject_lower, {}).items():
            all_lessons.extend(lessons)
        chapter_lessons = all_lessons

    if not chapter_lessons:
        return []

    # Score each lesson
    scored = []
    for lesson in chapter_lessons:
        content_lower = lesson.get("content", "").lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        # Bonus for title match
        title_lower = lesson.get("lesson_title", "").lower()
        score += sum(2 for kw in keywords if kw in title_lower)
        scored.append((score, lesson))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top_k, but ALWAYS return at least 1
    results = []
    for score, lesson in scored[:top_k]:
        results.append({
            "content": lesson["content"],
            "subject": lesson.get("subject", subject),
            "chapter_id": lesson.get("chapter_id", chapter_id),
            "lesson_id": lesson.get("lesson_id", "unknown"),
            "distance": max(0.01, 1.0 - (score * 0.1)),  # Fake distance for compatibility
        })

    # If keyword search found nothing relevant, return first lesson as summary
    if not results:
        fallback = chapter_lessons[0]
        results.append({
            "content": fallback["content"],
            "subject": fallback.get("subject", subject),
            "chapter_id": fallback.get("chapter_id", chapter_id),
            "lesson_id": fallback.get("lesson_id", "summary"),
            "distance": 0.9,
        })

    return results


# ---------------------------------------------------------------------------
# Retrieve (Hybrid: Embedding → Keyword)
# ---------------------------------------------------------------------------
def retrieve(question: str, subject: str, chapter_id: str) -> list[dict]:
    """
    Hybrid retrieval: try ChromaDB first, fallback to keyword search.
    NEVER returns empty if the chapter exists in NCERT.
    """
    logger.info(f"[RETRIEVE] q='{question[:50]}', subj={subject}, ch={chapter_id}")

    # 1. Try ChromaDB embedding search
    collection = _get_collection()
    if collection:
        try:
            where_filter = {
                "$and": [
                    {"subject": {"$eq": subject.lower()}},
                    {"chapter_id": {"$eq": chapter_id}},
                ]
            }
            results = collection.query(
                query_texts=[question],
                n_results=TOP_K,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            chunks = []
            if results and results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    if dist <= MAX_DISTANCE:
                        chunks.append({
                            "content": doc,
                            "subject": meta.get("subject", ""),
                            "chapter_id": meta.get("chapter_id", ""),
                            "lesson_id": meta.get("lesson_id", ""),
                            "distance": round(dist, 4),
                        })

            if chunks:
                logger.info(f"[RETRIEVE] ChromaDB returned {len(chunks)} chunks")
                return chunks
            else:
                logger.warning("[RETRIEVE] ChromaDB returned 0 qualifying chunks. Falling back to keyword.")
        except Exception as e:
            logger.error(f"[RETRIEVE] ChromaDB query error: {e}. Falling back to keyword.")

    # 2. Fallback: keyword search on in-memory index
    chunks = _keyword_search(question, subject, chapter_id, top_k=TOP_K)
    logger.info(f"[RETRIEVE] Keyword search returned {len(chunks)} chunks")
    return chunks


# ---------------------------------------------------------------------------
# System Prompt (5-Step Teaching Format)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_BASE = """You are a professional NCERT Class 10 teacher.

ABSOLUTE RULES:
1. Use ONLY the provided NCERT context below. Do NOT use any outside knowledge.
2. Do NOT guess or infer beyond what the context states.
3. If the context does not contain enough information, respond with exactly:
   "This topic is not covered in Class 10 NCERT."
4. NEVER answer the question directly. Always TEACH step-by-step.
5. ALWAYS follow this exact 5-Step Teaching Format:

Step 1: **Definition** — State the concept clearly.
Step 2: **Explanation** — Break down how it works.
Step 3: **NCERT Example** — Use an example strictly from the provided context.
Step 4: **Real-life Connection** — Relate to daily life.
Step 5: **Check Question** — Ask 1 short question to test understanding.
"""

DIFFICULTY_INSTRUCTIONS = {
    "easy": """
STYLE: Use very simple language. Short sentences. Relatable analogies.
""",
    "medium": """
STYLE: Use clear academic language. Be concise but thorough.
""",
    "hard": """
STYLE: Use precise technical terminology. Connect to broader theories. Challenge the student.
""",
}

BEHAVIORAL_MODIFIERS = {
    "encourage": "MODIFIER: The student seems unsure. Use encouraging language.",
    "revision_focus": "MODIFIER: Focus on basic definitions. Avoid complex details.",
    "advanced_challenge": "MODIFIER: Include an advanced application or edge case.",
    "slow_and_detailed": "MODIFIER: Slow down. Use more analogies and explain every term.",
}


def get_system_prompt(difficulty: str = "medium", strategy: dict = None) -> str:
    style = DIFFICULTY_INSTRUCTIONS.get(difficulty, DIFFICULTY_INSTRUCTIONS["medium"])

    behavior = ""
    if strategy:
        if strategy.get("encourage"):
            behavior += f"\n{BEHAVIORAL_MODIFIERS['encourage']}"
        mod = strategy.get("modifier")
        if mod in BEHAVIORAL_MODIFIERS:
            behavior += f"\n{BEHAVIORAL_MODIFIERS[mod]}"

    return SYSTEM_PROMPT_BASE + style + behavior


# ---------------------------------------------------------------------------
# LLM Interface
# ---------------------------------------------------------------------------
def _fallback_teaching_from_context(chunks: list[dict], chapter_id: str, subject: str, question: str = "") -> str:
    """Generate deterministic teaching response from NCERT JSON text. NEVER empty."""
    chapter_name = chapter_id.replace('_', ' ').title()
    if not chunks:
        return f"Let me explain about **{chapter_name}** in {subject.title()}.\n\nThis topic is covered in your NCERT Class 10 textbook. Please refer to the textbook for detailed explanations, examples, and practice problems."

    first = chunks[0]["content"][:600]
    second = chunks[1]["content"][:400] if len(chunks) > 1 else ""

    return f"""Here's what your NCERT textbook says about **{chapter_name}**:\n\n**Key Concept:**\n{first}\n\n{('**More Details:**' + chr(10) + second) if second else ''}\n\n**Remember:** Review the examples in your textbook for practice. Try solving the exercise questions at the end of the chapter."""


def call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama. 10s timeout, temp=0.2, max 512 tokens."""
    logger.info(f"[LLM] Calling Ollama ({model}), timeout=10s...")
    try:
        resp = _session.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 512,
                },
            },
            timeout=10,
        )
        resp.raise_for_status()
        answer = resp.json().get("response", "").strip()
        if not answer:
            logger.warning("[LLM] Ollama returned empty response.")
            return "Error: Empty response from Ollama."
        logger.info(f"[LLM] Ollama responded ({len(answer)} chars)")
        return answer
    except requests.exceptions.Timeout:
        logger.error("[LLM] Ollama timeout (10s). Will use fallback.")
        return "Error: Ollama timeout."
    except requests.exceptions.ConnectionError:
        logger.error("[LLM] Cannot connect to Ollama.")
        return "Error: Cannot connect to Ollama."
    except Exception as e:
        logger.error(f"[LLM] Unexpected error: {e}")
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Ask (Full Pipeline)
# ---------------------------------------------------------------------------
def ask(
    question: str,
    subject: str,
    chapter_id: str,
    difficulty: str = "medium",
    strategy: dict = None
) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → LLM/fallback → answer.
    NEVER crashes. NEVER returns empty.
    """
    logger.info(f"[PIPELINE] === START === question='{question[:60]}', subject={subject}, chapter={chapter_id}")

    # Stage 1: Resolve chapter
    resolved_id = _resolve_chapter_id(subject, chapter_id)
    logger.info(f"[PIPELINE] Stage 1 — Resolved: '{chapter_id}' → '{resolved_id}'")
    chapter_id = resolved_id

    # Stage 2: Retrieve context
    logger.info(f"[PIPELINE] Stage 2 — Retrieving context...")
    chunks = retrieve(question, subject, chapter_id)
    logger.info(f"[PIPELINE] Stage 2 — Got {len(chunks)} chunks")

    if not chunks:
        logger.error("[PIPELINE] Stage 2 — ZERO chunks! Using chapter-level fallback.")
        return {
            "answer": _fallback_teaching_from_context([], chapter_id, subject, question),
            "sources": [],
            "difficulty": difficulty,
        }

    # Stage 3: Build prompt
    logger.info(f"[PIPELINE] Stage 3 — Building prompt (difficulty={difficulty})...")
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f"[Source {i} — {c['lesson_id']}]\n{c['content']}")
    context = "\n\n".join(context_parts)

    system_prompt = get_system_prompt(difficulty, strategy)
    prompt = f"""{system_prompt}

--- NCERT CONTEXT ---
{context[:3000]}
--- END CONTEXT ---

Student's question: {question}

Teach:"""

    # Stage 4: Call LLM (10s timeout)
    logger.info(f"[PIPELINE] Stage 4 — Calling Ollama (10s timeout)...")
    answer = call_ollama(prompt)

    # Stage 5: Fallback if LLM fails
    if "Error" in answer or not answer.strip():
        logger.warning(f"[PIPELINE] Stage 5 — LLM FAILED ('{answer[:50]}'), using JSON fallback.")
        answer = _fallback_teaching_from_context(chunks, chapter_id, subject, question)
    else:
        logger.info(f"[PIPELINE] Stage 5 — LLM OK ({len(answer)} chars)")

    # Stage 6: Build sources
    sources = [
        {
            "subject": c["subject"],
            "chapter_id": c["chapter_id"],
            "lesson_id": c["lesson_id"],
        }
        for c in chunks
    ]

    logger.info(f"[PIPELINE] === DONE === ({len(answer)} chars, {len(sources)} sources)")
    return {"answer": answer, "sources": sources, "difficulty": difficulty}
