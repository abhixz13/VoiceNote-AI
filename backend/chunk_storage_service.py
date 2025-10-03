"""
Chunk Storage Service for persisting LLM responses with metadata in Supabase
"""

try:
    from .supabase_client import get_supabase_client
    from .ai_summary_service import AISummaryService
except ImportError:
    # Handle absolute imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from supabase_client import get_supabase_client
    from ai_summary_service import AISummaryService
from datetime import datetime
from typing import List, Dict, Any
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class ChunkStorageService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def store_chunks(self, recording_id: str, transcription_id: str, chunks: List[str], user_id: str) -> Dict[str, Any]:
        """
        Store semantic chunks in Supabase storage and update chunks table
        
        Args:
            recording_id: ID of the recording
            transcription_id: ID of the transcription record
            chunks: List of processed text chunks
            user_id: ID of the user
            
        Returns:
            Dictionary with chunk storage and summarization status
        """
        chunk_ids = []
        
        try:
            for i, chunk_text in enumerate(chunks):
                # Generate unique chunk ID
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                
                # Create chunk data structure
                chunk_data = {
                    "chunk_id": chunk_id,
                    "recording_id": recording_id,
                    "transcription_id": transcription_id,
                    "chunk_data": chunk_text,
                    "chunk_number": i + 1,
                    "total_chunks": len(chunks),
                    "created_at": datetime.now().isoformat()
                }
                
                # Store chunk as JSON file in Chunks bucket
                chunk_file_path = f"{recording_id}/{transcription_id}/{chunk_id}.json"
                
                try:
                    self.supabase.storage.from_("Chunks").upload(
                        chunk_file_path,
                        json.dumps(chunk_data, indent=2).encode('utf-8'),
                        {"content-type": "application/json"}
                    )
                    logger.info(f"Stored chunk {chunk_id} for recording {recording_id}")
                except Exception as upload_error:
                    if "already exists" in str(upload_error) or "Duplicate" in str(upload_error):
                        logger.info(f"Chunk file already exists for {chunk_id}, skipping upload...")
                    else:
                        raise upload_error
                
                # Update chunks table with metadata
                chunk_path = f"Chunks/{chunk_file_path}"
                chunk_metadata = {
                    "chunk_id": chunk_id,
                    "chunk_path": chunk_path,
                    "recording_id": recording_id,
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat()
                }
                
                try:
                    response = self.supabase.table('chunk').insert(chunk_metadata).execute()
                    if not response.data:
                        logger.warning(f"Failed to insert chunk metadata for {chunk_id}")
                except Exception as db_error:
                    # Check if chunk already exists
                    existing_response = self.supabase.table('chunk').select('chunk_id').eq('chunk_id', chunk_id).execute()
                    if existing_response.data:
                        logger.info(f"Chunk metadata already exists for {chunk_id}")
                    else:
                        logger.error(f"Error inserting chunk metadata for {chunk_id}: {db_error}")
                        raise db_error
            
            logger.info(f"Successfully stored {len(chunks)} chunks for recording {recording_id}")
            
            # Trigger AI summarization after successful chunk storage
            summary_result = await self._trigger_ai_summarization(recording_id, chunk_ids, chunks)
            
            # Return combined status with unified summary
            return {
                'status': 'success',
                'message': f'Successfully stored {len(chunks)} chunks and generated unified summary',
                'recording_id': recording_id,
                'chunks_stored': len(chunks),
                'chunk_ids': chunk_ids,
                'unified_summary': summary_result.get('unified_summary'),
                'summarization_status': summary_result.get('status', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error storing chunks for recording {recording_id}: {str(e)}")
            raise
    
    async def _trigger_ai_summarization(self, recording_id: str, chunk_ids: List[str], chunks: List[str]) -> Dict[str, Any]:
        """
        Trigger AI summarization service after successful chunk storage
        
        Args:
            recording_id: ID of the recording
            chunk_ids: List of generated chunk IDs
            chunks: List of chunk text content
            
        Returns:
            Dictionary with summarization status
        """
        try:
            logger.info(f"Triggering AI summarization for {len(chunks)} chunks in recording {recording_id}")
            
            # Create list of (chunk_id, chunk_text) tuples
            chunk_data = list(zip(chunk_ids, chunks))
            
            # Initialize and call AI Summary Service
            ai_summary_service = AISummaryService()
            summary_result = await ai_summary_service.process_chunks_for_recording(recording_id, chunk_data)
            
            logger.info(f"AI summarization completed for recording {recording_id}: {summary_result['status']}")
            return summary_result
            
        except Exception as e:
            logger.error(f"Error triggering AI summarization for recording {recording_id}: {str(e)}")
            # Don't raise - summarization failure shouldn't fail chunk storage
            return {
                'status': 'error',
                'message': f'Error in AI summarization: {str(e)}',
                'recording_id': recording_id,
                'summaries_generated': 0
            }
    
    async def store_chunk_summaries(self, recording_id: str, chunk_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store LLM responses with full metadata in Supabase recordings table
        
        Args:
            recording_id: ID of the recording to associate summaries with
            chunk_summaries: List of chunk summary objects with metadata
            
        Returns:
            Supabase response
        """
        metadata = {
            "chunk_summaries": chunk_summaries,
            "storage_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        # Update recordings table metadata column
        response = self.supabase.table('recordings').update({
            'metadata': metadata
        }).eq('recording_id', recording_id).execute()
        
        return response
    
    async def get_chunk_summaries(self, recording_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve stored chunk summaries for a recording
        
        Args:
            recording_id: ID of the recording to retrieve summaries for
            
        Returns:
            List of chunk summary objects or empty list if not found
        """
        response = self.supabase.table('recordings').select('metadata').eq('recording_id', recording_id).execute()
        
        if response.data and len(response.data) > 0 and response.data[0]['metadata']:
            return response.data[0]['metadata'].get('chunk_summaries', [])
        return []
    
    async def update_recording_summaries(self, recording_id: str, 
                                       summary_short: str = None,
                                       summary_medium: str = None, 
                                       summary_detailed: str = None) -> Dict[str, Any]:
        """
        Update the final merged summaries in recordings table
        
        Args:
            recording_id: ID of the recording
            summary_short: Executive summary
            summary_medium: Key points summary  
            summary_detailed: Detailed summary
            
        Returns:
            Supabase response
        """
        update_data = {}
        if summary_short:
            update_data['summary_short'] = summary_short
        if summary_medium:
            update_data['summary_medium'] = summary_medium
        if summary_detailed:
            update_data['summary_detailed'] = summary_detailed
            
        if update_data:
            response = self.supabase.table('recordings').update(update_data).eq('recording_id', recording_id).execute()
            return response
        return {}


def create_chunk_summary_dict(chunk_id: str, chunk_text: str, 
                             executive_summary: List[str], key_points: List[str],
                             detailed_summary: str, model_used: str = "gpt-3.5-turbo",
                             token_count: int = None) -> Dict[str, Any]:
    """
    Helper function to create standardized chunk summary structure
    
    Args:
        chunk_id: Unique identifier for the chunk
        chunk_text: Original text content of the chunk
        executive_summary: List of executive summary bullet points
        key_points: List of key points
        detailed_summary: Comprehensive detailed summary text
        model_used: LLM model used for summarization
        token_count: Estimated token count for the chunk
        
    Returns:
        Standardized chunk summary dictionary
    """
    return {
        "chunk_id": chunk_id,
        "chunk_text": chunk_text,
        "executive_summary": executive_summary,
        "key_points": key_points,
        "detailed_summary": detailed_summary,
        "model_used": model_used,
        "timestamp": datetime.utcnow().isoformat(),
        "token_count": token_count or len(chunk_text) // 4  # Rough estimate
    }
