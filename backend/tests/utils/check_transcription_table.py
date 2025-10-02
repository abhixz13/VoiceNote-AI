#!/usr/bin/env python3
"""
Check the transcription table schema and data
"""
import os
import sys
import logging
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("❌ No .env file found")
        sys.exit(1)
except ImportError:
    print("❌ python-dotenv not available")
    sys.exit(1)

def check_transcription_table():
    """Check the transcription table schema and existing data"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        print("🔍 Checking transcription table...")
        print("=" * 50)
        
        # 1. Check if table exists and get all records
        try:
            response = supabase.table('transcription').select('*').execute()
            print(f"✅ Transcription table exists with {len(response.data)} records")
            
            if response.data:
                print("📋 Existing records:")
                for i, record in enumerate(response.data):
                    print(f"   {i+1}. ID: {record.get('transcription_id')}")
                    print(f"      Recording ID: {record.get('recording_id')}")
                    print(f"      User ID: {record.get('user_id')}")
                    print(f"      Path: {record.get('transcription_path')}")
                    print(f"      Created: {record.get('created_at')}")
                    print()
            else:
                print("📋 No records found in transcription table")
                
        except Exception as e:
            print(f"❌ Error accessing transcription table: {e}")
            return
        
        # 2. Try to understand the schema by attempting an insert with minimal data
        print("🔍 Testing table schema...")
        try:
            # Test insert to see what fields are required
            test_data = {
                'recording_id': 'test-schema-check',
                'user_id': 'test-user',
                'transcription_path': 'test/path.txt'
            }
            
            # This will likely fail, but the error will tell us about the schema
            response = supabase.table('transcription').insert(test_data).execute()
            print("✅ Test insert successful (unexpected)")
            
            # Clean up the test record
            supabase.table('transcription').delete().eq('recording_id', 'test-schema-check').execute()
            
        except Exception as e:
            print(f"📝 Schema test error (this helps us understand the schema): {e}")
            
            # Parse the error to understand what's missing
            error_str = str(e)
            if 'transcription_id' in error_str and 'not-null constraint' in error_str:
                print("💡 Issue identified: transcription_id column requires a value but should be auto-generated")
            elif 'violates not-null constraint' in error_str:
                print("💡 Issue: Some required column is missing a value")
            
        # 3. Check what our recording_id should have
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        print(f"\n🔍 Checking for our specific recording: {recording_id}")
        try:
            response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
            if response.data:
                print(f"✅ Found transcription record for our recording:")
                record = response.data[0]
                for key, value in record.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ No transcription record found for our recording")
        except Exception as e:
            print(f"❌ Error checking specific recording: {e}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Checking Transcription Table Schema")
    print("=" * 50)
    check_transcription_table()
