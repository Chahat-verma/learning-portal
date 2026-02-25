"""Quick verification: test that all chapters return real content, not 'not covered in NCERT'"""
from services.rag_service import ask, _NCERT_INDEX

results = []
# Test all science chapters
for ch_id in _NCERT_INDEX.get("science", {}):
    r = ask("What is this chapter about?", "science", ch_id, difficulty="medium")
    status = "FAIL" if "not covered" in r["answer"].lower() else "OK"
    results.append(f"science/{ch_id}: {status} ({len(r['sources'])} sources)")

# Test all maths chapters
for ch_id in _NCERT_INDEX.get("maths", {}):
    r = ask("What is this chapter about?", "maths", ch_id, difficulty="medium")
    status = "FAIL" if "not covered" in r["answer"].lower() else "OK"
    results.append(f"maths/{ch_id}: {status} ({len(r['sources'])} sources)")

# Test fuzzy matching (old IDs should still work)
for old_id, subject in [("acids_bases", "science"), ("chemical_reactions", "science"), ("linear_equations", "maths")]:
    r = ask("Test question", subject, old_id, difficulty="medium")
    status = "FAIL" if "not covered" in r["answer"].lower() else "OK"
    results.append(f"FUZZY {subject}/{old_id}: {status} ({len(r['sources'])} sources)")

with open("verify_results.txt", "w") as f:
    for line in results:
        f.write(line + "\n")
        print(line)

print(f"\nTotal: {sum(1 for r in results if 'OK' in r)}/{len(results)} passed")
