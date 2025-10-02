
import unittest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

# Add the project root directory (three levels up) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the Supabase client before importing TranscriptionService
with patch('backend.supabase_client.get_supabase_client') as mock_supabase:
    mock_supabase.return_value = AsyncMock()
    from backend.transcription_service import TranscriptionService

class TestTranscriptionService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock environment variables first
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://mock-supabase-url.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vY2siLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjQwOTk1MjAwLCJleHAiOjE5NTY1NzEyMDB9.mock_signature',
            'OPENAI_API_KEY': 'sk-mock_openai_key'
        })
        self.env_patcher.start()

        # Mock Supabase client before creating service
        self.mock_supabase_client = AsyncMock()
        self.supabase_client_patcher = patch('backend.supabase_client.get_supabase_client',
                                             return_value=self.mock_supabase_client)
        self.supabase_client_patcher.start()

        # Mock OpenAI client before creating service
        self.mock_openai_client = AsyncMock()
        self.openai_patcher = patch('openai.OpenAI', return_value=self.mock_openai_client)
        self.openai_patcher.start()

        # Now create the service with mocks in place
        self.service = TranscriptionService()

    def tearDown(self):
        self.env_patcher.stop()
        self.supabase_client_patcher.stop()
        self.openai_patcher.stop()

    async def test_transcribe_recording_success(self):
        # Arrange
        recording_id = "test_recording_id"
        mock_file_path = "recordings/test_user/audio.webm"
        mock_audio_content = b"mock audio data"
        mock_transcription_text = "This is a mock transcription."
        
        # Mock _get_recording_info
        self.service._get_recording_info = AsyncMock(return_value={
            'recording_id': recording_id,
            'file_path': mock_file_path,
            'user_id': 'test_user_id'
        })
        
        # Mock _download_audio_file
        self.service._download_audio_file = AsyncMock(return_value=mock_audio_content)
        
        # Mock _transcribe_audio_content
        self.service._transcribe_audio_content = AsyncMock(return_value=mock_transcription_text)
        
        # Mock _update_recording_transcription to return a transcription_id
        self.service._update_recording_transcription = AsyncMock(return_value="mock_transcription_id")
        
        # Mock _trigger_text_processing - we don't test text_processing integration here
        self.service._trigger_text_processing = AsyncMock(return_value=None)

        # Act
        result = await self.service.transcribe_recording(recording_id)

        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['recording_id'], recording_id)
        self.assertEqual(result['transcription'], mock_transcription_text)

        self.service._get_recording_info.assert_called_once_with(recording_id)
        self.service._download_audio_file.assert_called_once_with(mock_file_path)
        self.service._transcribe_audio_content.assert_called_once_with(mock_audio_content)
        self.service._update_recording_transcription.assert_called_once_with(recording_id, mock_transcription_text)
        self.service._trigger_text_processing.assert_called_once_with(recording_id, "mock_transcription_id", mock_transcription_text)

if __name__ == '__main__':
    unittest.main()
