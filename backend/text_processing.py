import re
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

def preprocess_and_chunk_text(
    text: str, 
    chunk_size_tokens: int = 2000, 
    chunk_overlap_tokens: int = 200
) -> List[str]:
    """
    Preprocesses raw Whisper transcription text and chunks it semantically.
    
    This single agent handles:
    1. Text cleaning and normalization
    2. Robust sentence segmentation using LangChain
    3. Semantic chunking with overlap
    
    Args:
        text: Raw transcription text from OpenAI Whisper
        chunk_size_tokens: Target chunk size in tokens (approx 4 chars = 1 token)
        chunk_overlap_tokens: Overlap between chunks in tokens
        
    Returns:
        List of cleaned, normalized, and semantically chunked text strings
    """
    
    # 1. Text Cleaning & Normalization (keep our custom logic)
    cleaned_text = _clean_and_normalize_text(text)
    
    # 2. Semantic Chunking with LangChain's proven implementation
    chunks = _chunk_with_langchain(cleaned_text, chunk_size_tokens, chunk_overlap_tokens)
    
    return chunks


def _clean_and_normalize_text(text: str) -> str:
    """Clean and normalize raw Whisper transcription text."""
    # Remove redundant whitespace (spaces, tabs, newlines)
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Convert to lowercase for consistency in summarization
    text = text.lower()
    return text


def _chunk_with_langchain(
    text: str, 
    chunk_size_tokens: int, 
    chunk_overlap_tokens: int
) -> List[str]:
    """
    Use LangChain's RecursiveCharacterTextSplitter for robust chunking.
    Converts token targets to character approximations (1 token ≈ 4 chars).
    """
    # Convert token targets to character approximations
    chunk_size_chars = chunk_size_tokens * 4
    chunk_overlap_chars = chunk_overlap_tokens * 4
    
    # Initialize LangChain's robust text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=chunk_overlap_chars,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]  # Recursive hierarchy
    )
    
    # Split the text into chunks
    chunks = text_splitter.split_text(text)
    
    return chunks


# Example usage and test
def _test_preprocessing():
    """Test function to demonstrate the preprocessing agent."""
    # Sample Whisper-like transcription with potential artifacts
    sample_text = """
    um hello everyone welcome to the meeting today. we're going to discuss the new project. 
    the project is about AI summarization. it's very important. uh let me repeat that: 
    AI summarization is the key focus. we need to implement this properly. any questions? 
    no questions? great! let's move on to the next topic which is deployment strategies. 
    we'll discuss cloud deployment options. this is a very long sentence that might not have proper punctuation because sometimes in speech we just keep talking without clear breaks you know what I mean it's like when you're explaining something complex and you don't want to interrupt the flow of thought so you just keep going and going until you finally take a breath.
    """
    
    print("Original text:")
    print(repr(sample_text))
    print("\n" + "="*50 + "\n")
    
    # Process the text
    chunks = preprocess_and_chunk_text(sample_text, chunk_size_tokens=100, chunk_overlap_tokens=20)
    
    print(f"Generated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
        print(chunk)


if __name__ == "__main__":
    _test_preprocessing()
