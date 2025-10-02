#!/usr/bin/env python3
"""
VoiceNote AI - Backend API Layer
FastAPI application for audio transcription and summarization
"""

import os
import sys
import logging
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from .transcription_service import TranscriptionService
    from .ai_summary_service import AISummaryService
except ImportError:
    # Handle absolute imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    description="API for VoiceNote AI application, handling transcription, summarization, and note generation.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to validate environment
@app.on_event("startup")
async def startup_event():
    """Validate environment variables and dependencies on startup"""
    try:
        # Check required environment variables
        required_env_vars = [
            "OPENAI_API_KEY",
            "SUPABASE_URL", 
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        logger.info("✅ All required environment variables are set")
        logger.info("🚀 VoiceNote AI Backend started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup validation failed: {str(e)}")
        raise

# Initialize services (lazy initialization to avoid startup errors)
transcription_service = None
summary_service = None

def get_transcription_service():
    """Get or initialize transcription service"""
    global transcription_service
    if transcription_service is None:
        try:
            transcription_service = TranscriptionService()
        except Exception as e:
            logger.error(f"Failed to initialize TranscriptionService: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    return transcription_service

def get_summary_service():
    """Get or initialize summary service"""
    global summary_service
    if summary_service is None:
        try:
            summary_service = AISummaryService()
        except Exception as e:
            logger.error(f"Failed to initialize AISummaryService: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    return summary_service


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
    unified_summary: Optional[Dict] = None
    message: Optional[str] = None
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
    try:
        # Basic health check without initializing services
        return {
            "status": "healthy",
            "service": "VoiceNote AI Backend",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "python_version": sys.version,
                "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
                "has_supabase_url": bool(os.getenv("SUPABASE_URL")),
                "has_supabase_keys": bool(os.getenv("SUPABASE_ANON_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "VoiceNote AI Backend",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
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
        
        service = get_transcription_service()
        result = await service.transcribe_recording(recording_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return TranscriptionResponse(
            status=result['status'],
            recording_id=result['recording_id'],
            transcription_file_path=result.get('transcription_file_path'),
            timestamp=result.get('timestamp', datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Error in transcription endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Summarization endpoint
@app.post("/api/recordings/{recording_id}/summarize", response_model=SummaryResponse)
async def summarize_recording(recording_id: str):
    """
    Generate summaries for a transcribed recording (or transcribe first if needed)
    
    Args:
        recording_id: ID of the recording to summarize
        
    Returns:
        SummaryResponse with status and summaries
    """
    try:
        logger.info(f"Starting summarization for recording {recording_id}")
        
        # Use the new summarize_recording method from TranscriptionService
        service = get_transcription_service()
        result = await service.summarize_recording(recording_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['message'])
        
        return SummaryResponse(
            status=result['status'],
            recording_id=result['recording_id'],
            unified_summary=result.get('unified_summary'),
            message=result['message'],
            timestamp=datetime.now().isoformat()
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
        
        # Use the summarize_recording method which handles the full pipeline
        service = get_transcription_service()
        result = await service.summarize_recording(recording_id)
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['message'])
        
        return {
            "status": result['status'],
            "recording_id": result['recording_id'],
            "message": result['message'],
            "unified_summary": result.get('unified_summary'),
            "summary_id": result.get('summary_id'),
            "summary_path": result.get('summary_path'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in process endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
