#!/usr/bin/env python3
"""
Offline Test Script for VoiceNote AI
Processes a saved audio file and generates summaries locally
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_summary_service import AISummaryService
from text_processing import preprocess_and_chunk_text

# Load environment variables
load_dotenv()

class OfflineTester:
    def __init__(self):
        """Initialize the offline tester"""
        self.ai_service = AISummaryService()
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def test_audio_file(self, audio_file_path: str, output_file: str = None):
        """
        Test processing of a saved audio file
        
        Args:
            audio_file_path: Path to the audio file to process
            output_file: Optional output file for results (default: auto-generated)
        """
        print(f"🎵 Processing audio file: {audio_file_path}")
        print("=" * 60)
        
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"❌ Error: Audio file not found: {audio_file_path}")
            return
        
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ Error: OPENAI_API_KEY not found in environment variables")
            print("Please set your OpenAI API key in .env file or environment")
            return
        
        try:
            # Step 1: Test API connection
            print("🔗 Testing OpenAI API connection...")
            connection_test = await self.ai_service.testConnection()
            if connection_test['status'] != 'success':
                print(f"❌ API connection failed: {connection_test}")
                return
            print("✅ API connection successful")
            
            # Step 2: Transcribe and summarize
            print("\n🎤 Transcribing audio...")
            start_time = datetime.now()
            
            result = await self.ai_service.generateRecordingSummaries(audio_file_path)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"✅ Processing completed in {processing_time:.2f} seconds")
            
            # Step 3: Test text preprocessing
            print("\n📝 Testing text preprocessing...")
            transcription = result['transcription']
            print(f"Original transcription length: {len(transcription)} characters")
            
            # Test preprocessing with different chunk sizes
            chunks_small = preprocess_and_chunk_text(transcription, chunk_size_tokens=500, chunk_overlap_tokens=50)
            chunks_medium = preprocess_and_chunk_text(transcription, chunk_size_tokens=1000, chunk_overlap_tokens=100)
            chunks_large = preprocess_and_chunk_text(transcription, chunk_size_tokens=2000, chunk_overlap_tokens=200)
            
            print(f"📊 Chunking results:")
            print(f"  - Small chunks (500 tokens): {len(chunks_small)} chunks")
            print(f"  - Medium chunks (1000 tokens): {len(chunks_medium)} chunks")
            print(f"  - Large chunks (2000 tokens): {len(chunks_large)} chunks")
            
            # Step 4: Display results
            print("\n📋 Results Summary:")
            print("-" * 40)
            print(f"📁 Audio file: {audio_file_path}")
            print(f"⏱️  Processing time: {processing_time:.2f}s")
            print(f"📝 Transcription length: {len(transcription)} chars")
            print(f"📊 Generated {len(result['summaries'])} summary types")
            
            # Display summaries
            for summary_type, summary in result['summaries'].items():
                print(f"\n📄 {summary_type.upper()} Summary:")
                print("-" * 30)
                print(summary[:200] + "..." if len(summary) > 200 else summary)
            
            # Step 5: Save results
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.results_dir / f"test_results_{timestamp}.json"
            
            # Prepare results for saving
            save_data = {
                'test_info': {
                    'audio_file': audio_file_path,
                    'processing_time_seconds': processing_time,
                    'timestamp': datetime.now().isoformat(),
                    'transcription_length': len(transcription)
                },
                'transcription': transcription,
                'summaries': result['summaries'],
                'preprocessing_test': {
                    'small_chunks': {
                        'count': len(chunks_small),
                        'chunks': chunks_small
                    },
                    'medium_chunks': {
                        'count': len(chunks_medium),
                        'chunks': chunks_medium
                    },
                    'large_chunks': {
                        'count': len(chunks_large),
                        'chunks': chunks_large
                    }
                },
                'metadata': result.get('metadata', {})
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {output_file}")
            print("✅ Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during processing: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def test_with_sample_text(self, sample_text_file: str = None):
        """
        Test preprocessing with sample text from file (no audio file needed)
        
        Args:
            sample_text_file: Path to text file to test preprocessing on
        """
        print("📝 Testing text preprocessing with sample text...")
        print("=" * 60)
        
        # Read text from file
        if sample_text_file and os.path.exists(sample_text_file):
            with open(sample_text_file, 'r', encoding='utf-8') as f:
                sample_text = f.read()
            print(f"📖 Reading from file: {sample_text_file}")
        else:
            # Fallback to default sample text
            sample_text = """
            Hello everyone, welcome to today's meeting. We're going to discuss the new AI project. 
            The project involves implementing machine learning models for natural language processing. 
            We need to focus on three main areas: data preprocessing, model training, and deployment. 
            The team has been working hard on this and we're making good progress. 
            Any questions about the technical implementation or timeline?
            """
            print("ℹ️  Using default sample text")
        
        print(f"Original text length: {len(sample_text)} characters")
        print(f"Sample text preview: {sample_text[:100]}...")
        
        # Test different chunk sizes
        chunk_sizes = [200, 500, 1000, 2000]
        
        for size in chunk_sizes:
            chunks = preprocess_and_chunk_text(sample_text, chunk_size_tokens=size, chunk_overlap_tokens=size//10)
            print(f"\n📊 Chunk size {size} tokens:")
            print(f"  - Generated {len(chunks)} chunks")
            for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                print(f"  - Chunk {i+1}: {chunk[:50]}...")
            if len(chunks) > 3:
                print(f"  - ... and {len(chunks) - 3} more chunks")

def print_usage():
    """Print usage instructions"""
    print("🎤 VoiceNote AI - Offline Test Script")
    print("=" * 50)
    print("Usage:")
    print("  python test_offline.py <audio_file_path>")
    print("  python test_offline.py --sample-text [text_file_path]")
    print("")
    print("Examples:")
    print("  python test_offline.py recordings/sample.webm")
    print("  python test_offline.py --sample-text")
    print("  python test_offline.py --sample-text sample_ai_text.txt")
    print("")
    print("Requirements:")
    print("  - Set OPENAI_API_KEY in .env file")
    print("  - Audio file should be in supported format (webm, mp3, wav, etc.)")

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    tester = OfflineTester()
    
    if sys.argv[1] == "--sample-text":
        # Test with sample text
        text_file = sys.argv[2] if len(sys.argv) > 2 else None
        await tester.test_with_sample_text(text_file)
    else:
        # Test with audio file
        audio_file = sys.argv[1]
        await tester.test_audio_file(audio_file)

if __name__ == "__main__":
    asyncio.run(main())
