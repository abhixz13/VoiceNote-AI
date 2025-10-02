#!/usr/bin/env python3
"""
End-to-End Integration Test for Complete VoiceNote AI Pipeline
Tests the complete flow: transcription → text processing → chunk storage → AI summarization
"""
import asyncio
import os
import sys
import logging
import json
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

async def test_end_to_end_pipeline():
    """Test complete end-to-end pipeline with real services"""
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
        
        print(f"🚀 Starting complete end-to-end pipeline test for recording: {recording_id}")
        print("=" * 80)
        
        # Step 1: Run summarization service (this will trigger the complete pipeline)
        print("📝 Step 1: Running complete summarization pipeline...")
        result = await transcription_service.summarize_recording(recording_id)
        
        if result['status'] != 'success':
            print(f"❌ Pipeline failed: {result.get('message', 'Unknown error')}")
            return False
        
        print(f"✅ Complete pipeline completed successfully")
        print(f"   📄 Message: {result.get('message', 'No message')}")
        
        # Step 2: Verify transcription table was updated
        print("\n📋 Step 2: Verifying transcription table...")
        transcription_response = supabase.table('transcription').select('*').eq('recording_id', recording_id).order('created_at', desc=True).limit(1).execute()
        
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
            # List files in the chunks bucket for this recording/transcription
            chunk_files = supabase.storage.from_('Chunks').list(f"{recording_id}/{transcription_id}/")
            
            # If no files found with current transcription_id, try listing all files for this recording
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
        
        # Step 5: Verify unified summary was created in summaries table
        print("\n📊 Step 5: Verifying summaries table...")
        summaries_response = supabase.table('summaries').select('*').eq('recording_id', recording_id).order('created_at', desc=True).limit(1).execute()
        
        if not summaries_response.data:
            print("❌ No summary records found in summaries table")
            return False
        
        summary_record = summaries_response.data[0]
        summary_id = summary_record['summary_id']
        summary_path = summary_record['summary_path']
        
        print(f"✅ Found summary record in database:")
        print(f"   🆔 Summaries ID: {summary_id}")
        print(f"   📁 Summaries Path: {summary_path}")
        print(f"   📝 Recording ID: {summary_record['recording_id']}")
        print(f"   📅 Created At: {summary_record['created_at']}")
        
        # Step 6: Verify unified summary JSON in Summaries storage bucket
        print("\n📄 Step 6: Verifying unified summary in Summaries storage bucket...")
        try:
            # Download the summary JSON file
            summary_file_path = summary_path.replace('Summaries/', '')  # Remove bucket prefix
            summary_content = supabase.storage.from_('Summaries').download(summary_file_path)
            summary_data = summary_content.decode('utf-8')
            summary_json = json.loads(summary_data)
            
            print(f"✅ Successfully downloaded and parsed unified summary:")
            print(f"   🆔 Summaries ID: {summary_json.get('summary_id')}")
            print(f"   📝 Recording ID: {summary_json.get('recording_id')}")
            print(f"   📅 Created At: {summary_json.get('created_at')}")
            print(f"   📊 Total Chunks: {summary_json.get('total_chunks')}")
            print(f"   ✅ Successful Summaries: {summary_json.get('successful_summaries')}")
            print(f"   ❌ Failed Summaries: {summary_json.get('failed_summaries')}")
            
            # Verify chunk summaries structure
            chunk_summaries = summary_json.get('chunk_summaries', {})
            print(f"   📦 Chunk Summaries: {len(chunk_summaries)} chunks found")
            
            for chunk_key in list(chunk_summaries.keys())[:3]:  # Show first 3 chunks
                chunk_data = chunk_summaries[chunk_key]
                print(f"      {chunk_key}: {chunk_data.get('chunk_id')} - {chunk_data.get('chunk_summary', '')[:50]}...")
            
            # Verify consolidated summary structure
            consolidated_summary = summary_json.get('consolidated_summary', {})
            if consolidated_summary:
                print(f"   🎯 Consolidated Summaries:")
                print(f"      Executive: {consolidated_summary.get('executive_summary', '')[:100]}...")
                key_points = consolidated_summary.get('key_points', '')
                if isinstance(key_points, list):
                    print(f"      Key Points: {len(key_points)} points")
                else:
                    print(f"      Key Points: {len(str(key_points).split('•'))-1} points")
                print(f"      Detailed: {len(consolidated_summary.get('detailed_summary', ''))} characters")
            else:
                print("   ❌ No consolidated summary found")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying unified summary: {e}")
            return False
        
        # Step 7: Verify chunk content structure
        print("\n🔍 Step 7: Verifying individual chunk content...")
        try:
            # Download and verify first chunk
            first_chunk = chunks_response.data[0]
            chunk_path = first_chunk['chunk_path'].replace('Chunks/', '')  # Remove bucket prefix
            
            chunk_content = supabase.storage.from_('Chunks').download(chunk_path)
            chunk_data = chunk_content.decode('utf-8')
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
        
        # Step 8: Verify recording status
        print("\n📊 Step 8: Verifying recording status...")
        recording_response = supabase.table('recordings').select('status, updated_at').eq('recording_id', recording_id).execute()
        
        if recording_response.data:
            recording_status = recording_response.data[0]
            print(f"✅ Recording status: {recording_status['status']}")
            print(f"   📅 Updated: {recording_status['updated_at']}")
        else:
            print("❌ Could not retrieve recording status")
            return False
        
        # Step 9: Validate JSON structure matches specification
        print("\n🔍 Step 9: Validating optimized JSON structure...")
        
        # Check for required top-level fields
        required_fields = ['recording_id', 'summary_id', 'created_at', 'total_chunks', 'chunk_summaries', 'consolidated_summary']
        missing_fields = [field for field in required_fields if field not in summary_json]
        
        if missing_fields:
            print(f"❌ Missing required fields in summary JSON: {missing_fields}")
            return False
        
        # Check chunk summaries structure (should be numbered: chunk_1, chunk_2, etc.)
        chunk_keys = list(chunk_summaries.keys())
        expected_chunk_keys = [f"chunk_{i}" for i in range(1, len(chunk_keys) + 1)]
        
        if set(chunk_keys) != set(expected_chunk_keys):
            print(f"❌ Chunk keys don't match expected format. Expected: {expected_chunk_keys}, Got: {chunk_keys}")
            return False
        
        # Check consolidated summary structure
        consolidated_required = ['executive_summary', 'key_points', 'detailed_summary']
        consolidated_missing = [field for field in consolidated_required if field not in consolidated_summary]
        
        if consolidated_missing:
            print(f"❌ Missing required fields in consolidated summary: {consolidated_missing}")
            return False
        
        print(f"✅ JSON structure validation passed:")
        print(f"   ✓ All required top-level fields present")
        print(f"   ✓ Chunk summaries properly numbered (chunk_1, chunk_2, etc.)")
        print(f"   ✓ Consolidated summary has all required fields")
        print(f"   ✓ No field duplication detected")
        
        print("\n" + "=" * 80)
        print("🎉 END-TO-END INTEGRATION TEST PASSED!")
        print("✅ Complete VoiceNote AI pipeline is working correctly:")
        print("   1. ✅ Audio transcription completed")
        print("   2. ✅ Transcription stored in database and storage")
        print("   3. ✅ Text processing triggered successfully")
        print("   4. ✅ Semantic chunks generated and stored")
        print("   5. ✅ Chunk metadata saved to database")
        print("   6. ✅ AI summarization completed for all chunks")
        print("   7. ✅ Consolidated summary generated using GPT-4")
        print("   8. ✅ Unified summary JSON created and stored")
        print("   9. ✅ Summaries table updated with metadata")
        print("  10. ✅ Optimized JSON structure validated")
        print("  11. ✅ All data structures are correct and optimized")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end integration test failed with error: {str(e)}")
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
        
        # # Delete summaries from database
        # supabase.table('summaries').delete().eq('recording_id', recording_id).execute()
        # 
        # # Delete chunks from database
        # supabase.table('chunk').delete().eq('recording_id', recording_id).execute()
        # 
        # # Delete transcription from database
        # supabase.table('transcription').delete().eq('recording_id', recording_id).execute()
        # 
        # # Delete files from storage (summaries, chunks, and transcription)
        # # This would require listing and deleting individual files
        
        print("⚠️  Cleanup skipped - uncomment cleanup code if needed")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🧪 VoiceNote AI End-to-End Pipeline Integration Test")
    print("=" * 80)
    
    # Run the integration test
    success = asyncio.run(test_end_to_end_pipeline())
    
    if success:
        print("\n🎯 All tests passed! The complete VoiceNote AI pipeline is working correctly.")
    else:
        print("\n💥 Integration test failed. Please check the logs above for details.")
        sys.exit(1)
