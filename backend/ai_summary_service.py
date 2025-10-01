"""
AISummaryService Layer
Handles audio transcription and text summarization using OpenAI APIs
"""

import openai
import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Import the new chunk storage service
from chunk_storage_service import ChunkStorageService, create_chunk_summary_dict

class AISummaryService:
    def __init__(self):
        """Initialize the AI Summary Service"""
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.logger = logging.getLogger(__name__)
        
        # Initialize chunk storage service
        self.storage_service = ChunkStorageService()
        
        # Configuration
        self.whisper_model = "whisper-1"
        self.gpt_model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    async def generateSummaries(self, transcription: str, video_info: Dict = None, recording_id: str = None) -> Dict:
        """
        Generate comprehensive summaries from a recording
        
        Args:
            transcription: The transcribed text content
            video_info: Optional video metadata
            recording_id: ID of the recording for storage
            
        Returns:
            Dict containing transcription and summaries
        """
        try:
            # Step 2: Generate multiple summary types
            summaries = await self._generate_summaries(transcription, video_info, recording_id)
            
            # Step 3: Combine results
            result = {
                'transcription': transcription,
                'summaries': summaries,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'audio_file': "Supabase transcription", # Indicate it's a transcription
                    'video_info': video_info or {}
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating summaries: {str(e)}")
            return await self._generate_fallback_summary(transcription, str(e))
    
    async def _generate_summaries(self, transcription: str, video_info: Dict = None, recording_id: str = None) -> Dict:
        """Generate summaries using map-reduce approach with real chunk processing"""
        
        # Import the existing chunking function
        from text_processing import preprocess_and_chunk_text
        
        # 1. First chunk the transcription using existing function
        chunks = preprocess_and_chunk_text(transcription, chunk_size_tokens=2000, chunk_overlap_tokens=200)
        self.logger.info(f"Generated {len(chunks)} semantic chunks from transcription")
        
        # Store for chunk summaries
        chunk_summaries = []
        
        # 2. Process each chunk through LLM (Map Stage)
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"Chunk_{i+1:02d}"
            self.logger.info(f"Processing {chunk_id} ({len(chunk_text)} chars)")
            
            try:
                # Process chunk through LLM for executive, key points, and detailed summary
                chunk_result = await self._process_chunk(chunk_text, chunk_id)
                
                # Create standardized chunk summary for storage
                chunk_summary = create_chunk_summary_dict(
                    chunk_id=chunk_id,
                    chunk_text=chunk_text,
                    executive_summary=chunk_result['executive_summary'],
                    key_points=chunk_result['key_points'],
                    detailed_summary=chunk_result['detailed_summary'],
                    model_used="gpt-3.5-turbo"  # Using GPT-3.5 for chunks as planned
                )
                chunk_summaries.append(chunk_summary)
                
            except Exception as e:
                self.logger.error(f"Error processing {chunk_id}: {str(e)}")
                # Create fallback chunk summary
                chunk_summary = create_chunk_summary_dict(
                    chunk_id=chunk_id,
                    chunk_text=chunk_text,
                    executive_summary=["Error processing chunk"],
                    key_points=["Failed to generate key points"],
                    detailed_summary=f"Error: {str(e)}",
                    model_used="error"
                )
                chunk_summaries.append(chunk_summary)
        
        # 3. Store all chunk summaries in Supabase
        if recording_id and chunk_summaries:
            try:
                await self.storage_service.store_chunk_summaries(recording_id, chunk_summaries)
                self.logger.info(f"Stored {len(chunk_summaries)} real chunk summaries for recording {recording_id}")
            except Exception as e:
                self.logger.error(f"Error storing chunk summaries: {str(e)}")
        
        # 4. TODO: Implement reduce stage - merge chunk summaries into final comprehensive summaries
        # For now, return basic summaries as placeholder
        summaries = {
            'short': "Executive summary placeholder (reduce stage needed)",
            'medium': "Key points placeholder (reduce stage needed)", 
            'detailed': "Detailed summary placeholder (reduce stage needed)"
        }
        
        return summaries
    
    async def _process_chunk(self, chunk_text: str, chunk_id: str) -> Dict[str, Any]:
        """
        Process a single chunk through LLM to generate executive, key points, and detailed summary
        
        Args:
            chunk_text: The text content of the chunk
            chunk_id: Unique identifier for the chunk
            
        Returns:
            Dictionary with executive_summary, key_points, and detailed_summary
        """
        try:
            # Build prompt for chunk summarization (Map Stage)
            prompt = f"""You are an expert summarizer. Summarize the following text chunk.

[ChunkID: {chunk_id}]
[Chunk Text]:
{chunk_text}

Tasks:
1) Executive Summary: Provide 3-5 concise bullet points (≤25 words each) capturing the main ideas.
2) Key Points: List 4-6 specific key points or facts from the text.
3) Detailed Summary: Write a comprehensive summary (300-600 words) with clear structure.

Output format (use exactly this structure):
---EXECUTIVE---
- [point 1]
- [point 2]
- [point 3]
---KEYPOINTS---
- [key point 1]
- [key point 2]
- [key point 3]
- [key point 4]
---DETAILED---
[Detailed summary with clear headings and structure]
"""
            
            # Call GPT-3.5-turbo
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert AI summarizer. Provide clear, concise, and well-structured summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Extract sections
            executive_summary = self._extract_section(content, "---EXECUTIVE---", "---KEYPOINTS---")
            key_points = self._extract_section(content, "---KEYPOINTS---", "---DETAILED---")
            detailed_summary = self._extract_section(content, "---DETAILED---", None)
            
            return {
                'executive_summary': [line.strip('- ').strip() for line in executive_summary.split('\n') if line.strip().startswith('-')],
                'key_points': [line.strip('- ').strip() for line in key_points.split('\n') if line.strip().startswith('-')],
                'detailed_summary': detailed_summary.strip()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk_id}: {str(e)}")
            # Fallback response
            return {
                'executive_summary': [f"Error processing {chunk_id}"],
                'key_points': ["Failed to generate key points"],
                'detailed_summary': f"Error: {str(e)}"
            }
    
    def _extract_section(self, content: str, start_marker: str, end_marker: str = None) -> str:
        """Extract a section between markers"""
        try:
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return ""
            
            start_idx += len(start_marker)
            
            if end_marker:
                end_idx = content.find(end_marker, start_idx)
                if end_idx == -1:
                    return content[start_idx:].strip()
                return content[start_idx:end_idx].strip()
            else:
                return content[start_idx:].strip()
        except Exception as e:
            self.logger.error(f"Error extracting section: {str(e)}")
            return ""
    
    async def _call_gpt_api(self, prompt: str) -> str:
        """Make API call to GPT"""
        try:
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are an expert AI content analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error calling GPT API: {str(e)}")
            raise
    
    def _build_summary_prompt(self, transcription: str, summary_type: str, video_info: Dict = None) -> str:
        """Build appropriate prompt based on summary type"""
        base_prompt = f"""
        Create a {summary_type} summary of the following transcribed content.
        
        Transcription:
        {transcription}
        """
        
        if video_info:
            base_prompt += f"""
            
            Video Information:
            - Title: {video_info.get('title', 'Unknown')}
            - Duration: {video_info.get('duration', 'Unknown')}
            - Uploader: {video_info.get('uploader', 'Unknown')}
            """
        
        if summary_type == 'short':
            base_prompt += """
            
            Requirements for short summary:
            - 2-3 sentences maximum
            - Focus on main topic and key takeaway
            - Be concise and direct
            """
        elif summary_type == 'medium':
            base_prompt += """
            
            Requirements for medium summary:
            - 1-2 paragraphs
            - Include main points and key insights
            - Mention important concepts or technologies
            """
        else:  # detailed
            base_prompt += """
            
            Requirements for detailed summary:
            - Comprehensive overview
            - Structured with clear sections
            - Include technical details and explanations
            - Highlight key concepts and their applications
            - Provide actionable insights
            """
        
        return base_prompt

    async def _generate_fallback_summary(self, transcription: str, error: str) -> Dict:
        """Generate fallback summary when main process fails"""
        return {
            'transcription': transcription,
            'summaries': {
                'short': f"Unable to generate summary: {error}",
                'medium': f"Summary generation failed. Error: {error}",
                'detailed': f"Failed to generate summary. Error details: {error}"
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'error': error,
                'fallback': True
            }
        }
