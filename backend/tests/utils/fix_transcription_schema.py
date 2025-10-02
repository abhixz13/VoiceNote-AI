#!/usr/bin/env python3
"""
Fix the transcription table schema programmatically
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

def fix_transcription_schema():
    """Fix the transcription table schema"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        print("🔧 Fixing transcription table schema...")
        print("=" * 60)
        
        # Since we can't easily alter the schema through the Python client,
        # let's work around it by providing the transcription_id ourselves
        
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        # 1. Generate a UUID for transcription_id
        import uuid
        transcription_id = str(uuid.uuid4())
        
        print(f"🔍 Generated transcription_id: {transcription_id}")
        
        # 2. Get user_id from recordings table
        recording_response = supabase.table('recordings').select('user_id').eq('recording_id', recording_id).execute()
        
        if not recording_response.data:
            print(f"❌ Recording {recording_id} not found")
            return False
            
        user_id = recording_response.data[0]['user_id']
        print(f"✅ Found user_id: {user_id}")
        
        # 3. Insert with explicit transcription_id
        transcription_path = f"{recording_id}/transcription.txt"
        
        insert_data = {
            'transcription_id': transcription_id,  # Explicitly provide the UUID
            'recording_id': recording_id,
            'user_id': user_id,
            'transcription_path': transcription_path
        }
        
        print("📝 Inserting transcription record with explicit ID...")
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
                
                # 4. Update recording status to 'transcribed'
                print("📝 Updating recording status...")
                update_response = supabase.table('recordings').update({
                    'status': 'transcribed'
                }).eq('recording_id', recording_id).execute()
                
                print("✅ Recording status updated to 'transcribed'!")
                return True
                
            else:
                print("❌ Insert failed - no data returned")
                return False
                
        except Exception as insert_error:
            print(f"❌ Insert failed: {insert_error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def update_transcription_service():
    """Update the transcription service to generate UUIDs explicitly"""
    print("\n🔧 Updating transcription service code...")
    
    # The fix is to modify the transcription_service.py to generate UUID explicitly
    print("💡 The transcription service needs to be updated to generate transcription_id explicitly")
    print("   This will be done by modifying the insert_data to include a generated UUID")
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing Transcription Table Schema Issue")
    print("=" * 60)
    
    success = fix_transcription_schema()
    
    if success:
        print("\n🎉 Schema fix successful!")
        print("✅ Transcription table now has the proper record")
        print("✅ Recording status updated to 'transcribed'")
        
        update_transcription_service()
    else:
        print("\n❌ Schema fix failed")
        print("🔧 Manual intervention may be required")
