#!/usr/bin/env python3
"""
Simple test runner for the end-to-end integration test
"""
import os
import sys
import subprocess

def run_end_to_end_test():
    """Run the end-to-end integration test"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the test file
    test_file = os.path.join(script_dir, 'tests', 'integration', 'test_end_to_end_pipeline.py')
    
    print("🚀 Running VoiceNote AI End-to-End Integration Test")
    print("=" * 60)
    print(f"Test file: {test_file}")
    print("=" * 60)
    
    try:
        # Run the test
        result = subprocess.run([sys.executable, test_file], 
                              cwd=script_dir,
                              capture_output=False,
                              text=True)
        
        if result.returncode == 0:
            print("\n🎉 Test completed successfully!")
            return True
        else:
            print(f"\n❌ Test failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = run_end_to_end_test()
    sys.exit(0 if success else 1)
