import sqlite3
import json

def check_metrics():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    student = cursor.execute('SELECT * FROM students WHERE id="behavior_test_student"').fetchone()
    if student:
        print("--- Student Metrics ---")
        d = dict(student)
        print(f"Confidence: {d['confidence_score']}")
        print(f"Momentum:   {d['learning_momentum']}")
        print(f"Avg Time:   {d['avg_response_time']}")
        print(f"Streak:     {d['current_streak']}")
        print(f"Difficulty: {d['current_difficulty']}")
    else:
        print("Student not found")

    print("\n--- Topic Mastery ---")
    mastery = cursor.execute('SELECT * FROM topic_mastery WHERE student_id="behavior_test_student"').fetchall()
    for row in mastery:
        print(dict(row))

if __name__ == "__main__":
    check_metrics()
