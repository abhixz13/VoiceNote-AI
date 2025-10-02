#!/usr/bin/env python3
"""
Unit test for ChunkStorageService
Tests chunk storage functionality in isolation with mocked dependencies
"""
import unittest
import asyncio
import os
import sys
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Add the project root directory (three levels up) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the Supabase client before importing ChunkStorageService
with patch('backend.supabase_client.get_supabase_client') as mock_supabase:
    mock_supabase.return_value = AsyncMock()
    from backend.chunk_storage_service import ChunkStorageService

class TestChunkStorageService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://mock-supabase-url.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'mock_supabase_key'
        })
        self.env_patcher.start()

        # Mock Supabase client
        self.mock_supabase_client = AsyncMock()
        self.supabase_client_patcher = patch('backend.supabase_client.get_supabase_client',
                                             return_value=self.mock_supabase_client)
        self.supabase_client_patcher.start()

        # Create service instance
        self.service = ChunkStorageService()

    def tearDown(self):
        self.env_patcher.stop()
        self.supabase_client_patcher.stop()

    async def test_store_chunks_success(self):
        """Test successful chunk storage"""
        # Arrange
        recording_id = "test_recording_id"
        transcription_id = "test_transcription_id"
        user_id = "test_user_id"
        chunks = [
            "This is the first chunk of text.",
            "This is the second chunk of text.",
            "This is the third chunk of text."
        ]

        # Mock storage upload success
        self.mock_supabase_client.storage.from_.return_value.upload.return_value = {"success": True}
        
        # Mock database insert success
        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"chunk_id": "mock_chunk_id"}]
        self.mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

        # Act
        with patch('uuid.uuid4') as mock_uuid:
            # Mock UUID generation to return predictable values
            mock_uuid.side_effect = [
                MagicMock(spec=str, __str__=lambda x: f"chunk_id_{i}")
                for i in range(len(chunks))
            ]
            
            result_chunk_ids = await self.service.store_chunks(recording_id, transcription_id, chunks, user_id)

        # Assert
        self.assertEqual(len(result_chunk_ids), 3)
        self.assertEqual(result_chunk_ids, ["chunk_id_0", "chunk_id_1", "chunk_id_2"])

        # Verify storage uploads were called
        self.assertEqual(self.mock_supabase_client.storage.from_.call_count, 3)
        self.assertEqual(self.mock_supabase_client.storage.from_.return_value.upload.call_count, 3)

        # Verify database inserts were called
        self.assertEqual(self.mock_supabase_client.table.call_count, 3)
        self.assertEqual(self.mock_supabase_client.table.return_value.insert.call_count, 3)

        # Verify the structure of uploaded data
        upload_calls = self.mock_supabase_client.storage.from_.return_value.upload.call_args_list
        
        for i, call in enumerate(upload_calls):
            file_path, content, headers = call[0]
            
            # Check file path format
            expected_path = f"{recording_id}/{transcription_id}/chunk_id_{i}.json"
            self.assertEqual(file_path, expected_path)
            
            # Check content structure
            chunk_data = json.loads(content.decode('utf-8'))
            self.assertEqual(chunk_data['chunk_id'], f"chunk_id_{i}")
            self.assertEqual(chunk_data['recording_id'], recording_id)
            self.assertEqual(chunk_data['transcription_id'], transcription_id)
            self.assertEqual(chunk_data['chunk_data'], chunks[i])
            self.assertEqual(chunk_data['chunk_number'], i + 1)
            self.assertEqual(chunk_data['total_chunks'], len(chunks))
            self.assertIn('created_at', chunk_data)
            
            # Check headers
            self.assertEqual(headers['content-type'], 'application/json')

    async def test_store_chunks_duplicate_handling(self):
        """Test handling of duplicate chunks"""
        # Arrange
        recording_id = "test_recording_id"
        transcription_id = "test_transcription_id"
        user_id = "test_user_id"
        chunks = ["Test chunk"]

        # Mock storage upload to raise duplicate error
        duplicate_error = Exception("The resource already exists")
        self.mock_supabase_client.storage.from_.return_value.upload.side_effect = duplicate_error
        
        # Mock database insert success
        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"chunk_id": "mock_chunk_id"}]
        self.mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

        # Act & Assert - should not raise exception
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.__str__ = lambda x: "test_chunk_id"
            
            result_chunk_ids = await self.service.store_chunks(recording_id, transcription_id, chunks, user_id)
            
        # Should still return chunk IDs even with duplicate storage files
        self.assertEqual(len(result_chunk_ids), 1)
        self.assertEqual(result_chunk_ids[0], "test_chunk_id")

    async def test_store_chunks_database_duplicate_handling(self):
        """Test handling of duplicate database entries"""
        # Arrange
        recording_id = "test_recording_id"
        transcription_id = "test_transcription_id"
        user_id = "test_user_id"
        chunks = ["Test chunk"]

        # Mock storage upload success
        self.mock_supabase_client.storage.from_.return_value.upload.return_value = {"success": True}
        
        # Mock database insert to raise error, then mock existing record check
        db_error = Exception("duplicate key value violates unique constraint")
        self.mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = db_error
        
        # Mock existing record check
        mock_existing_response = MagicMock()
        mock_existing_response.data = [{"chunk_id": "existing_chunk_id"}]
        self.mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_existing_response

        # Act & Assert - should not raise exception
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.__str__ = lambda x: "test_chunk_id"
            
            result_chunk_ids = await self.service.store_chunks(recording_id, transcription_id, chunks, user_id)
            
        # Should still return chunk IDs even with duplicate database entries
        self.assertEqual(len(result_chunk_ids), 1)
        self.assertEqual(result_chunk_ids[0], "test_chunk_id")

if __name__ == '__main__':
    unittest.main()
