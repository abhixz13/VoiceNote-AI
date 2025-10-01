import re
import json
import logging
from typing import List
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from supabase_client import get_supabase_client

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


async def process_transcription(recording_id: str) -> None:
    """
    Main entry point: Download transcription, chunk it, store chunks, and trigger summarization
    
    Args:
        recording_id: ID of the recording to process
    """
    try:
        supabase = get_supabase_client()
        
        # 1. Get transcription file path from database
        recording = supabase.table('recordings').select('*').eq('id', recording_id).execute()
        if not recording.data:
            logger.error(f"Recording {recording_id} not found")
            return
        
        transcription_file_path = recording.data[0].get('transcription')
        if not transcription_file_path:
            logger.error(f"No transcription found for recording {recording_id}")
            return
        
        # 2. Download transcription from Supabase Storage
        transcription_content = supabase.storage.from_("transcription").download(transcription_file_path)
        transcription = transcription_content.decode('utf-8')
        logger.info(f"Downloaded transcription for recording {recording_id}")
        
        # 3. Chunk the transcription
        chunks = preprocess_and_chunk_text(
            transcription,
            chunk_size_tokens=2000,
            chunk_overlap_tokens=200
        )
        logger.info(f"Generated {len(chunks)} chunks for recording {recording_id}")
        
        # 4. Store each chunk in Supabase Storage bucket "chunks"
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"chunk_{i+1:03d}"
            chunk_file_path = f"{recording_id}/{chunk_id}.txt"
            
            # Create metadata for the chunk
            metadata = {
                "recording_id": recording_id,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": datetime.now().isoformat()
            }
            
            # Upload chunk to "chunks" bucket
            supabase.storage.from_("chunks").upload(
                chunk_file_path,
                chunk_text.encode('utf-8'),
                {
                    "content-type": "text/plain",
                    "x-metadata": json.dumps(metadata)
                }
            )
            
            logger.info(f"Stored {chunk_id} for recording {recording_id}")
        
        # 5. Trigger AI Summary Service
        await _trigger_summarization(recording_id)
        
        logger.info(f"Text processing completed for recording {recording_id}")
        
    except Exception as e:
        logger.error(f"Error processing transcription for {recording_id}: {str(e)}")
        raise


async def _trigger_summarization(recording_id: str) -> None:
    """
    Trigger AI summarization service to process chunks
    
    Args:
        recording_id: ID of the recording
    """
    try:
        from ai_summary_service import AISummaryService
        
        logger.info(f"Triggering summarization for recording {recording_id}")
        
        # Call AI Summary Service
        summary_service = AISummaryService()
        await summary_service.process_chunks_for_recording(recording_id)
        
        logger.info(f"Summarization completed for recording {recording_id}")
        
    except Exception as e:
        logger.error(f"Error triggering summarization for {recording_id}: {str(e)}")
        # Don't raise - summarization failure shouldn't fail text processing
