#!/usr/bin/env python3
"""
Transcription Service - Handles audio transcription using OpenAI Whisper
Separated from summarization for better architecture
"""
import openai
import os
import json
from typing import Dict, Optional, Any
from datetime import datetime
import logging
import tempfile

try:
    from .supabase_client import get_supabase_client
    from .text_processing import process_transcription
except ImportError:
    # Handle absolute imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from supabase_client import get_supabase_client
    from text_processing import process_transcription

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
            
            # 3. Transcribe audio using Whisper
            # transcription = await self._transcribe_audio_content(audio_content)
            #transcription = await self._transcribe_audio_content(audio_content)
            # Load hardcoded transcription from sample_ai_text.txt
            # import os
            # sample_file = os.path.join(os.path.dirname(__file__), 'sample_ai_text.txt')
            # with open(sample_file, 'r') as f:
            #     transcription = f.read()
            transcription = await self._transcribe_audio_content(audio_content)
            
            # 4. Store transcription in Supabase
            transcription_id = await self._update_recording_transcription(recording_id, transcription)
            
            # 5. Trigger text_processing to chunk and process
            await self._trigger_text_processing(recording_id, transcription_id, transcription)
            
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
            response = self.supabase.table('recordings').select('*').eq('recording_id', recording_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error(f"Error getting recording info {recording_id}: {str(e)}")
            return None
    
    async def _download_audio_file(self, file_path: str) -> Optional[bytes]:
        """Download audio file from Supabase Storage"""
        try:
            # Ensure the bucket name is always 'recordings' for audio files
            # The file_path from the database should be treated as the object path within this bucket.
            bucket_name = 'recordings'
            object_path = file_path
            
            # If the file_path from DB already includes the bucket name (e.g., 'recordings/temp-user/audio.webm'),
            # we need to remove the bucket name prefix to get the correct object_path for Supabase storage operations.
            if file_path.startswith(f'{bucket_name}/'):
                object_path = file_path.split(f'{bucket_name}/', 1)[1]

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
    
    async def _update_recording_transcription(self, recording_id: str, transcription: str) -> str:
        """Store transcription in Supabase Storage and update database with transcription metadata"""
        try:
            # Get user_id from recordings table (needed for transcription table)
            recording_info = await self._get_recording_info(recording_id)
            if not recording_info or 'user_id' not in recording_info:
                raise ValueError(f"Could not retrieve user_id for recording {recording_id}")
            user_id = recording_info['user_id']

            # 1. Store transcription text in Supabase Storage (Transcription bucket)
            # The object path within the bucket
            transcription_object_path = f"{recording_id}/transcription.txt"
            # The full path including bucket name for database storage
            transcription_full_path = f"Transcription/{transcription_object_path}"
            
            try:
                self.supabase.storage.from_("Transcription").upload(
                    transcription_object_path, 
                    transcription.encode('utf-8'),
                    {"content-type": "text/plain"}
                )
                self.logger.info(f"Uploaded transcription for {recording_id} to Transcription/{transcription_object_path}")
            except Exception as upload_error:
                # Check if it's a duplicate file error
                if "already exists" in str(upload_error) or "Duplicate" in str(upload_error):
                    self.logger.info(f"Transcription file already exists for {recording_id}, skipping upload...")
                    # File already exists, which is fine - we'll continue with database operations
                else:
                    raise upload_error

            # 2. Insert metadata into the public.transcription table (or update if exists)
            import uuid
            transcription_id = str(uuid.uuid4())  # Generate UUID explicitly
            
            insert_data = {
                'transcription_id': transcription_id,  # Explicitly provide UUID
                'recording_id': recording_id,
                'user_id': user_id, # Use user_id from recording
                'transcription_path': transcription_full_path # Full path including bucket name
            }
            
            try:
                response = self.supabase.table('transcription').insert(insert_data).execute()
                if response.data is None:
                    raise ValueError("Failed to insert transcription metadata into database.")
                
                # Use the transcription_id we generated
                inserted_transcription_id = response.data[0]['transcription_id']
                self.logger.info(f"Inserted transcription metadata with transcription_id: {inserted_transcription_id} for recording {recording_id}")
            except Exception as db_error:
                # Check if transcription already exists for this recording
                existing_response = self.supabase.table('transcription').select('transcription_id').eq('recording_id', recording_id).execute()
                if existing_response.data:
                    inserted_transcription_id = existing_response.data[0]['transcription_id']
                    self.logger.info(f"Transcription metadata already exists with transcription_id: {inserted_transcription_id} for recording {recording_id}")
                else:
                    raise db_error
            
            # 3. Update the recordings table status to 'processing' (will be set to 'summarized' after processing)
            update_data = {
                'status': 'processing',
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table('recordings').update(update_data).eq('recording_id', recording_id).execute()
            self.logger.info(f"Updated recording {recording_id} status to 'processing'")
            
            return inserted_transcription_id  # Return the generated transcription_id
            
        except Exception as e:
            self.logger.error(f"Error storing transcription and updating metadata for {recording_id}: {str(e)}")
            raise
    
    async def _update_recording_status(self, recording_id: str, status: str, error_message: str = None) -> None:
        """Update recording status"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Removed metadata update as the column no longer exists in recordings table
            # if error_message:
            #     update_data['metadata'] = json.dumps({'error': error_message})
            
            response = self.supabase.table('recordings').update(update_data).eq('recording_id', recording_id).execute()
            self.logger.info(f"Updated recording {recording_id} status to {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating recording status {recording_id}: {str(e)}")
    
    async def _trigger_text_processing(self, recording_id: str, transcription_id: str, transcription_text: str) -> None:
        """
        Trigger text_processing to chunk transcription and store in Supabase
        
        Args:
            recording_id: ID of the recording
            transcription_id: ID of the transcription record
            transcription_text: The actual transcription text
        """
        try:
            self.logger.info(f"Triggering text processing for recording {recording_id} (transcription {transcription_id})")
            
            # Call text_processing to handle chunking and storage
            await process_transcription(recording_id, transcription_id, transcription_text)
            
            self.logger.info(f"Text processing completed for recording {recording_id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering text processing for {recording_id}: {str(e)}")
            raise  # Re-raise the exception so caller knows processing failed
    
    async def summarize_recording(self, recording_id: str) -> Dict[str, Any]:
        """
        Generate summary for an existing recording (triggered by user clicking "Summarize")
        
        Args:
            recording_id: ID of the recording to summarize
            
        Returns:
            Dictionary with status and summary information
        """
        try:
            self.logger.info(f"Starting summarization for recording {recording_id}")
            
            # Check if recording exists and has transcription
            recording_info = await self._get_recording_info(recording_id)
            if not recording_info:
                return {
                    'status': 'error',
                    'message': f'Recording {recording_id} not found',
                    'recording_id': recording_id
                }
            
            # Check if summaries already exist to avoid token waste
            current_status = recording_info.get('status', 'recorded')
            if current_status == 'summarized':
                self.logger.info(f"Recording {recording_id} already has summaries, returning existing ones...")
                
                # Get existing summary from summaries table
                existing_summary = await self._get_existing_summary(recording_id)
                if existing_summary:
                    return {
                        'status': 'success',
                        'message': 'Summaries already exist for this recording',
                        'recording_id': recording_id,
                        'unified_summary': existing_summary.get('unified_summary') if existing_summary else None,
                        'summary_id': existing_summary.get('summary_id') if existing_summary else None,
                        'summary_path': existing_summary.get('summary_path') if existing_summary else None,
                        'already_existed': True
                    }
            
            # Check if transcription exists
            transcription_response = self.supabase.table('transcription').select('*').eq('recording_id', recording_id).execute()
            
            if not transcription_response.data:
                # No transcription exists, need to transcribe first
                self.logger.info(f"No transcription found for {recording_id}, starting transcription process")
                transcription_result = await self.transcribe_recording(recording_id)
                
                if transcription_result['status'] != 'success':
                    return {
                        'status': 'error',
                        'message': 'Failed to transcribe recording',
                        'recording_id': recording_id
                    }
                
                # After transcription, it will automatically trigger text processing and summarization
                # The result from transcribe_recording already contains the full pipeline output
                return {
                    'status': 'success',
                    'message': 'Transcription and summary generation completed successfully',
                    'recording_id': recording_id,
                    'unified_summary': transcription_result.get('unified_summary') if transcription_result else None,
                    'summary_id': transcription_result.get('summary_id') if transcription_result else None,
                    'summary_path': transcription_result.get('summary_path') if transcription_result else None
                }
            else:
                # Transcription exists, get the latest one
                latest_transcription = transcription_response.data[-1]  # Get most recent
                transcription_id = latest_transcription['transcription_id']
                
                # Get transcription text from storage
                transcription_path = latest_transcription['transcription_path'].replace('Transcription/', '')
                transcription_content = self.supabase.storage.from_('Transcription').download(transcription_path)
                transcription_text = transcription_content.decode('utf-8')
                
                # Trigger text processing (chunking + summarization)
                self.logger.info(f"Triggering text processing for existing transcription {transcription_id}")
                await self._trigger_text_processing(recording_id, transcription_id, transcription_text)
                
                # Update recording status to 'summarized' immediately after successful processing
                await self._update_recording_status(recording_id, 'summarized')
                self.logger.info(f"Updated recording {recording_id} status to 'summarized'")
                
                # Try to get the generated summary from summaries table (don't fail if this doesn't work)
                existing_summary = None
                try:
                    existing_summary = await self._get_existing_summary(recording_id)
                except Exception as summary_error:
                    self.logger.warning(f"Could not retrieve summary for {recording_id}: {summary_error}")
                
                # Return success status with unified summary (if available)
                return {
                    'status': 'success',
                    'message': 'Summary generation completed successfully',
                    'recording_id': recording_id,
                    'unified_summary': existing_summary.get('unified_summary') if existing_summary else None,
                    'summary_id': existing_summary.get('summary_id') if existing_summary else None,
                    'summary_path': existing_summary.get('summary_path') if existing_summary else None
                }
            
        except Exception as e:
            self.logger.error(f"Error in summarize_recording for {recording_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error generating summary: {str(e)}',
                'recording_id': recording_id
            }
    
    async def _get_existing_summary(self, recording_id: str) -> Dict[str, Any]:
        """
        Get existing unified summary for a recording from Supabase
        
        Args:
            recording_id: ID of the recording
            
        Returns:
            Dictionary with existing summary data or None if not found
        """
        try:
            # Get summary metadata from summaries table
            summaries_response = self.supabase.table('summaries').select('*').eq('recording_id', recording_id).order('created_at', desc=True).limit(1).execute()
            
            if not summaries_response.data:
                self.logger.warning(f"No summary metadata found for recording {recording_id}")
                return None
            
            summary_metadata = summaries_response.data[0]
            summary_path = summary_metadata['summary_path']
            
            # Extract filename from path (e.g., "Summaries/uuid.json" -> "uuid.json")
            filename = summary_path.replace('Summaries/', '')
            
            # Download unified summary JSON from Summaries bucket
            try:
                summary_content = self.supabase.storage.from_('Summaries').download(filename)
                unified_summary = json.loads(summary_content.decode('utf-8'))
                
                return {
                    'summary_metadata': summary_metadata,
                    'unified_summary': unified_summary,
                    'summary_id': summary_metadata['summary_id'],
                    'summary_path': summary_path
                }
                
            except Exception as storage_error:
                self.logger.error(f"Error downloading summary file {filename}: {str(storage_error)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting existing summary for {recording_id}: {str(e)}")
            return None
