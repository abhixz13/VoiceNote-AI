Ingestion — accept transcripts (raw text, time-aligned ASR JSON, or streaming ASR).

Preprocess & Segment — clean text, normalize, detect speakers, split into semantically-coherent chunks.

Embed & Index — create embeddings for chunks and store in vector DB (for retrieval & provenance).

Chunk Summarizer (map stage) — summarize each chunk locally (LLM or smaller model).

Merge + Refine (reduce stage) — combine chunk summaries into hierarchical summary and refine with a final LLM pass.

Factuality & Attribution — run fact-checking/consistency checks, optionally attach timestamps and source sentences.

Postprocess & Format — produce persona variants, bullet/ECE/structured outputs, and annotations (confidence, citations).

UI / API / Storage — expose endpoints and UI for results, store transcripts and summaries securely.

Monitoring & Feedback Loop — collect user ratings to retrain or tune summarization prompts/models.