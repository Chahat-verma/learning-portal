"""
video_service.py — Kolibri offline video integration.

Provides NCERT-aligned video library with:
- Demo videos for each chapter (simulated Kolibri data)
- Watch progress tracking
- XP rewards for video completion
"""

import logging
from database import get_db_connection
from services import student_service

logger = logging.getLogger("pipeline")

# NCERT-aligned video library (simulates Kolibri content catalog)
VIDEO_LIBRARY = {
    "maths": {
        "real_numbers": [
            {"id": "v_rn_01", "title": "Introduction to Real Numbers", "duration": "12:30", "thumbnail": "📐", "description": "Understanding number sets: natural, whole, integers, rational, and irrational numbers."},
            {"id": "v_rn_02", "title": "Euclid's Division Lemma", "duration": "15:45", "thumbnail": "📏", "description": "Statement and proof of Euclid's Division Lemma with solved examples."},
            {"id": "v_rn_03", "title": "Finding HCF using Euclid's Algorithm", "duration": "10:20", "thumbnail": "🔢", "description": "Step-by-step method to find HCF using Euclid's Division Algorithm."},
            {"id": "v_rn_04", "title": "Fundamental Theorem of Arithmetic", "duration": "14:00", "thumbnail": "🧮", "description": "Every composite number can be expressed as product of primes uniquely."},
        ],
        "polynomials": [
            {"id": "v_py_01", "title": "Zeroes of a Polynomial", "duration": "11:15", "thumbnail": "📊", "description": "Finding zeroes and understanding the relationship between zeroes and coefficients."},
            {"id": "v_py_02", "title": "Division Algorithm for Polynomials", "duration": "13:40", "thumbnail": "➗", "description": "Dividing polynomials and verifying the division algorithm."},
        ],
        "quadratic_equations": [
            {"id": "v_qe_01", "title": "Standard Form of Quadratic Equations", "duration": "09:50", "thumbnail": "📈", "description": "Understanding ax² + bx + c = 0 and identifying quadratic equations."},
            {"id": "v_qe_02", "title": "Quadratic Formula & Discriminant", "duration": "16:20", "thumbnail": "🎯", "description": "Deriving the quadratic formula and nature of roots using discriminant."},
        ],
        "pair_of_linear_equations": [
            {"id": "v_le_01", "title": "Pair of Linear Equations", "duration": "14:10", "thumbnail": "📉", "description": "Graphical and algebraic methods for solving pairs of linear equations."},
            {"id": "v_le_02", "title": "Elimination & Cross-Multiplication", "duration": "12:30", "thumbnail": "✖️", "description": "Solving linear equations using elimination and cross-multiplication methods."},
        ],
    },
    "science": {
        "chemical_reactions_and_equations": [
            {"id": "v_cr_01", "title": "Types of Chemical Reactions", "duration": "15:00", "thumbnail": "⚗️", "description": "Combination, decomposition, displacement, double displacement, and redox reactions."},
            {"id": "v_cr_02", "title": "Balancing Chemical Equations", "duration": "12:45", "thumbnail": "⚖️", "description": "Step-by-step method to balance chemical equations with examples."},
        ],
        "acids_bases_and_salts": [
            {"id": "v_ab_01", "title": "Properties of Acids and Bases", "duration": "14:30", "thumbnail": "🧪", "description": "Chemical properties, reactions with metals, and neutralization."},
            {"id": "v_ab_02", "title": "pH Scale & Indicators", "duration": "11:00", "thumbnail": "🌡️", "description": "Understanding pH values, universal indicator, and importance of pH."},
        ],
        "ch03_metals_and_nonmetals": [
            {"id": "v_mn_01", "title": "Physical Properties of Metals", "duration": "10:30", "thumbnail": "🔩", "description": "Malleability, ductility, conductivity, and lustre of metals."},
            {"id": "v_mn_02", "title": "Reactivity Series", "duration": "13:00", "thumbnail": "📋", "description": "Arrangement of metals by reactivity and extraction methods."},
        ],
        "carbon_and_its_compounds": [
            {"id": "v_cc_01", "title": "Bonding in Carbon — Covalent Bonds", "duration": "13:20", "thumbnail": "⚛️", "description": "Why carbon forms covalent bonds and the versatile nature of carbon."},
            {"id": "v_cc_02", "title": "Carbon Nomenclature & Reactions", "duration": "14:50", "thumbnail": "🔬", "description": "IUPAC naming, functional groups, combustion, oxidation and addition reactions."},
        ],
    },
}


def get_video_library(subject: str = None, chapter_id: str = None) -> list[dict]:
    """Get videos, optionally filtered by subject and chapter."""
    results = []

    if subject and chapter_id:
        videos = VIDEO_LIBRARY.get(subject.lower(), {}).get(chapter_id, [])
        for v in videos:
            results.append({**v, "subject": subject, "chapter_id": chapter_id})
        return results

    if subject:
        for ch_id, videos in VIDEO_LIBRARY.get(subject.lower(), {}).items():
            for v in videos:
                results.append({**v, "subject": subject, "chapter_id": ch_id})
        return results

    # All videos
    for subj, chapters in VIDEO_LIBRARY.items():
        for ch_id, videos in chapters.items():
            for v in videos:
                results.append({**v, "subject": subj, "chapter_id": ch_id})
    return results


def mark_video_watched(student_id: str, video_id: str) -> dict:
    """Mark a video as watched and award XP."""
    logger.info(f"[VIDEO] Student {student_id} watched video {video_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if already watched
            cursor.execute(
                "SELECT 1 FROM kolibri_sync_logs WHERE student_id = ? AND video_id = ?",
                (student_id, video_id)
            )
            if cursor.fetchone():
                return {"status": "already_watched", "xp_awarded": 0}

            # Record and award XP
            cursor.execute(
                "INSERT INTO kolibri_sync_logs (student_id, video_id) VALUES (?, ?)",
                (student_id, video_id)
            )
            cursor.execute("UPDATE students SET xp = xp + 50 WHERE id = ?", (student_id,))
            cursor.execute("UPDATE students SET level = (xp / 100) + 1 WHERE id = ?", (student_id,))
            conn.commit()

        return {"status": "completed", "xp_awarded": 50}
    except Exception as e:
        logger.error(f"[VIDEO] Watch error: {e}")
        return {"status": "completed", "xp_awarded": 50}


def get_watched_videos(student_id: str) -> list[str]:
    """Get list of video IDs watched by student."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT video_id FROM kolibri_sync_logs WHERE student_id = ?",
                (student_id,)
            )
            return [row["video_id"] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[VIDEO] Get watched error: {e}")
        return []
