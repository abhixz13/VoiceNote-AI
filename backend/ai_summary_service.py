"""
AISummaryService Layer
Reads chunks from Supabase Storage, generates summaries, and stores them
"""

import openai
import os
import json
from typing import Dict, List, Tuple, Any
import uuid
from datetime import datetime
import logging

try:
    from .supabase_client import get_supabase_client
except ImportError:
    # Handle absolute imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
        
    async def process_chunks_for_recording(self, recording_id: str, chunk_data: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Main entry point: Generate chunk summaries and consolidated summary, return unified JSON
        
        Args:
            recording_id: ID of the recording to process
            chunk_data: List of (chunk_id, chunk_text) tuples
            
        Returns:
            Dictionary with unified JSON output structure
        """
        try:
            self.logger.info(f"Processing {len(chunk_data)} chunks for recording {recording_id}")
            
            if not chunk_data:
                self.logger.warning(f"No chunks provided for recording {recording_id}")
                return {
                    'status': 'error',
                    'message': 'No chunks provided for summarization',
                    'recording_id': recording_id
                }
            
            # Step 1: Generate chunk summaries
            chunk_summaries = []
            successful_summaries = 0
            failed_summaries = 0
            
            for chunk_id, chunk_text in chunk_data:
                try:
                    self.logger.info(f"Generating summary for chunk {chunk_id}")
                    
                    # Generate one detailed summary for the chunk
                    chunk_summary_text = await self._generate_chunk_summary(chunk_text, chunk_id)
                    
                    # Create chunk summary JSON
                    chunk_summary_json = await self._create_chunk_summary_json(recording_id, chunk_id, chunk_summary_text)
                    
                    chunk_summaries.append(chunk_summary_json)
                    successful_summaries += 1
                    
                except Exception as chunk_error:
                    self.logger.error(f"Error processing chunk {chunk_id}: {str(chunk_error)}")
                    failed_summaries += 1
            
            if not chunk_summaries:
                return {
                    'status': 'error',
                    'message': 'Failed to generate any chunk summaries',
                    'recording_id': recording_id
                }
            
            # Step 2: Generate consolidated summary from chunk summaries
            consolidated_summary = None
            try:
                consolidated_summary = await self._synthesize_chunk_summaries_to_consolidated(chunk_summaries, recording_id)
                self.logger.info(f"Generated consolidated summary for recording {recording_id}")
            except Exception as e:
                self.logger.error(f"Error generating consolidated summary for {recording_id}: {str(e)}")
                consolidated_summary = {
                    "executive_summary": f"Error generating consolidated summary: {str(e)}",
                    "key_points": "• Error occurred during consolidation",
                    "detailed_summary": f"Error generating consolidated summary: {str(e)}"
                }
            
            # Step 3: Create optimized unified JSON output
            # Convert chunk summaries to numbered format (chunk_1, chunk_2, etc.)
            chunk_summaries_dict = {}
            for i, chunk_summary in enumerate(chunk_summaries, 1):
                chunk_summaries_dict[f"chunk_{i}"] = {
                    "chunk_id": chunk_summary["chunk_id"],
                    "chunk_summary": chunk_summary["chunk_summary"]
                }
            
            unified_output = {
                "recording_id": recording_id,
                "created_at": datetime.now().isoformat(),
                "total_chunks": len(chunk_data),
                "successful_summaries": successful_summaries,
                "failed_summaries": failed_summaries,
                "chunk_summaries": chunk_summaries_dict,
                "consolidated_summary": consolidated_summary
            }
            
            # Step 4: Store unified JSON in Supabase and get summary metadata
            summary_metadata = await self._store_unified_summary_with_metadata(recording_id, unified_output)
            
            # Determine overall status
            if successful_summaries > 0 and failed_summaries == 0:
                status = 'success'
                message = f'Successfully generated summaries for all {successful_summaries} chunks and consolidated summary'
            elif successful_summaries > 0 and failed_summaries > 0:
                status = 'partial_success'
                message = f'Generated summaries for {successful_summaries} chunks, failed for {failed_summaries} chunks'
            else:
                status = 'error'
                message = f'Failed to generate summaries for all {failed_summaries} chunks'
            
            self.logger.info(f"Completed summarization for recording {recording_id}: {message}")
            
            return {
                'status': status,
                'message': message,
                'recording_id': recording_id,
                'unified_summary': unified_output,
                'summary_id': summary_metadata['summary_id'],
                'summary_path': summary_metadata['summary_path']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing chunks for recording {recording_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error in summarization process: {str(e)}',
                'recording_id': recording_id
            }
    
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
        Generate one detailed summary for a single chunk using GPT
        
        Args:
            chunk_text: The text content of the chunk
            chunk_id: Unique identifier for the chunk
            
        Returns:
            Detailed summary text for the chunk
        """
        try:
            # Build prompt for chunk summarization (only detailed summary)
            prompt = f"""You are an expert summarizer. Analyze the following text chunk and provide a comprehensive summary.

[ChunkID: {chunk_id}]
[Chunk Text]:
{chunk_text}

Provide a comprehensive 150-300 word summary that captures all important aspects, key information, and details from this text chunk. Focus on preserving the essential content while making it concise and well-structured.

Respond with just the summary text, no JSON formatting needed."""

            # Call GPT-3.5-turbo
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are an expert AI summarizer. Provide clear, comprehensive summaries that capture all important information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary_text = response.choices[0].message.content.strip()
            self.logger.info(f"Generated chunk summary for {chunk_id}")
            return summary_text
            
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
    
    async def _create_chunk_summary_json(self, recording_id: str, chunk_id: str, chunk_summary: str) -> Dict[str, str]:
        """
        Create chunk summary JSON with minimal required fields (optimized)
        
        Args:
            recording_id: ID of the recording
            chunk_id: ID of the chunk
            chunk_summary: The detailed summary text for the chunk
            
        Returns:
            Optimized chunk summary JSON structure
        """
        chunk_summary_json = {
            "chunk_id": chunk_id,
            "chunk_summary": chunk_summary
        }
        
        return chunk_summary_json
    
    async def _synthesize_chunk_summaries_to_consolidated(self, chunk_summaries: List[Dict], recording_id: str) -> Dict[str, str]:
        """
        Synthesize chunk summaries into consolidated executive, key points, and detailed summary
        
        Args:
            chunk_summaries: List of chunk summary dictionaries
            recording_id: ID of the recording
            
        Returns:
            Dictionary with consolidated executive_summary, key_points, detailed_summary
        """
        try:
            # Prepare input text from all chunk summaries
            consolidated_input = f"Recording ID: {recording_id}\n\n"
            consolidated_input += "CHUNK SUMMARIES TO SYNTHESIZE:\n"
            consolidated_input += "=" * 50 + "\n\n"
            
            for i, chunk_summary in enumerate(chunk_summaries, 1):
                consolidated_input += f"CHUNK {i} (ID: {chunk_summary['chunk_id']}):\n"
                consolidated_input += f"Summary: {chunk_summary['chunk_summary']}\n"
                consolidated_input += "-" * 30 + "\n\n"
            
            # Create reasoning prompt for consolidation
            prompt = f"""You are an expert AI reasoning model tasked with synthesizing multiple chunk-level summaries into one comprehensive, consolidated summary for an entire recording.

{consolidated_input}

TASK: Analyze all the chunk summaries above and create ONE consolidated summary that captures the complete essence of the entire recording. Look for:
- Overarching themes and main topics
- Key insights that span multiple chunks
- Important details that should be preserved
- Logical flow and connections between chunks

Please provide a consolidated summary in the following JSON format:
{{
  "executive_summary": "A comprehensive 3-4 sentence overview of the entire recording's main purpose and key outcomes",
  "key_points": "5-8 bullet points covering the most important insights, decisions, and information from the entire recording",
  "detailed_summary": "A comprehensive 300-500 word summary that captures all important aspects, themes, and details from the entire recording while maintaining logical flow"
}}

Focus on creating a cohesive narrative that represents the complete recording, not just a collection of chunk summaries."""

            # Call reasoning model (using GPT-4 for better synthesis)
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for better reasoning and synthesis
                messages=[
                    {"role": "system", "content": "You are an expert AI reasoning model specializing in synthesizing and consolidating information. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent reasoning
                max_tokens=2000   # Higher token limit for comprehensive summaries
            )
            
            synthesis_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                consolidated_summaries = json.loads(synthesis_text)
                self.logger.info(f"Successfully synthesized consolidated summary for recording {recording_id}")
                return consolidated_summaries
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                self.logger.warning(f"Failed to parse JSON for consolidated summary {recording_id}, using fallback format")
                return {
                    "executive_summary": synthesis_text[:300] + "...",
                    "key_points": f"• {synthesis_text[:200]}...",
                    "detailed_summary": synthesis_text
                }
            
        except Exception as e:
            self.logger.error(f"Error synthesizing summaries for {recording_id}: {str(e)}")
            return {
                "executive_summary": f"Error synthesizing summary: {str(e)}",
                "key_points": "• Error occurred during synthesis",
                "detailed_summary": f"Error synthesizing summary: {str(e)}"
            }
    
    async def _store_unified_summary_with_metadata(self, recording_id: str, unified_output: Dict[str, Any]) -> Dict[str, str]:
        """
        Store unified summary JSON in Supabase Summaries bucket and update summaries table
        
        Args:
            recording_id: ID of the recording
            unified_output: Complete unified summary JSON
            
        Returns:
            Dictionary with summary_id and summary_path
        """
        try:
            # Generate unique summary ID
            summary_id = str(uuid.uuid4())
            
            # Add summary_id to the unified output for reference
            unified_output["summary_id"] = summary_id
            
            # Store unified summary as JSON file in Summaries bucket using summary_id as filename
            summary_file_path = f"{summary_id}.json"
            
            try:
                self.supabase.storage.from_("Summaries").upload(
                    summary_file_path,
                    json.dumps(unified_output, indent=2).encode('utf-8'),
                    {"content-type": "application/json"}
                )
                self.logger.info(f"Stored unified summary {summary_id} for recording {recording_id}")
            except Exception as upload_error:
                if "already exists" in str(upload_error) or "Duplicate" in str(upload_error):
                    # Update existing file
                    self.supabase.storage.from_("Summaries").update(
                        summary_file_path,
                        json.dumps(unified_output, indent=2).encode('utf-8'),
                        {"content-type": "application/json"}
                    )
                    self.logger.info(f"Updated existing unified summary {summary_id} for recording {recording_id}")
                else:
                    raise upload_error
            
            # Update summaries table with metadata
            summary_path = f"Summaries/{summary_file_path}"
            summary_metadata = {
                "summary_id": summary_id,
                "recording_id": recording_id,
                "summary_path": summary_path,
                "created_at": datetime.now().isoformat()
            }
            
            try:
                response = self.supabase.table('summaries').insert(summary_metadata).execute()
                if not response.data:
                    self.logger.warning(f"Failed to insert summary metadata for {summary_id}")
                else:
                    self.logger.info(f"Updated summaries table for {summary_id}")
            except Exception as db_error:
                # Check if summary already exists
                existing_response = self.supabase.table('summaries').select('summary_id').eq('summary_id', summary_id).execute()
                if existing_response.data:
                    self.logger.info(f"Summary metadata already exists for {summary_id}")
                else:
                    self.logger.error(f"Error inserting summary metadata for {summary_id}: {db_error}")
                    # Don't raise - storage succeeded even if DB update failed
            
            return {
                'summary_id': summary_id,
                'summary_path': summary_path
            }
            
        except Exception as e:
            self.logger.error(f"Error storing unified summary for recording {recording_id}: {str(e)}")
            raise
    
    async def _store_summary_complete(self, recording_id: str, chunk_id: str, summary_json: Dict[str, str]) -> None:
        """
        Store summary JSON in Summaries storage bucket and update summaries table
        
        Args:
            recording_id: ID of the recording
            chunk_id: ID of the chunk
            summary_json: Complete summary JSON structure
        """
        try:
            summary_id = summary_json["summary_id"]
            
            # Store summary as JSON file in Summaries bucket
            summary_file_path = f"{recording_id}/{chunk_id}/{summary_id}.json"
            
            try:
                self.supabase.storage.from_("Summaries").upload(
                    summary_file_path,
                    json.dumps(summary_json, indent=2).encode('utf-8'),
                    {"content-type": "application/json"}
                )
                self.logger.info(f"Stored summary {summary_id} for chunk {chunk_id}")
                status = "Generated"
            except Exception as upload_error:
                if "already exists" in str(upload_error) or "Duplicate" in str(upload_error):
                    self.logger.info(f"Summary file already exists for {summary_id}, skipping upload...")
                    status = "Generated"
                else:
                    self.logger.error(f"Error uploading summary {summary_id}: {upload_error}")
                    status = "Unsuccessful"
            
            # Update summaries table with metadata
            summary_path = f"Summaries/{summary_file_path}"
            summary_metadata = {
                "summary_id": summary_id,
                "recording_id": recording_id,
                "chunk_id": chunk_id,
                "summary_path": summary_path,
                "status": status,
                "created_at": datetime.now().isoformat()
            }
            
            try:
                response = self.supabase.table('summary').insert(summary_metadata).execute()
                if not response.data:
                    self.logger.warning(f"Failed to insert summary metadata for {summary_id}")
                else:
                    self.logger.info(f"Updated summary table for {summary_id}")
            except Exception as db_error:
                # Check if summary already exists
                existing_response = self.supabase.table('summary').select('summary_id').eq('summary_id', summary_id).execute()
                if existing_response.data:
                    self.logger.info(f"Summary metadata already exists for {summary_id}")
                else:
                    self.logger.error(f"Error inserting summary metadata for {summary_id}: {db_error}")
                    # Don't raise - storage succeeded even if DB update failed
            
        except Exception as e:
            self.logger.error(f"Error storing summary for chunk {chunk_id}: {str(e)}")
            raise
    
