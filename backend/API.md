# VoiceNote AI Backend API Documentation

This document outlines the API endpoints available in the VoiceNote AI backend service.

## Base URL
The API is served from the root of the application (e.g., `http://localhost:8000`).

---

## 1. Health Check Endpoints

### 1.1 Root Endpoint
- **Path**: `/`
- **Method**: `GET`
- **Description**: Basic root endpoint to confirm the service is running.
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "VoiceNote AI Backend",
    "version": "1.0.0",
    "timestamp": "ISO_FORMAT_DATETIME"
  }
  ```

### 1.2 Health Endpoint
- **Path**: `/health`
- **Method**: `GET`
- **Description**: Health check endpoint for monitoring, specifically for platforms like Railway.
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "VoiceNote AI Backend",
    "version": "1.0.0",
    "timestamp": "ISO_FORMAT_DATETIME"
  }
  ```

---

## 2. Transcription Endpoints

### 2.1 Transcribe Recording
- **Path**: `/api/recordings/{recording_id}/transcribe`
- **Method**: `POST`
- **Description**: Transcribes an audio recording from Supabase storage. If the transcription is successful, it triggers the text processing pipeline (chunking and storage).
- **Path Parameters**:
  - `recording_id` (string, required): The unique identifier of the recording to transcribe.
- **Request Body**: None
- **Response Model**: `TranscriptionResponse`
  - `status` (string): "success" or "error".
  - `recording_id` (string): The ID of the recording.
  - `transcription_file_path` (string, optional): Path to the transcribed text file in Supabase storage.
  - `error` (string, optional): Error message if transcription fails.
  - `timestamp` (string): Timestamp of the response.
- **Example Successful Response**:
  ```json
  {
    "status": "success",
    "recording_id": "dd177ad1-a77b-40c0-a1ce-7ac98686e35a",
    "transcription_file_path": "Transcription/dd177ad1-a77b-40c0-a1ce-7ac98686e35a/transcription.txt",
    "error": null,
    "timestamp": "2025-10-02T01:43:14.085141+00:00"
  }
  ```
- **Example Error Response**:
  ```json
  {
    "detail": "Error message from transcription service"
  }
  ```

---

## 3. Summarization Endpoints

### 3.1 Summarize Recording
- **Path**: `/api/recordings/{recording_id}/summarize`
- **Method**: `POST`
- **Description**: Generates summaries for a given recording. This endpoint orchestrates the entire process: if no transcription exists, it first transcribes the recording; otherwise, it proceeds directly to text processing (chunking, storing chunks, triggering AI summarization for each chunk, and then synthesizing all chunk summaries into one consolidated summary for the entire recording).
- **Path Parameters**:
  - `recording_id` (string, required): The unique identifier of the recording to summarize.
- **Request Body**: None
- **Response Model**: `SummaryResponse`
  - `status` (string): "success", "partial_success", or "error".
  - `recording_id` (string): The ID of the recording.
  - `unified_summary` (object, optional): Complete unified JSON structure containing chunk summaries and consolidated summary.
  - `message` (string, optional): Status message indicating the outcome of summarization.
  - `error` (string, optional): Error message if summarization fails.
  - `timestamp` (string): Timestamp of the response.
- **Example Successful Response**:
  ```json
  {
    "status": "success",
    "recording_id": "dd177ad1-a77b-40c0-a1ce-7ac98686e35a",
    "unified_summary": {
      "recording_id": "dd177ad1-a77b-40c0-a1ce-7ac98686e35a",
      "chunk_summaries": [
        {
          "recording_id": "dd177ad1-a77b-40c0-a1ce-7ac98686e35a",
          "chunk_id": "9ac7f843-0ab6-4b69-bdbe-5a8cb087dfe9",
          "summary_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
          "chunk_summary": "Detailed summary of chunk content...",
          "created_at": "2025-10-02T01:43:14.085141+00:00",
          "model_used": "gpt-3.5-turbo"
        }
      ],
      "consolidated_summary": {
        "executive_summary": "Comprehensive overview of the entire recording...",
        "key_points": "• Key insight 1\n• Key insight 2\n• Key insight 3",
        "detailed_summary": "Comprehensive 300-500 word summary of the entire recording..."
      },
      "metadata": {
        "total_chunks": 1,
        "successful_summaries": 1,
        "failed_summaries": 0,
        "created_at": "2025-10-02T01:43:14.085141+00:00",
        "model_used": "gpt-3.5-turbo"
      }
    },
    "message": "Summary generation completed successfully",
    "error": null,
    "timestamp": "2025-10-02T01:43:14.085141+00:00"
  }
  ```
