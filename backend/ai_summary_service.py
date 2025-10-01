"""
AISummaryService Layer
Reads chunks from Supabase Storage, generates summaries, and stores them
"""

import openai
import os
import json
from typing import Dict, List
from datetime import datetime
import logging

from supabase_client import get_supabase_client

class AISummaryService:
    def __init__(self):
        """Initialize the AI Summary Service"""
        # Initialize Supabase first
        self.supabase = get_supabase_client()
        
        # Initialize OpenAI client separately to avoid proxy conflicts
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.gpt_model = "gpt-3.5-turbo"
        self.max_tokens = 1500
        self.temperature = 0.7
        
    async def process_chunks_for_recording(self, recording_id: str) -> None:
        """
        Main entry point: Read chunks from Supabase Storage, generate summaries, and store them
        
        Args:
            recording_id: ID of the recording to process
        """
        try:
            self.logger.info(f"Processing chunks for recording {recording_id}")
            
            # 1. Get list of chunks from Supabase Storage
            chunks = await self._get_chunks_from_storage(recording_id)
            
            if not chunks:
                self.logger.warning(f"No chunks found for recording {recording_id}")
                return
            
            # 2. Process each chunk and generate summary
            for chunk_data in chunks:
                chunk_id = chunk_data['chunk_id']
                chunk_text = chunk_data['chunk_text']
                
                self.logger.info(f"Generating summary for {chunk_id}")
                
                # Generate summary using GPT
                summary = await self._generate_chunk_summary(chunk_text, chunk_id)
                
                # 3. Store summary in Supabase Storage "summaries" bucket
                await self._store_summary(recording_id, chunk_id, summary)
            
            self.logger.info(f"Completed summarization for recording {recording_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing chunks for recording {recording_id}: {str(e)}")
            raise
    
    async def _get_chunks_from_storage(self, recording_id: str) -> List[Dict]:
        """
        Download all chunks for a recording from Supabase Storage
        
        Args:
            recording_id: ID of the recording
            
        Returns:
            List of dicts containing chunk_id and chunk_text
        """
            try:
                # List all files in the recording's folder in Chunks bucket (note: capital C to match Supabase bucket name)
                files = self.supabase.storage.from_("Chunks").list(recording_id)
            
            chunks = []
            for file in files:
                if file['name'].endswith('.txt'):
                    # Extract chunk_id from filename (e.g., "chunk_001.txt" -> "chunk_001")
                    chunk_id = file['name'].replace('.txt', '')
                        chunk_file_path = f"{recording_id}/{file['name']}"
                        
                        # Download chunk content
                        chunk_content = self.supabase.storage.from_("Chunks").download(chunk_file_path)
                    chunk_text = chunk_content.decode('utf-8')
                    
                    chunks.append({
                        'chunk_id': chunk_id,
                        'chunk_text': chunk_text
                    })
            
            # Sort by chunk_id to maintain order
            chunks.sort(key=lambda x: x['chunk_id'])
            
            self.logger.info(f"Retrieved {len(chunks)} chunks for recording {recording_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error getting chunks from storage for {recording_id}: {str(e)}")
            return []
    
    async def _generate_chunk_summary(self, chunk_text: str, chunk_id: str) -> str:
        """
        Generate summary for a single chunk using GPT
        
        Args:
            chunk_text: The text content of the chunk
            chunk_id: Unique identifier for the chunk
            
        Returns:
            Summary text
        """
        try:
            # Build prompt for chunk summarization
            prompt = f"""You are an expert summarizer. Summarize the following text chunk concisely.

[ChunkID: {chunk_id}]
[Chunk Text]:
{chunk_text}

Provide a clear, concise summary (200-400 words) that captures the main ideas and key points."""

            # Call GPT-3.5-turbo
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are an expert AI summarizer. Provide clear and concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary = response.choices[0].message.content
            self.logger.info(f"Generated summary for {chunk_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary for {chunk_id}: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    async def _store_summary(self, recording_id: str, chunk_id: str, summary: str) -> None:
        """
        Store summary in Supabase Storage "summaries" bucket
        
        Args:
            recording_id: ID of the recording
            chunk_id: ID of the chunk
            summary: The generated summary text
        """
        try:
            summary_file_path = f"{recording_id}/{chunk_id}_summary.txt"
            
            # Create metadata
            metadata = {
                "recording_id": recording_id,
                "chunk_id": chunk_id,
                "created_at": datetime.now().isoformat()
            }
            
                # Upload summary to "Summaries" bucket (note: capital S to match Supabase bucket name)
                self.supabase.storage.from_("Summaries").upload(
                    summary_file_path,
                    summary.encode('utf-8'),
                    {
                        "content-type": "text/plain",
                        "x-metadata": json.dumps(metadata)
                    }
                )
            
            self.logger.info(f"Stored summary for {chunk_id} in recording {recording_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing summary for {chunk_id}: {str(e)}")
            raise
