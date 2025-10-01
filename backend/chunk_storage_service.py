"""
Chunk Storage Service for persisting LLM responses with metadata in Supabase
"""

from supabase_client import get_supabase_client
from datetime import datetime
from typing import List, Dict, Any
import json


class ChunkStorageService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
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
        }).eq('id', recording_id).execute()
        
        return response
    
    async def get_chunk_summaries(self, recording_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve stored chunk summaries for a recording
        
        Args:
            recording_id: ID of the recording to retrieve summaries for
            
        Returns:
            List of chunk summary objects or empty list if not found
        """
        response = self.supabase.table('recordings').select('metadata').eq('id', recording_id).execute()
        
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
            response = self.supabase.table('recordings').update(update_data).eq('id', recording_id).execute()
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
