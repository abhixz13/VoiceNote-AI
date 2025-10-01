Step 2: Map Stage (Per-chunk summaries)

For each chunk:

Send it to the model with a prompt that asks for two outputs:

Prompt Template (per chunk):
You are an expert summarizer. Summarize the following text.

[ChunkID: X]
[Chunk Text]

Tasks:
1) Executive Summary: 3-5 concise bullet points (≤25 words each).
2) Detailed Summary: 300–600 words with clear headings.

Output format:
---EXECUTIVE---
- ...
- ...
---DETAILED---
## Background
...
## Key Points
...
Output Stored as JSON:
{
  "chunk_id": "Chunk_01",
  "executive": ["point1", "point2", "point3"],
  "detailed": "long detailed text here..."
}

Step 3: Reduce Stage (Merging summaries)

A) Executive Summary Merge

Collect all per-chunk executives.

Ask model to synthesize into a single 6–10 bullet executive summary.

Prompt template
You are given executive summaries from multiple document chunks.

[EXECUTIVE_SUMMARIES]

Task:
1) Merge into one Executive Summary of 6–10 bullets.
2) Prioritize most important insights.
3) Avoid repetition.

B) Detailed Summary Merge

Option 1 — If all detailed summaries fit in context:

Concatenate all and ask for a single cohesive detailed summary (1000–2000 words).

Option 2 — If too large:

Hierarchical reduce:

Group 5 chunks → merge into group summary.

Then merge group summaries into a final summary.

Prompt Template (group merge):
You are given detailed summaries from several chunks.

[DETAILED_SUMMARIES_GROUP]

Task:
- Merge into one cohesive summary (~600–800 words).
- Keep structure: Background, Key Points, Evidence, Implications.
- Remove redundancy, keep clarity.

