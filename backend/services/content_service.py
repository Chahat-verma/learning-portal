from typing import List, Dict

SUBJECTS_DATA = [
    {
        "id": "maths",
        "name": "Mathematics",
        "icon": "Calculator",
        "color": "blue",
        "chapters": [
            {"id": "real_numbers", "name": "Real Numbers", "description": "Euclid's Division, LCM & HCF"},
            {"id": "polynomials", "name": "Polynomials", "description": "Zeroes of Polynomials, Division Algorithm"},
            {"id": "pair_of_linear_equations", "name": "Linear Equations", "description": "Pair of Linear Equations in Two Variables"},
            {"id": "quadratic_equations", "name": "Quadratic Equations", "description": "Nature of Roots, Quadratic Formula"},
        ]
    },
    {
        "id": "science",
        "name": "Science",
        "icon": "Beaker",
        "color": "green",
        "chapters": [
            {"id": "chemical_reactions_and_equations", "name": "Chemical Reactions & Equations", "description": "Types of Reactions, Balancing Equations"},
            {"id": "acids_bases_and_salts", "name": "Acids, Bases & Salts", "description": "pH Scale, Properties of Acids & Bases"},
            {"id": "ch03_metals_and_nonmetals", "name": "Metals and Non-metals", "description": "Physical & Chemical Properties"},
            {"id": "carbon_and_its_compounds", "name": "Carbon and its Compounds", "description": "Covalent Bonding, Carbon Compounds"},
        ]
    },
]

def get_all_subjects() -> List[Dict]:
    return [{"id": s["id"], "name": s["name"], "icon": s["icon"], "color": s["color"]} for s in SUBJECTS_DATA]

def get_chapters_for_subject(subject_id: str) -> List[Dict]:
    for subject in SUBJECTS_DATA:
        if subject["id"] == subject_id:
            return subject["chapters"]
    return []
