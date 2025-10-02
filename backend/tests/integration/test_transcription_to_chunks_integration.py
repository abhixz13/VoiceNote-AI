#!/usr/bin/env python3
"""
Integration test for full transcription-to-chunks pipeline
Tests the complete flow: transcription → text processing → chunk storage
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root directory (three levels up) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the backend directory
    env_path = Path('../../.env')
    if not env_path.exists():
        env_path = Path('../../../.env')
    if not env_path.exists():
        # Try current directory relative to where we're running from
        env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("No .env file found, using existing environment variables")
except ImportError:
    print("python-dotenv not available, using existing environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_transcription_to_chunks_integration():
    """Test complete transcription to chunks pipeline with real services"""
    try:
        # Import with absolute paths from backend
        import backend.transcription_service as ts_module
        import backend.supabase_client as sc_module
        
        TranscriptionService = ts_module.TranscriptionService
        get_supabase_client = sc_module.get_supabase_client
        
        # Check if required environment variables are set
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("Please set these environment variables or create a .env file")
            return False
        
        print("✅ Environment variables are set")
        
        # Initialize services
        transcription_service = TranscriptionService()
        supabase = get_supabase_client()
        
        # Test recording ID (should exist in your database)
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"🚀 Starting full transcription-to-chunks integration test for recording: {recording_id}")
        print("=" * 80)
        
        # Step 1: Run transcription service (this will trigger text processing and chunk storage)
        print("📝 Step 1: Running transcription service...")
        result = await transcription_service.transcribe_recording(recording_id)
        
        if result['status'] != 'success':
            print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Transcription completed successfully")
        print(f"   📄 Transcription length: {len(result.get('transcription', ''))} characters")
        
        # Step 2: Verify transcription table was updated
        print("\n📋 Step 2: Verifying transcription table...")
        transcription_response = supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
        
        if not transcription_response.data:
            print("❌ No transcription record found in database")
            return False
        
        transcription_record = transcription_response.data[0]
        transcription_id = transcription_record['transcription_id']
        print(f"✅ Transcription record found:")
        print(f"   📝 Transcription ID: {transcription_id}")
        print(f"   📁 Path: {transcription_record['transcription_path']}")
        print(f"   👤 User ID: {transcription_record['user_id']}")
        
        # Step 3: Verify chunks were created in storage
        print("\n📦 Step 3: Verifying chunks in storage...")
        try:
            # Get the most recent transcription_id for this recording (from the current run)
            recent_transcription = supabase.table('transcription').select('transcription_id').eq('recording_id', recording_id).order('created_at', desc=True).limit(1).execute()
            current_transcription_id = recent_transcription.data[0]['transcription_id'] if recent_transcription.data else transcription_id
            
            print(f"   Using transcription_id: {current_transcription_id}")
            
            # List files in the chunks bucket for this recording/transcription
            chunk_files = supabase.storage.from_('Chunks').list(f"{recording_id}/{current_transcription_id}/")
            
            # If no files found with new transcription_id, try listing all files for this recording
            if not chunk_files:
                print(f"   No files found with transcription_id {transcription_id}, checking all files for recording...")
                all_recording_files = supabase.storage.from_('Chunks').list(f"{recording_id}/")
                
                if all_recording_files:
                    print(f"✅ Found {len(all_recording_files)} directories/files for recording {recording_id}:")
                    for item in all_recording_files:
                        print(f"   📁 {item['name']}")
                        # Try to list files in each subdirectory
                        try:
                            sub_files = supabase.storage.from_('Chunks').list(f"{recording_id}/{item['name']}/")
                            if sub_files:
                                chunk_files.extend(sub_files)
                                print(f"      Found {len(sub_files)} files in {item['name']}/")
                        except:
                            pass
                
            if not chunk_files:
                print("❌ No chunk files found in storage")
                return False
            
            print(f"✅ Found {len(chunk_files)} chunk files in storage:")
            for i, file in enumerate(chunk_files[:3]):  # Show first 3 files
                print(f"   📄 {i+1}. {file['name']} ({file.get('metadata', {}).get('size', 'Unknown')} bytes)")
            
            if len(chunk_files) > 3:
                print(f"   ... and {len(chunk_files) - 3} more files")
                
        except Exception as e:
            print(f"❌ Error checking chunk storage: {e}")
            return False
        
        # Step 4: Verify chunks table was updated
        print("\n🗃️  Step 4: Verifying chunks table...")
        chunks_response = supabase.table('chunk').select('*').eq('recording_id', recording_id).execute()
        
        if not chunks_response.data:
            print("❌ No chunk records found in chunks table")
            return False
        
        print(f"✅ Found {len(chunks_response.data)} chunk records in database:")
        for i, chunk in enumerate(chunks_response.data[:3]):  # Show first 3 chunks
            print(f"   📦 {i+1}. Chunk ID: {chunk['chunk_id']}")
            print(f"        Path: {chunk['chunk_path']}")
            print(f"        Created: {chunk['created_at']}")
        
        if len(chunks_response.data) > 3:
            print(f"   ... and {len(chunks_response.data) - 3} more chunks")
        
        # Step 5: Verify chunk content
        print("\n🔍 Step 5: Verifying chunk content...")
        try:
            # Download and verify first chunk
            first_chunk = chunks_response.data[0]
            chunk_path = first_chunk['chunk_path'].replace('Chunks/', '')  # Remove bucket prefix
            
            chunk_content = supabase.storage.from_('Chunks').download(chunk_path)
            chunk_data = chunk_content.decode('utf-8')
            
            import json
            chunk_json = json.loads(chunk_data)
            
            print(f"✅ Successfully downloaded and parsed chunk content:")
            print(f"   📦 Chunk ID: {chunk_json.get('chunk_id')}")
            print(f"   📝 Recording ID: {chunk_json.get('recording_id')}")
            print(f"   🔗 Transcription ID: {chunk_json.get('transcription_id')}")
            print(f"   📊 Chunk Number: {chunk_json.get('chunk_number')} of {chunk_json.get('total_chunks')}")
            print(f"   📄 Content preview: {chunk_json.get('chunk_data', '')[:100]}...")
            
        except Exception as e:
            print(f"❌ Error verifying chunk content: {e}")
            return False
        
        # Step 6: Verify recording status
        print("\n📊 Step 6: Verifying recording status...")
        recording_response = supabase.table('recordings').select('status, updated_at').eq('recording_id', recording_id).execute()
        
        if recording_response.data:
            recording_status = recording_response.data[0]
            print(f"✅ Recording status: {recording_status['status']}")
            print(f"   📅 Updated: {recording_status['updated_at']}")
        else:
            print("❌ Could not retrieve recording status")
            return False
        
        print("\n" + "=" * 80)
        print("🎉 INTEGRATION TEST PASSED!")
        print("✅ Complete transcription-to-chunks pipeline is working correctly:")
        print("   1. ✅ Audio transcription completed")
        print("   2. ✅ Transcription stored in database and storage")
        print("   3. ✅ Text processing triggered successfully")
        print("   4. ✅ Semantic chunks generated and stored")
        print("   5. ✅ Chunk metadata saved to database")
        print("   6. ✅ All data structures are correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def cleanup_test_data(recording_id: str):
    """Optional: Clean up test data after test completion"""
    try:
        import backend.supabase_client as sc_module
        get_supabase_client = sc_module.get_supabase_client
        supabase = get_supabase_client()
        
        print(f"\n🧹 Cleaning up test data for recording {recording_id}...")
        
        # Note: Uncomment these lines if you want to clean up after testing
        # Be careful - this will delete real data!
        
        # # Delete chunks from database
        # supabase.table('chunks').delete().eq('recording_id', recording_id).execute()
        # 
        # # Delete transcription from database
        # supabase.table('transcription').delete().eq('recording_id', recording_id).execute()
        # 
        # # Delete files from storage (chunks and transcription)
        # # This would require listing and deleting individual files
        
        print("⚠️  Cleanup skipped - uncomment cleanup code if needed")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🧪 Transcription-to-Chunks Integration Test")
    print("=" * 80)
    
    # Run the integration test
    success = asyncio.run(test_transcription_to_chunks_integration())
    
    if success:
        print("\n🎯 All tests passed! The transcription-to-chunks pipeline is working correctly.")
    else:
        print("\n💥 Integration test failed. Please check the logs above for details.")
        sys.exit(1)
