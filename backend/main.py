"""
VoiceNote AI Backend - Python FastAPI Server
Handles audio transcription and summarization using OpenAI APIs
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from ai_summary_service import AISummaryService
from supabase_client import get_supabase_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="VoiceNote AI Backend",
    description="Backend API for audio transcription and summarization",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service
ai_service = AISummaryService()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class TranscriptionRequest(BaseModel):
    recording_id: int

class TranscriptionResponse(BaseModel):
    message: str
    recording_id: int
    status: str
    transcription_length: Optional[int] = None
    summaries_generated: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

# Transcription endpoint
@app.post("/api/recordings/{recording_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_recording(recording_id: int):
    """
    Transcribe and summarize a recording
    """
    try:
        logger.info(f"Starting transcription for recording {recording_id}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Fetch recording details from database
        recording_response = supabase.table('recordings').select('*').eq('id', recording_id).execute()
        
        if not recording_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        
        recording = recording_response.data[0]
        
        # Update status to processing
        supabase.table('recordings').update({
            'status': 'processing',
            'updated_at': datetime.now().isoformat()
        }).eq('id', recording_id).execute()
        
        # Download audio file from Supabase Storage
        audio_path = recording.get('file_path')
        if not audio_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audio file path found for recording"
            )
        
        # Download audio file
        audio_response = supabase.storage.from_('recordings').download(audio_path)
        
        if audio_response[1]:  # Check for error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download audio file: {audio_response[1]}"
            )
        
        audio_data = audio_response[0]
        
        # Save audio to temporary file for processing
        temp_audio_path = f"temp_audio_{recording_id}_{datetime.now().timestamp()}.webm"
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_data)
        
        try:
            # Generate transcription and summaries using AISummaryService
            result = await ai_service.generateRecordingSummaries(temp_audio_path)
            
            # Update database with results
            update_data = {
                'transcription': result['transcription'],
                'summary_short': result['summaries']['short'],
                'summary_medium': result['summaries']['medium'],
                'summary_detailed': result['summaries']['detailed'],
                'status': 'transcribed',
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('recordings').update(update_data).eq('id', recording_id).execute()
            
            logger.info(f"Successfully processed recording {recording_id}")
            
            return TranscriptionResponse(
                message="Transcription and summarization completed successfully",
                recording_id=recording_id,
                status="transcribed",
                transcription_length=len(result['transcription']),
                summaries_generated=len(result['summaries'])
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing recording {recording_id}: {str(e)}")
        
        # Update status to error
        try:
            supabase.table('recordings').update({
                'status': 'error',
                'updated_at': datetime.now().isoformat()
            }).eq('id', recording_id).execute()
        except:
            pass  # Ignore errors when updating status
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process recording: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
