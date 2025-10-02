#!/usr/bin/env python3
"""
Fix the transcription_path in the existing record to include the bucket name
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

def fix_transcription_path():
    """Fix the transcription_path to include the bucket name"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"🔧 Fixing transcription path for: {recording_id}")
        print("=" * 60)
        
        # 1. Get current transcription record
        response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
        
        if not response.data:
            print("❌ No transcription record found")
            return False
            
        current_record = response.data[0]
        current_path = current_record['transcription_path']
        transcription_id = current_record['transcription_id']
        
        print(f"📋 Current path: {current_path}")
        
        # 2. Check if path already includes bucket name
        if current_path.startswith('Transcription/'):
            print("✅ Path already includes bucket name - no fix needed")
            return True
            
        # 3. Update the path to include bucket name
        new_path = f"Transcription/{current_path}"
        print(f"📝 New path: {new_path}")
        
        # 4. Update the record
        update_response = supabase.table('transcription').update({
            'transcription_path': new_path
        }).eq('transcription_id', transcription_id).execute()
        
        if update_response.data:
            print("✅ Successfully updated transcription path!")
            updated_record = update_response.data[0]
            print(f"   Updated path: {updated_record['transcription_path']}")
            return True
        else:
            print("❌ Update failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def verify_path_fix():
    """Verify the path fix worked"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"\n🔍 Verifying fix for: {recording_id}")
        print("=" * 60)
        
        response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
        
        if response.data:
            record = response.data[0]
            path = record['transcription_path']
            print(f"✅ Current transcription path: {path}")
            
            if path.startswith('Transcription/'):
                print("🎉 Path is correctly formatted!")
                return True
            else:
                print("❌ Path still doesn't include bucket name")
                return False
        else:
            print("❌ No transcription record found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Transcription Path")
    print("=" * 60)
    
    success = fix_transcription_path()
    
    if success:
        verify_path_fix()
    else:
        print("❌ Path fix failed")
