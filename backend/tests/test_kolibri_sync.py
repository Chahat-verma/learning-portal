import pytest
import sqlite3
import os
from services import kolibri_service
from database import get_db_connection

# Mock Kolibri DB Path
MOCK_KOLIBRI_DB = "mock_kolibri.sqlite3"

@pytest.fixture
def mock_kolibri_db():
    """Create a mock Kolibri DB with necessary tables and data."""
    if os.path.exists(MOCK_KOLIBRI_DB):
        os.remove(MOCK_KOLIBRI_DB)
        
    conn = sqlite3.connect(MOCK_KOLIBRI_DB)
    cursor = conn.cursor()
    
    # Create table expected by kolibri_service
    cursor.execute("""
        CREATE TABLE logger_contentsummarylog (
            id INTEGER PRIMARY KEY,
            content_id TEXT,
            user_id TEXT,
            progress REAL,
            end_timestamp TIMESTAMP
        )
    """)
    
    # Insert dummy completed video
    cursor.execute("""
        INSERT INTO logger_contentsummarylog (content_id, user_id, progress, end_timestamp)
        VALUES 
        ('video_123', 'k_user_1', 1.0, '2023-01-01 12:00:00'),
        ('video_456', 'k_user_1', 0.5, '2023-01-01 12:30:00'), -- Incomplete
        ('video_789', 'k_user_1', 1.0, '2023-01-01 13:00:00')  -- Completed
    """)
    
    conn.commit()
    conn.close()
    
    # Override service config
    original_path = kolibri_service.KOLIBRI_DB_PATH
    kolibri_service.KOLIBRI_DB_PATH = MOCK_KOLIBRI_DB
    
    yield
    
    # Cleanup
    kolibri_service.KOLIBRI_DB_PATH = original_path
    if os.path.exists(MOCK_KOLIBRI_DB):
        try:
            os.remove(MOCK_KOLIBRI_DB)
        except PermissionError:
            pass

def test_kolibri_sync_flow(client, unique_student_id, mock_kolibri_db):
    """Test full sync flow with mock DB."""
    
    # 1. Initial Sync
    # We use the client endpoint to test full integration
    resp = client.post("/kolibri/sync", json={
        "student_id": unique_student_id,
        "kolibri_user_id": "k_user_1"
    })
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Should skip video_456 (incomplete) and sync 123, 789
    assert data["synced_count"] == 2
    assert data["total_xp_gained"] == 100 # 50 * 2
    
    # Verify items
    activity_ids = [item["content_id"] for item in data["items"]]
    assert "video_123" in activity_ids
    assert "video_789" in activity_ids
    assert "video_456" not in activity_ids
    
    # Verify App DB Updates
    with get_db_connection() as conn:
        # Check Sync Logs
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kolibri_sync_logs WHERE student_id = ?", (unique_student_id,))
        logs = cursor.fetchall()
        assert len(logs) == 2
        
        # Check XP (Assuming student started with 0 or we check diff)
        # Note: XP update logic adds to existing.
        # Check Mastery
        cursor.execute("SELECT * FROM topic_mastery WHERE student_id = ?", (unique_student_id,))
        mastery_rows = cursor.fetchall()
        assert len(mastery_rows) > 0
        
    # 2. Duplicate Check (Sync again)
    resp_2 = client.post("/kolibri/sync", json={
        "student_id": unique_student_id,
        "kolibri_user_id": "k_user_1"
    })
    data_2 = resp_2.json()
    
    assert data_2["synced_count"] == 0
    assert data_2["total_xp_gained"] == 0
