# VoiceNote AI - Backend Architecture

## 📁 Project Structure

```
backend/
├── main.py                      # API Layer (FastAPI endpoints)
├── transcription_service.py     # Transcription business logic
├── ai_summary_service.py        # Summarization business logic
├── text_processing.py           # Text preprocessing & chunking
├── chunk_storage_service.py     # Chunk metadata storage
├── supabase_client.py          # Supabase client initialization
└── requirements.txt            # Python dependencies
```

## 🏗️ Architecture Overview

### **Separation of Concerns**

```
┌──────────────────────────────────────────────┐
│  main.py - API LAYER                         │
│  • FastAPI routes                            │
│  • Request/response handling                 │
│  • Service orchestration                     │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  SERVICE LAYER                               │
│  • transcription_service.py                  │
│  • ai_summary_service.py                     │
│  • Pure business logic                       │
│  • No HTTP/API concerns                      │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  DATA LAYER                                  │
│  • Supabase (Database + Storage)             │
│  • OpenAI API (Whisper + GPT)                │
└──────────────────────────────────────────────┘
```

## 🔄 Data Flow

### **1. Transcription Flow**

```
Frontend → POST /api/recordings/{id}/transcribe
    ↓
main.py (API Layer)
    ↓
TranscriptionService.transcribe_recording()
    ↓
1. Get recording info from Supabase DB
2. Download audio from Supabase Storage (recordings bucket)
3. Transcribe using OpenAI Whisper
4. Upload transcription.txt to Storage
5. Update DB with file path reference
```

### **2. Summarization Flow**

```
Frontend → POST /api/recordings/{id}/summarize
    ↓
main.py (API Layer)
    ↓
AISummaryService.generate_summaries_for_recording()
    ↓
1. Get recording info from Supabase DB
2. Download transcription.txt from Storage
3. Chunk text semantically
4. Generate chunk summaries (GPT-3.5-turbo)
5. Store chunk metadata in DB
6. Merge summaries (Reduce stage - TODO)
7. Update DB with final summaries
```

## 📊 Storage Pattern

### **Supabase Database (`recordings` table)**
Stores **metadata only**:
- `id` - Recording ID
- `file_path` - Path to audio file in storage
- `transcription` - Path to transcription file in storage
- `status` - 'recorded', 'processing', 'transcribed', 'error'
- `summary_short` - Executive summary
- `summary_medium` - Key points
- `summary_detailed` - Detailed summary
- `metadata` - JSONB (chunk summaries, errors, etc.)

### **Supabase Storage (`recordings` bucket)**
Stores **actual files**:
- `{recording_id}/audio.webm` - Audio file
- `{recording_id}/transcription.txt` - Transcription text

## 🚀 API Endpoints

### **Health Check**
```
GET /
Returns: Service status and version
```

### **Transcription**
```
POST /api/recordings/{recording_id}/transcribe
Returns: Transcription status and file path
```

### **Summarization**
```
POST /api/recordings/{recording_id}/summarize
Returns: Summary status and summaries
```

### **Full Processing**
```
POST /api/recordings/{recording_id}/process
Returns: Complete transcription + summarization
```

## 🔧 Service Initialization

Services are initialized **once at startup** (not per request):
```python
# main.py
transcription_service = TranscriptionService()
summary_service = AISummaryService()
```

This ensures:
- Better performance
- Persistent connections
- Resource efficiency

## 📝 Key Design Principles

1. **Clean Separation**: API layer separate from business logic
2. **Storage over DB**: Large text files in storage, metadata in DB
3. **Service Reusability**: Services can be used independently
4. **Error Handling**: Comprehensive error handling at all layers
5. **Async Operations**: All I/O operations are asynchronous

---

*Last updated: October 1, 2025*

