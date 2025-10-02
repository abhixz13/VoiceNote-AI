#!/usr/bin/env python3
"""
Check what was created in Supabase during our transcription tests
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

def check_supabase_results():
    """Check what was created in Supabase"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"🔍 Checking results for recording ID: {recording_id}")
        print("=" * 60)
        
        # 1. Check transcription table
        print("📋 Checking transcription table...")
        try:
            response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
            if response.data:
                print(f"✅ Found {len(response.data)} transcription records:")
                for record in response.data:
                    print(f"   📝 Transcription ID: {record.get('transcription_id')}")
                    print(f"   📁 Path: {record.get('transcription_path')}")
                    print(f"   👤 User ID: {record.get('user_id')}")
                    print(f"   📅 Created: {record.get('created_at')}")
            else:
                print("❌ No transcription records found")
        except Exception as e:
            print(f"❌ Error checking transcription table: {e}")
        
        print()
        
        # 2. Check Transcription storage bucket
        print("📁 Checking Transcription storage bucket...")
        try:
            files = supabase.storage.from_('Transcription').list(f"{recording_id}/")
            if files:
                print(f"✅ Found {len(files)} files in Transcription bucket:")
                for file in files:
                    print(f"   📄 File: {file['name']}")
                    print(f"   📏 Size: {file.get('metadata', {}).get('size', 'Unknown')} bytes")
                    print(f"   📅 Updated: {file.get('updated_at')}")
                    
                    # Try to download and show content
                    try:
                        content = supabase.storage.from_('Transcription').download(f"{recording_id}/{file['name']}")
                        if content:
                            text_content = content.decode('utf-8')
                            print(f"   📝 Content preview: {text_content[:200]}...")
                    except Exception as e:
                        print(f"   ⚠️  Could not read content: {e}")
            else:
                print("❌ No files found in Transcription bucket")
        except Exception as e:
            print(f"❌ Error checking Transcription bucket: {e}")
        
        print()
        
        # 3. Check recording status
        print("📊 Checking recording status...")
        try:
            response = supabase.table('recordings').select('*').eq('recording_id', recording_id).execute()
            if response.data:
                record = response.data[0]
                print(f"✅ Recording status: {record.get('status')}")
                print(f"📅 Updated: {record.get('updated_at')}")
            else:
                print("❌ Recording not found")
        except Exception as e:
            print(f"❌ Error checking recording status: {e}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Checking Supabase Results")
    print("=" * 60)
    check_supabase_results()
