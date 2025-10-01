#!/usr/bin/env python3
"""
VoiceNote AI - Backend API Layer
FastAPI application for audio transcription and summarization
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from transcription_service import TranscriptionService
from ai_summary_service import AISummaryService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VoiceNote AI Backend",
    description="Backend API for audio transcription and summarization",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (once at startup, not per request)
transcription_service = TranscriptionService()
summary_service = AISummaryService()


# Pydantic models for request/response
class TranscriptionRequest(BaseModel):
    recording_id: str

class TranscriptionResponse(BaseModel):
    status: str
    recording_id: str
    transcription_file_path: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

class SummaryRequest(BaseModel):
    recording_id: str

class SummaryResponse(BaseModel):
    status: str
    recording_id: str
    summaries: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "healthy",
        "service": "VoiceNote AI Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "VoiceNote AI Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Transcription endpoint
@app.post("/api/recordings/{recording_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_recording(recording_id: str):
    """
    Transcribe an audio recording from Supabase storage
    
    Args:
        recording_id: ID of the recording to transcribe
        
    Returns:
        TranscriptionResponse with status and transcription file path
    """
    try:
        logger.info(f"Starting transcription for recording {recording_id}")
        
        result = await transcription_service.transcribe_recording(recording_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return TranscriptionResponse(
            status=result['status'],
            recording_id=result['recording_id'],
            transcription_file_path=result.get('transcription_file_path'),
            timestamp=result['timestamp']
        )
        
    except Exception as e:
        logger.error(f"Error in transcription endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Summarization endpoint
@app.post("/api/recordings/{recording_id}/summarize", response_model=SummaryResponse)
async def summarize_recording(recording_id: str):
    """
    Generate summaries for a transcribed recording
    
    Args:
        recording_id: ID of the recording to summarize
        
    Returns:
        SummaryResponse with status and summaries
    """
    try:
        logger.info(f"Starting summarization for recording {recording_id}")
        
        result = await summary_service.generate_summaries_for_recording(recording_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return SummaryResponse(
            status=result['status'],
            recording_id=result['recording_id'],
            summaries=result.get('summaries'),
            timestamp=result['timestamp']
        )
        
    except Exception as e:
        logger.error(f"Error in summarization endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Combined endpoint (transcribe + summarize)
@app.post("/api/recordings/{recording_id}/process")
async def process_recording(recording_id: str, background_tasks: BackgroundTasks):
    """
    Process recording: transcribe then summarize
    
    Args:
        recording_id: ID of the recording to process
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting full processing for recording {recording_id}")
        
        # Step 1: Transcribe
        transcription_result = await transcription_service.transcribe_recording(recording_id)
        if transcription_result['status'] == 'error':
            raise HTTPException(status_code=500, detail=transcription_result['error'])
        
        # Step 2: Summarize
        summary_result = await summary_service.generate_summaries_for_recording(recording_id)
        if summary_result['status'] == 'error':
            raise HTTPException(status_code=500, detail=summary_result['error'])
        
        return {
            "status": "success",
            "recording_id": recording_id,
            "message": "Recording transcribed and summarized successfully",
            "transcription_file_path": transcription_result.get('transcription_file_path'),
            "summaries": summary_result.get('summaries'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in process endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
