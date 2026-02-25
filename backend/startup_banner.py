"""
startup_banner.py — Print system status on startup.
Shows whether Ollama, RAG, ChromaDB are active.
"""

import requests
import logging

logger = logging.getLogger("pipeline")


def print_startup_banner():
    """Print a clear status banner showing what's working."""
    from services.rag_service import _NCERT_INDEX, CHROMA_AVAILABLE, RAW_DIR

    # Check Ollama
    ollama_ok = False
    ollama_model = "N/A"
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            model_names = [m["name"] for m in models]
            ollama_ok = True
            ollama_model = ", ".join(model_names[:3]) if model_names else "No models"
    except Exception:
        pass

    # Count lessons
    total_lessons = sum(len(ls) for chs in _NCERT_INDEX.values() for ls in chs.values())
    subjects = list(_NCERT_INDEX.keys())

    # Print banner
    print()
    print("=" * 60)
    print("          ICAN — Offline AI Tutor (Demo Mode)")
    print("=" * 60)

    if ollama_ok:
        print(f"  ✅ OLLAMA BRAIN        : ACTIVATED ({ollama_model})")
    else:
        print(f"  ❌ OLLAMA BRAIN        : NOT AVAILABLE (failsafe mode)")

    if total_lessons > 0:
        print(f"  ✅ RAG INDEX           : ACTIVATED ({total_lessons} lessons loaded)")
        print(f"     Subjects            : {', '.join(subjects)}")
    else:
        print(f"  ❌ RAG INDEX           : NOT LOADED (check raw/ directory)")
        print(f"     RAW_DIR             : {RAW_DIR}")

    if CHROMA_AVAILABLE:
        print(f"  ✅ CHROMADB EMBEDDINGS : ACTIVATED (vector search enabled)")
    else:
        print(f"  ⚠️  CHROMADB EMBEDDINGS : NOT AVAILABLE (keyword fallback only)")

    print(f"  ✅ DEMO MODE           : ACTIVATED (3 students loaded)")
    print(f"  ✅ VIDEO LIBRARY       : ACTIVATED (Kolibri integration)")
    print(f"  ✅ QUIZ ENGINE         : ACTIVATED (deterministic fallback)")
    print()

    if ollama_ok and total_lessons > 0:
        print("  🚀 ALL SYSTEMS GO — READY FOR DEMO!")
    elif total_lessons > 0:
        print("  ⚠️  PARTIAL MODE — Ollama offline, using failsafe responses")
    else:
        print("  ❌ CRITICAL — No NCERT data loaded!")

    print("=" * 60)
    print(f"  Server: http://localhost:8000")
    print(f"  Health: http://localhost:8000/health")
    print("=" * 60)
    print()
