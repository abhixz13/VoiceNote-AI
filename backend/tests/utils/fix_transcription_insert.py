#!/usr/bin/env python3
"""
Fix the transcription table insertion issue
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

def fix_transcription_insert():
    """Manually insert the transcription record that should have been created"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"🔧 Fixing transcription record for: {recording_id}")
        print("=" * 60)
        
        # 1. First, get the user_id from the recordings table
        print("🔍 Getting user_id from recordings table...")
        recording_response = supabase.table('recordings').select('user_id').eq('recording_id', recording_id).execute()
        
        if not recording_response.data:
            print(f"❌ Recording {recording_id} not found in recordings table")
            return
            
        user_id = recording_response.data[0]['user_id']
        print(f"✅ Found user_id: {user_id}")
        
        # 2. Check if transcription record already exists
        print("🔍 Checking if transcription record already exists...")
        existing_response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
        
        if existing_response.data:
            print("✅ Transcription record already exists:")
            record = existing_response.data[0]
            for key, value in record.items():
                print(f"   {key}: {value}")
            return
        
        # 3. Insert the transcription record
        print("📝 Inserting transcription record...")
        transcription_path = f"{recording_id}/transcription.txt"
        
        insert_data = {
            'recording_id': recording_id,
            'user_id': user_id,
            'transcription_path': transcription_path
        }
        
        try:
            response = supabase.table('transcription').insert(insert_data).execute()
            
            if response.data:
                print("✅ Successfully inserted transcription record!")
                record = response.data[0]
                print(f"   Transcription ID: {record.get('transcription_id')}")
                print(f"   Recording ID: {record.get('recording_id')}")
                print(f"   User ID: {record.get('user_id')}")
                print(f"   Path: {record.get('transcription_path')}")
                print(f"   Created: {record.get('created_at')}")
                
                # 4. Update the recording status to 'transcribed'
                print("📝 Updating recording status to 'transcribed'...")
                update_response = supabase.table('recordings').update({
                    'status': 'transcribed'
                }).eq('recording_id', recording_id).execute()
                
                if update_response.data:
                    print("✅ Successfully updated recording status!")
                else:
                    print("⚠️  Recording status update may have failed")
                    
            else:
                print("❌ Insert appeared successful but no data returned")
                
        except Exception as insert_error:
            print(f"❌ Error inserting transcription record: {insert_error}")
            
            # Let's try to understand what went wrong
            error_str = str(insert_error)
            if 'uuid' in error_str.lower():
                print("💡 The issue might be with UUID format requirements")
            elif 'not-null constraint' in error_str:
                print("💡 Some required field is missing")
            elif 'foreign key' in error_str:
                print("💡 Foreign key constraint issue")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔧 Fixing Transcription Table Insert")
    print("=" * 60)
    fix_transcription_insert()
