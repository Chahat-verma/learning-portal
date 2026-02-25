import requests
import os
import sys

# Default URL
API_URL = "http://localhost:8000/kolibri/sync"

def trigger_sync(student_id, kolibri_user_id=None):
    payload = {
        "student_id": student_id,
        "kolibri_user_id": kolibri_user_id
    }
    
    try:
        print(f"🔄 Triggering Sync for Student: {student_id}...")
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Sync Verified!")
            print(f"Synced Videos: {data['synced_count']}")
            print(f"XP Gained: {data['total_xp_gained']}")
            
            if data['items']:
                print("\n[Details]")
                for item in data['items']:
                    print(f"- {item['content_id']} ({item['subtopic']}): +{item['xp']} XP")
            
            if data.get('suggested_quiz'):
                print("\n📝 Suggested Micro-Quiz Generated!")
                print(f"Quiz ID: {data['suggested_quiz'].get('quiz_id')}")
        else:
            print(f"❌ Sync Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the backend is running at http://localhost:8000")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sync_kolibri.py <student_id> [kolibri_user_id]")
        sys.exit(1)
        
    s_id = sys.argv[1]
    k_id = sys.argv[2] if len(sys.argv) > 2 else "kolibri_user_1"
    
    trigger_sync(s_id, k_id)
