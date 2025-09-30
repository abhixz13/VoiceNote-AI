# Offline Testing Guide

This guide explains how to use the offline test script to process audio files and generate summaries locally.

## Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the `backend` directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Test with Audio File

```bash
# Test with a specific audio file
python test_offline.py path/to/your/audio.webm

# Example
python test_offline.py recordings/sample.webm
```

### Test with Sample Text (No Audio Required)

```bash
# Test text preprocessing without audio
python test_offline.py --sample-text
```

## What the Test Does

1. **API Connection Test**: Verifies OpenAI API access
2. **Audio Transcription**: Uses Whisper to transcribe the audio
3. **Summary Generation**: Creates short, medium, and detailed summaries
4. **Text Preprocessing**: Tests chunking with different sizes
5. **Results Saving**: Saves all results to JSON file

## Output

The script will:
- Display progress in the terminal
- Show transcription and summaries
- Test text preprocessing with different chunk sizes
- Save detailed results to `test_results/` directory

## Supported Audio Formats

- WebM (.webm)
- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- And other formats supported by OpenAI Whisper

## Example Output

```
🎵 Processing audio file: sample.webm
============================================================
🔗 Testing OpenAI API connection...
✅ API connection successful

🎤 Transcribing audio...
✅ Processing completed in 15.23 seconds

📝 Testing text preprocessing...
Original transcription length: 1250 characters

📊 Chunking results:
  - Small chunks (500 tokens): 3 chunks
  - Medium chunks (1000 tokens): 2 chunks
  - Large chunks (2000 tokens): 1 chunks

📋 Results Summary:
----------------------------------------
📁 Audio file: sample.webm
⏱️  Processing time: 15.23s
📝 Transcription length: 1250 chars
📊 Generated 3 summary types

📄 SHORT Summary:
------------------------------
This meeting discussed the new AI project focusing on machine learning models...

💾 Results saved to: test_results/test_results_20241227_143022.json
✅ Test completed successfully!
```

## Troubleshooting

- **API Key Error**: Make sure `OPENAI_API_KEY` is set in `.env` file
- **File Not Found**: Check the audio file path is correct
- **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
