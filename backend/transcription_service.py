#!/usr/bin/env python3
"""
Transcription Service - Handles audio transcription using OpenAI Whisper
Separated from summarization for better architecture
"""
import openai
import os
import json
from typing import Dict, Optional
from datetime import datetime
import logging
import tempfile

from supabase_client import get_supabase_client

class TranscriptionService:
    def __init__(self):
        """Initialize the Transcription Service"""
        # Initialize Supabase first
        self.supabase = get_supabase_client()
        
        # Initialize OpenAI client separately to avoid proxy conflicts
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.whisper_model = "whisper-1"
    
    async def transcribe_recording(self, recording_id: str) -> Dict:
        """
        Transcribe a recording from Supabase storage
        
        Args:
            recording_id: ID of the recording to transcribe
            
        Returns:
            Dict with transcription result and status
        """
        try:
            # 1. Get recording info from database
            recording = await self._get_recording_info(recording_id)
            if not recording:
                return {
                    'status': 'error',
                    'error': f'Recording {recording_id} not found',
                    'recording_id': recording_id
                }
            
            # 2. Download audio file from Supabase Storage
            audio_content = await self._download_audio_file(recording['file_path'])
            if not audio_content:
                return {
                    'status': 'error',
                    'error': f'Failed to download audio file for {recording_id}',
                    'recording_id': recording_id
                }
            
            # 3. Transcribe audio using Whisper (HARDCODED FOR TESTING)
            # transcription = await self._transcribe_audio_content(audio_content)
            #transcription = await self._transcribe_audio_content(audio_content)
            # Load hardcoded transcription from sample_ai_text.txt
            import os
            sample_file = os.path.join(os.path.dirname(__file__), 'sample_ai_text.txt')
            with open(sample_file, 'r') as f:
                transcription = f.read()
            
            # 4. Store transcription in Supabase
            await self._update_recording_transcription(recording_id, transcription)
            
            # 5. Trigger text_processing to chunk and process
            await self._trigger_text_processing(recording_id)
            
            return {
                'status': 'success',
                'recording_id': recording_id,
                'transcription': transcription,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error transcribing recording {recording_id}: {str(e)}")
            # Update recording status to error
            await self._update_recording_status(recording_id, 'error', str(e))
            return {
                'status': 'error',
                'error': str(e),
                'recording_id': recording_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_recording_info(self, recording_id: str) -> Optional[Dict]:
        """Get recording information from database"""
        try:
            response = self.supabase.table('recordings').select('*').eq('id', recording_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error(f"Error getting recording info {recording_id}: {str(e)}")
            return None
    
    async def _download_audio_file(self, file_path: str) -> Optional[bytes]:
        """Download audio file from Supabase Storage"""
        try:
            # Extract bucket name and file path
            if '/' in file_path:
                bucket_name, object_path = file_path.split('/', 1)
            else:
                bucket_name = 'recordings'
                object_path = file_path
            
            # Download file from storage
            response = self.supabase.storage.from_(bucket_name).download(object_path)
            return response
            
        except Exception as e:
            self.logger.error(f"Error downloading audio file {file_path}: {str(e)}")
            return None
    
    async def _transcribe_audio_content(self, audio_content: bytes) -> str:
        """Transcribe audio content using Whisper API"""
        try:
            # Save to temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=self.whisper_model,
                        file=audio_file,
                        response_format="text"
                    )
                return transcript
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    async def _update_recording_transcription(self, recording_id: str, transcription: str) -> None:
        """Store transcription in Supabase Storage and update database with file path"""
        try:
            # 1. Store transcription text in Supabase Storage (transcription bucket)
            transcription_file_path = f"{recording_id}/transcription.txt"
            
            # Upload to transcription bucket
            self.supabase.storage.from_("transcription").upload(
                transcription_file_path, 
                transcription.encode('utf-8'),
                {"content-type": "text/plain"}
            )
            
            # 2. Update database with file path reference
            update_data = {
                'transcription': transcription_file_path,  # Store file path, not text
                'status': 'transcribed',
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('recordings').update(update_data).eq('id', recording_id).execute()
            self.logger.info(f"Stored transcription for {recording_id} at transcription/{transcription_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error storing transcription for {recording_id}: {str(e)}")
            raise
    
    async def _update_recording_status(self, recording_id: str, status: str, error_message: str = None) -> None:
        """Update recording status"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if error_message:
                update_data['metadata'] = json.dumps({'error': error_message})
            
            response = self.supabase.table('recordings').update(update_data).eq('id', recording_id).execute()
            self.logger.info(f"Updated recording {recording_id} status to {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating recording status {recording_id}: {str(e)}")
    
    async def _trigger_text_processing(self, recording_id: str) -> None:
        """
        Trigger text_processing to chunk transcription and store in Supabase
        
        Args:
            recording_id: ID of the recording
        """
        try:
            from text_processing import process_transcription
            
            self.logger.info(f"Triggering text processing for recording {recording_id}")
            
            # Call text_processing to handle chunking and storage
            await process_transcription(recording_id)
            
            self.logger.info(f"Text processing completed for recording {recording_id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering text processing for {recording_id}: {str(e)}")
            # Don't raise - processing failure shouldn't fail the transcription