- **Example Error Response**:
  ```json
  {
    "detail": "Error message from summarization service"
  }
  ```
---

## 4. Combined Processing Endpoint

### 4.1 Process Recording (Transcribe + Summarize)
- **Path**: `/api/recordings/{recording_id}/process`
- **Method**: `POST`
- **Description**: A combined endpoint that first transcribes and then summarizes a recording. This uses `BackgroundTasks` to potentially handle long-running operations.
- **Path Parameters**:
  - `recording_id` (string, required): The unique identifier of the recording to process.
- **Request Body**: None
- **Response**:
  - `status` (string): "success" or "error".
  - `recording_id` (string): The ID of the recording.
  - `message` (string): A descriptive message about the processing outcome.
  - `transcription_file_path` (string, optional): Path to the transcribed text file.
  - `summaries` (object, optional): Details about generated summaries.
  - `timestamp` (string): Timestamp of the response.
- **Example Successful Response**:
  ```json
  {
    "status": "success",
    "recording_id": "dd177ad1-a77b-40c0-a1ce-7ac98686e35a",
    "message": "Recording transcribed and summarized successfully",
    "transcription_file_path": "Transcription/dd177ad1-a77b-40c0-a1ce-7ac98686e35a/transcription.txt",
    "summaries": {
      "status": "success",
      "message": "Successfully generated summaries for all 1 chunks",
      "summaries_generated": 1,
      "summaries_failed": 0,
      "summary_ids": ["uuid_of_summary"]
    },
    "timestamp": "2025-10-02T01:43:14.085141+00:00"
  }
  ```
- **Example Error Response**:
   ```json
   {
     "detail": "Error message from processing service"
   }
   ```

---

## 5. Unified JSON Output Structure

### 5.1 Complete Unified Summary
The system now generates one comprehensive JSON structure containing both chunk-level summaries and a consolidated summary for the entire recording.

**Storage Location**: `Summary/{summary_id}.json`

### 5.2 Optimized Unified JSON Structure
```json
{
  "recording_id": "recording_uuid",
  "summary_id": "summary_uuid",
  "created_at": "timestamp",
  "total_chunks": 3,
  "successful_summaries": 3,
  "failed_summaries": 0,
  "chunk_summaries": {
    "chunk_1": {
      "chunk_id": "chunk_uuid_1",
      "chunk_summary": "Detailed summary of first chunk..."
    },
    "chunk_2": {
      "chunk_id": "chunk_uuid_2", 
      "chunk_summary": "Detailed summary of second chunk..."
    },
    "chunk_3": {
      "chunk_id": "chunk_uuid_3",
      "chunk_summary": "Detailed summary of third chunk..."
    }
  },
  "consolidated_summary": {
    "executive_summary": "3-4 sentence overview of entire recording",
    "key_points": "5-8 bullet points of key insights from entire recording",
    "detailed_summary": "300-500 word comprehensive summary of entire recording"
  }
}
```

### 5.3 Key Optimizations
- **Eliminated Duplication**: Common fields (`recording_id`, `created_at`, `summary_id`) appear only once at the top level
- **Numbered Chunks**: Chunk summaries organized as `chunk_1`, `chunk_2`, etc. for easy access
- **Minimal Chunk Data**: Each chunk contains only `chunk_id` and `chunk_summary` (no redundant metadata)
- **Consolidated Metadata**: Processing statistics integrated at the top level
- **Removed Unnecessary Fields**: Eliminated `model_used` and duplicate timestamps

### 5.4 Supabase Integration

#### Database Tables
- **`summaries`**: Metadata for unified summaries
  - `summary_id` (uuid): Unique identifier for the summary
  - `recording_id` (uuid): Reference to the recording
  - `summary_path` (text): Path to summary JSON in Summary storage bucket
  - `created_at` (timestamptz): Timestamp when summary was created
- **`chunk`**: Metadata for text chunks
- **`transcription`**: Metadata for transcription files

#### Storage Buckets
- **`Summary`**: Contains unified summary JSON files
  - File naming: `{summary_id}.json`
  - Content: Complete unified JSON structure with chunk summaries and consolidated summary
