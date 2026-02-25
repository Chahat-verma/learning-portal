import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add backend to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
import database

TEST_DB = "test_students.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Override database path
    database.DB_NAME = TEST_DB
    database.DB_PATH = TEST_DB # Since it's in the same dir as execution or just use filename
    # Better to use absolute path to avoid confusion
    database.DB_PATH = os.path.join(os.path.dirname(__file__), TEST_DB)
    
    # Initialize DB
    if os.path.exists(database.DB_PATH):
        os.remove(database.DB_PATH)
    
    database.init_db()
    
    yield
    
    # Cleanup
    if os.path.exists(database.DB_PATH):
        try:
            os.remove(database.DB_PATH)
        except PermissionError:
            pass # Sometimes file is locked on Windows

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture
def unique_student_id():
    import uuid
    return f"student_{uuid.uuid4().hex[:8]}"
