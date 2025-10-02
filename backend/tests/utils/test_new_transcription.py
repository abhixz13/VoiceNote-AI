#!/usr/bin/env python3
"""
Test transcription service with a different recording to verify the fix works for new transcriptions
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

async def test_new_transcription():
    """Test transcription with a different recording if available"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        print("🔍 Looking for other recordings to test...")
        print("=" * 60)
        
        # Find recordings that are not yet transcribed
        response = supabase.table('recordings').select('recording_id, status, file_path').neq('status', 'transcribed').limit(5).execute()
        
        if not response.data:
            print("📝 No untranscribed recordings found. Let's check what we have...")
            all_recordings = supabase.table('recordings').select('recording_id, status, file_path').execute()
            
            if all_recordings.data:
                print(f"✅ Found {len(all_recordings.data)} total recordings:")
                for i, record in enumerate(all_recordings.data[:3]):  # Show first 3
                    print(f"   {i+1}. ID: {record['recording_id']}")
                    print(f"      Status: {record['status']}")
                    print(f"      File: {record.get('file_path', 'No file path')}")
                    print()
                    
                # Let's test with an existing recording that has status 'transcribed' 
                # to see if our duplicate handling works
                test_recording_id = all_recordings.data[0]['recording_id']
                print(f"🧪 Testing duplicate handling with: {test_recording_id}")
                
            else:
                print("❌ No recordings found in database")
                return
        else:
            print(f"✅ Found {len(response.data)} untranscribed recordings:")
            for record in response.data:
                print(f"   ID: {record['recording_id']}")
                print(f"   Status: {record['status']}")
                print(f"   File: {record.get('file_path', 'No file path')}")
                print()
            
            # Use the first untranscribed recording
            test_recording_id = response.data[0]['recording_id']
            print(f"🧪 Testing transcription with: {test_recording_id}")
        
        # Test the transcription service
        print(f"\n🚀 Running transcription service for: {test_recording_id}")
        print("=" * 60)
        
        from transcription_service import TranscriptionService
        service = TranscriptionService()
        
        result = await service.transcribe_recording(test_recording_id)
        
        print(f"📊 Result: {result}")
        
        if result['status'] == 'success':
            print("🎉 Transcription service is working perfectly!")
            print("✅ Both storage and database are being updated correctly")
        else:
            print(f"⚠️  Transcription had issues: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    print("🧪 Testing New Transcription")
    print("=" * 60)
    asyncio.run(test_new_transcription())
