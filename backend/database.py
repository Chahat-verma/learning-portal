import sqlite3
import os
from contextlib import contextmanager

DB_NAME = "students.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)

@contextmanager
def get_db_connection():
    """
    Context manager for SQLite database connection.
    Ensures connection is closed properly.
    Uses check_same_thread=False for FastAPI concurrency.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    
    # Enable Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Enforce Foreign Key constraints
    conn.execute("PRAGMA foreign_keys=ON")
    
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables."""
    print(f"Initializing database at {DB_PATH}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                current_difficulty TEXT DEFAULT 'easy',
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                last_topic TEXT,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        # Student topics table (for weak topic detection)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_topics (
                student_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                correct INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                PRIMARY KEY (student_id, topic),
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        # Topic Mastery table (Granular tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_mastery (
                student_id TEXT NOT NULL,
                subtopic TEXT NOT NULL,
                mastery_score REAL DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0,
                PRIMARY KEY (student_id, subtopic),
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        # Quizzes table (stores generated questions for grading)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                chapter_id TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        # Quiz attempts table (tracks scores)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        # Kolibri Sync Logs (prevents duplicate rewards)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kolibri_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                content_id TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id),
                UNIQUE(student_id, video_id)
            )
        ''')

        # --- Safe migrations for existing databases ---
        migrations = [
            ("students", "current_streak", "INTEGER DEFAULT 0"),
            ("students", "wrong_streak", "INTEGER DEFAULT 0"),
            ("students", "last_topic", "TEXT"),
            # Behavioral Layer Migrations
            ("students", "avg_response_time", "REAL DEFAULT 0"),
            ("students", "confidence_score", "REAL DEFAULT 0.5"),
            ("students", "learning_momentum", "REAL DEFAULT 0"),
        ]
        for table, col, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # Column already exists

        conn.commit()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
