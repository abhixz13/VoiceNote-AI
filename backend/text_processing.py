import re
import json
import logging
from typing import List
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from .supabase_client import get_supabase_client
    from .chunk_storage_service import ChunkStorageService
except ImportError:
    # Handle absolute imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from supabase_client import get_supabase_client
    from chunk_storage_service import ChunkStorageService

# Configure logging
logger = logging.getLogger(__name__)

def preprocess_and_chunk_text(
    text: str, 
    chunk_size_tokens: int = 2000, 
    chunk_overlap_tokens: int = 200
) -> List[str]:
    """
    Preprocesses raw Whisper transcription text and chunks it semantically.
    
    This single agent handles:
    1. Text cleaning and normalization
    2. Robust sentence segmentation using LangChain
    3. Semantic chunking with overlap
    
    Args:
        text: Raw transcription text from OpenAI Whisper
        chunk_size_tokens: Target chunk size in tokens (approx 4 chars = 1 token)
        chunk_overlap_tokens: Overlap between chunks in tokens
        
    Returns:
        List of cleaned, normalized, and semantically chunked text strings
    """
    
    # 1. Text Cleaning & Normalization (keep our custom logic)
    cleaned_text = _clean_and_normalize_text(text)
    
    # 2. Semantic Chunking with LangChain's proven implementation
    chunks = _chunk_with_langchain(cleaned_text, chunk_size_tokens, chunk_overlap_tokens)
    
    return chunks


def _clean_and_normalize_text(text: str) -> str:
    """Clean and normalize raw Whisper transcription text."""
    # Remove redundant whitespace (spaces, tabs, newlines)
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Convert to lowercase for consistency in summarization
    text = text.lower()
    return text


def _chunk_with_langchain(
    text: str, 
    chunk_size_tokens: int, 
    chunk_overlap_tokens: int
) -> List[str]:
    """
    Use LangChain's RecursiveCharacterTextSplitter for robust chunking.
    Converts token targets to character approximations (1 token ≈ 4 chars).
    """
    # Convert token targets to character approximations
    chunk_size_chars = chunk_size_tokens * 4
    chunk_overlap_chars = chunk_overlap_tokens * 4
    
    # Initialize LangChain's robust text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=chunk_overlap_chars,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]  # Recursive hierarchy
    )
    
    # Split the text into chunks
    chunks = text_splitter.split_text(text)
    
    return chunks


async def process_transcription(
    recording_id: str,
    transcription_id: str,
    transcription_text: str
) -> None:
    """
    Main entry point: Process transcription text, chunk it, and store chunks
    
    Args:
        recording_id: ID of the recording to process
        transcription_id: ID of the transcription record
        transcription_text: The actual transcription text
    """
    try:
        supabase = get_supabase_client()
        
        # Get user_id from recordings table
        recording_response = supabase.table('recordings').select('user_id').eq('id', recording_id).execute()
        if not recording_response.data:
            raise ValueError(f"Recording {recording_id} not found")
        user_id = recording_response.data[0]['user_id']
        
        # 1. We already have the transcription_text, no need to download
        # 2. Chunk the transcription
        chunks = preprocess_and_chunk_text(
            transcription_text,
            chunk_size_tokens=2000,
            chunk_overlap_tokens=200
        )
        logger.info(f"Generated {len(chunks)} chunks for recording {recording_id}")
        
        # 3. Use ChunkStorageService to store chunks
        chunk_storage = ChunkStorageService()
        storage_result = await chunk_storage.store_chunks(recording_id, transcription_id, chunks, user_id)
        logger.info(f"Stored {storage_result['chunks_stored']} chunks for recording {recording_id}")
        
        # Log summarization status
        if storage_result['summarization_status'] == 'success':
            logger.info(f"Unified summary generated successfully for recording {recording_id}")
            if storage_result.get('unified_summary'):
                logger.info(f"Unified summary contains {len(storage_result['unified_summary'].get('chunk_summaries', []))} chunk summaries")
        else:
            logger.warning(f"Summarization had issues: {storage_result.get('summarization_status', 'unknown')}")
        
        logger.info(f"Chunk processing completed for recording {recording_id}")
        
    except Exception as e:
        logger.error(f"Error processing transcription for {recording_id}: {str(e)}")
        raise


