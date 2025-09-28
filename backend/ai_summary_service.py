"""
AISummaryService Layer
Handles audio transcription and text summarization using OpenAI APIs
"""

import openai
import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

class AISummaryService:
    def __init__(self):
        """Initialize the AI Summary Service"""
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.whisper_model = "whisper-1"
        self.gpt_model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    async def generateRecordingSummaries(self, audio_file_path: str, video_info: Dict = None) -> Dict:
        """
        Generate comprehensive summaries from a recording
        
        Args:
            audio_file_path: Path to the audio file
            video_info: Optional video metadata
            
        Returns:
            Dict containing transcription and summaries
        """
        try:
            # Step 1: Transcribe audio using Whisper
            transcription = await self._transcribe_audio(audio_file_path)
            
            # Step 2: Generate multiple summary types
            summaries = await self._generate_summaries(transcription, video_info)
            
            # Step 3: Combine results
            result = {
                'transcription': transcription,
                'summaries': summaries,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'audio_file': audio_file_path,
                    'video_info': video_info or {}
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating summaries: {str(e)}")
            return await self._generate_fallback_summary(audio_file_path, str(e))
    
    async def regenerateSummary(self, transcription: str, summary_type: str = "detailed") -> str:
        """
        Regenerate a specific type of summary from existing transcription
        
        Args:
            transcription: The transcribed text
            summary_type: Type of summary (short, medium, detailed)
            
        Returns:
            Regenerated summary
        """
        try:
            prompt = self._build_summary_prompt(transcription, summary_type)
            
            response = await self._call_gpt_api(prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"Error regenerating summary: {str(e)}")
            return f"Error regenerating {summary_type} summary: {str(e)}"
    
    async def generateLiveSummary(self, audio_chunk: bytes, previous_context: str = "") -> str:
        """
        Generate live summary from audio chunk (for real-time processing)
        
        Args:
            audio_chunk: Audio data chunk
            previous_context: Previous summary context
            
        Returns:
            Live summary update
        """
        try:
            # Transcribe the chunk
            transcription = await self._transcribe_audio_chunk(audio_chunk)
            
            # Generate incremental summary
            prompt = self._build_live_summary_prompt(transcription, previous_context)
            response = await self._call_gpt_api(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating live summary: {str(e)}")
            return ""
    
    async def testConnection(self) -> Dict:
        """
        Test OpenAI API connection and return status
        
        Returns:
            Dict with connection status and available models
        """
        try:
            # Test GPT API
            test_response = await self._call_gpt_api("Hello, this is a connection test.")
            gpt_status = "connected" if test_response else "failed"
            
            # Get available models
            models = await self.getAvailableModels()
            
            return {
                'status': 'success',
                'gpt_api': gpt_status,
                'whisper_api': 'available',  # Whisper doesn't have a test endpoint
                'available_models': models,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def getAvailableModels(self) -> List[str]:
        """
        Get list of available OpenAI models
        
        Returns:
            List of available model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id or 'whisper' in model.id]
        except Exception as e:
            self.logger.error(f"Error getting models: {str(e)}")
            return ['gpt-4', 'gpt-3.5-turbo', 'whisper-1']  # Fallback
    
    # Private methods
    
    async def _transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file using Whisper API"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file,
                    response_format="text"
                )
            return transcript
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    async def _transcribe_audio_chunk(self, audio_chunk: bytes) -> str:
        """Transcribe audio chunk for live processing"""
        # For live processing, we'd need to save chunk to temp file
        # This is a simplified version
        temp_file = f"temp_chunk_{datetime.now().timestamp()}.wav"
        try:
            with open(temp_file, 'wb') as f:
                f.write(audio_chunk)
            return await self._transcribe_audio(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    async def _generate_summaries(self, transcription: str, video_info: Dict = None) -> Dict:
        """Generate multiple types of summaries"""
        summary_types = ['short', 'medium', 'detailed']
        summaries = {}
        
        for summary_type in summary_types:
            try:
                prompt = self._build_summary_prompt(transcription, summary_type, video_info)
                summary = await self._call_gpt_api(prompt)
                summaries[summary_type] = summary
            except Exception as e:
                self.logger.error(f"Error generating {summary_type} summary: {str(e)}")
                summaries[summary_type] = f"Error generating {summary_type} summary"
        
        return summaries
    
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
    
    def _build_live_summary_prompt(self, transcription: str, previous_context: str) -> str:
        """Build prompt for live summary generation"""
        return f"""
        Generate a brief summary update based on this new content, considering the previous context.
        
        Previous context: {previous_context}
        
        New content: {transcription}
        
        Provide a concise update that builds on the previous summary.
        """
    
    async def _generate_fallback_summary(self, audio_file_path: str, error: str) -> Dict:
        """Generate fallback summary when main process fails"""
        return {
            'transcription': f"Transcription failed: {error}",
            'summaries': {
                'short': f"Unable to process audio file: {error}",
                'medium': f"Audio processing failed. Error: {error}",
                'detailed': f"Failed to generate summary from {audio_file_path}. Error details: {error}"
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'audio_file': audio_file_path,
                'error': error,
                'fallback': True
            }
        }
