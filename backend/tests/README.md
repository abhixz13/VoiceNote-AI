# VoiceNote AI Test Suite

This directory contains comprehensive tests for the VoiceNote AI backend system.

## Test Structure

```
tests/
├── integration/
│   ├── test_transcription_to_chunks_integration.py  # Original chunk pipeline test
│   └── test_end_to_end_pipeline.py                  # Complete end-to-end test
├── unit/
│   ├── test_transcription_service.py                # Unit tests for transcription
│   └── test_chunk_storage_service.py                # Unit tests for chunk storage
└── utils/
    └── test_results/                                 # Test result artifacts
```

## Integration Tests

### 1. End-to-End Pipeline Test (`test_end_to_end_pipeline.py`)

**Purpose**: Tests the complete VoiceNote AI pipeline from transcription to unified summary generation.

**What it tests**:
- ✅ Audio transcription using OpenAI Whisper
- ✅ Text processing and semantic chunking
- ✅ Chunk storage in Supabase (storage + database)
- ✅ AI summarization for each chunk
- ✅ GPT-4 consolidation of chunk summaries
- ✅ Unified JSON generation and storage
- ✅ Summaries table updates
- ✅ Optimized JSON structure validation

**Pipeline Flow Tested**:
```
Audio Recording → Transcription → Text Processing → Chunk Storage → AI Summarization → Consolidated Summary → Unified JSON
```

**Run Command**:
```bash
# From backend directory
python tests/integration/test_end_to_end_pipeline.py

# Or using the test runner
python run_end_to_end_test.py
```

### 2. Transcription-to-Chunks Test (`test_transcription_to_chunks_integration.py`)

**Purpose**: Tests the transcription and chunking pipeline (subset of end-to-end test).

**What it tests**:
- ✅ Audio transcription
- ✅ Text processing and chunking
- ✅ Chunk storage and metadata

**Run Command**:
```bash
python tests/integration/test_transcription_to_chunks_integration.py
```

## Unit Tests

### 1. Transcription Service Tests (`test_transcription_service.py`)

**Purpose**: Tests `TranscriptionService` in isolation with mocked dependencies.

**Run Command**:
```bash
python tests/unit/test_transcription_service.py
```

### 2. Chunk Storage Service Tests (`test_chunk_storage_service.py`)

**Purpose**: Tests `ChunkStorageService` in isolation with mocked dependencies.

**Run Command**:
```bash
python tests/unit/test_chunk_storage_service.py
```

## Prerequisites

### Environment Variables
Create a `.env` file in the backend directory with:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### Test Data
The integration tests use a specific recording ID:
```
recording_id = "dd177ad1-a77b-40c0-a1ce-7ac98686e35a"
```

Ensure this recording exists in your Supabase `recordings` table with an associated audio file in the `recordings` storage bucket.

## Expected Test Results

### Successful End-to-End Test Output:
```
🧪 VoiceNote AI End-to-End Pipeline Integration Test
================================================================================
✅ Environment variables are set
🚀 Starting complete end-to-end pipeline test for recording: dd177ad1-a77b-40c0-a1ce-7ac98686e35a
================================================================================
📝 Step 1: Running complete summarization pipeline...
✅ Complete pipeline completed successfully
📋 Step 2: Verifying transcription table...
✅ Transcription record found
📦 Step 3: Verifying chunks in storage...
✅ Found X chunk files in storage
🗃️  Step 4: Verifying chunks table...
✅ Found X chunk records in database
📊 Step 5: Verifying summaries table...
✅ Found summary record in database
📄 Step 6: Verifying unified summary in Summary storage bucket...
✅ Successfully downloaded and parsed unified summary
🔍 Step 7: Verifying individual chunk content...
✅ Successfully downloaded and parsed chunk content
📊 Step 8: Verifying recording status...
✅ Recording status: transcribed
🔍 Step 9: Validating optimized JSON structure...
✅ JSON structure validation passed
================================================================================
🎉 END-TO-END INTEGRATION TEST PASSED!
```

## Troubleshooting

### Common Issues:

1. **Missing Environment Variables**
   - Ensure `.env` file exists with all required variables
   - Check variable names match exactly

2. **Recording Not Found**
   - Verify the test recording ID exists in your database
   - Check that the audio file exists in Supabase storage

3. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all dependencies are installed

4. **Supabase Connection Issues**
   - Verify Supabase URL and keys are correct
   - Check network connectivity

### Debug Mode:
Add `logging.basicConfig(level=logging.DEBUG)` to see detailed logs.

## Test Data Cleanup

The tests include optional cleanup functions that are commented out by default to prevent accidental data deletion. Uncomment the cleanup code in the test files if you want to clean up test data after running tests.

⚠️ **Warning**: Be careful with cleanup functions as they will delete real data from your Supabase instance.
