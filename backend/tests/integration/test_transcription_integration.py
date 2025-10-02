#!/usr/bin/env python3
"""
Integration test script for TranscriptionService - Actually runs transcription with real services
This will make real calls to Supabase and OpenAI
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
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print("No .env file found, using existing environment variables")
except ImportError:
    print("python-dotenv not available, using existing environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_transcription_integration():
    """Test transcription for a specific recording ID with real services"""
    try:
        from backend.transcription_service import TranscriptionService
        
        # Check if required environment variables are set
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"Missing required environment variables: {missing_vars}")
            print("Please set these environment variables or create a .env file")
            return
        
        # Initialize the transcription service
        service = TranscriptionService()
        
        # Specify the recording ID to test
        recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
        
        print(f"Starting REAL transcription for recording ID: {recording_id}")
        print("This will make actual calls to Supabase and OpenAI...")
        
        # Run the transcription
        result = await service.transcribe_recording(recording_id)
        
        print(f"Transcription result: {result}")
        
        if result['status'] == 'success':
            print("✅ Transcription completed successfully!")
            print("Check your Supabase:")
            print("1. transcription table - should have a new record")
            print("2. Transcription storage bucket - should have a new transcription.txt file")
        else:
            print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"Error running transcription integration test: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_transcription_integration())
