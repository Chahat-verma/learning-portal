import subprocess
import sys
import os
import time

def run_tests():
    print("="*60)
    print("ICAN - Offline AI Learning Engine - Validation Suite")
    print("="*60)
    
    start_time = time.time()
    
    # Run pytest
    # capture_output=True creates issues with some terminals, using simple call
    # We want to see the output live or capture it? Let's capture.
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
        
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*60)
    print("VALIDATION REPORT")
    print("="*60)
    
    if result.returncode == 0:
        print("✅ SYSTEM STABILITY: PASSED")
        print("✅ LOGICAL CONSISTENCY: PASSED")
        print("✅ DETERMINISTIC BEHAVIOR: PASSED")
        print(f"⏱️  Duration: {duration:.2f}s")
        print("\nAll tests passed successfully. The system is ready for deployment.")
        return 0
    else:
        print("❌ SYSTEM STABILITY: FAILED")
        print("❌ LOGICAL CONSISTENCY: FAILED")
        print(f"⏱️  Duration: {duration:.2f}s")
        print("\nSome tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
