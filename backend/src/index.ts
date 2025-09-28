import { Hono } from "hono";
import { cors } from "hono/cors";
import { zValidator } from "@hono/zod-validator";
import { createClient } from "@supabase/supabase-js";
import OpenAI from "openai";
import {
  CreateRecordingSchema,
  UpdateRecordingSchema,
  PaginationSchema,
  RecordingSchema,
  RecordingsListSchema
} from "../../utils/types/types";
import { Env } from "./types";

const app = new Hono<{ Bindings: Env }>();

// Enable CORS for the frontend
app.use("*", cors({
  origin: "*",
  allowHeaders: ["Content-Type", "Authorization"],
  allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}));

// Helper function to format timestamps
const formatTimestamp = (date: Date) => date.toISOString();

// Helper function to get current timestamp
const now = () => formatTimestamp(new Date());

// Initialize OpenAI client globally (or pass to functions)
let openai: OpenAI | undefined;

// Transcription Helper Function
const transcribeAudio = async (audioBlob: Blob, openaiClient: OpenAI): Promise<string> => {
  try {
    // Convert blob to file-like object for OpenAI API
    const audioFile = new File([audioBlob], 'audio.webm', { type: 'audio/webm' });
    
    const transcript = await openaiClient.audio.transcriptions.create({
      model: "whisper-1",
      file: audioFile,
      response_format: "text"
    });
    
    return transcript;
  } catch (error) {
    console.error("Error transcribing audio:", error);
    throw new Error(`Transcription failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Summarization Helper Function
const generateSummaries = async (transcription: string, openaiClient: OpenAI, videoInfo?: any): Promise<{
  summary_short: string;
  summary_medium: string;
  summary_detailed: string;
}> => {
  const summaryTypes = ['short', 'medium', 'detailed'];
  const summaries: { [key: string]: string } = {};
  
  for (const summaryType of summaryTypes) {
    try {
      const prompt = buildSummaryPrompt(transcription, summaryType, videoInfo);
      const summary = await callGptApi(prompt, openaiClient);
      summaries[`summary_${summaryType}`] = summary;
    } catch (error) {
      console.error(`Error generating ${summaryType} summary:`, error);
      summaries[`summary_${summaryType}`] = `Error generating ${summaryType} summary: ${error instanceof Error ? error.message : 'Unknown error'}`;
    }
  }
  
  return {
    summary_short: summaries.summary_short,
    summary_medium: summaries.summary_medium,
    summary_detailed: summaries.summary_detailed,
  };
};

// Helper function to build summary prompts (based on your AISummaryService)
const buildSummaryPrompt = (transcription: string, summaryType: string, videoInfo?: any): string => {
  let basePrompt = `Create a ${summaryType} summary of the following transcribed content.\n\nTranscription:\n${transcription}`;
  
  if (videoInfo) {
    basePrompt += `\n\nVideo Information:\n- Title: ${videoInfo.title || 'Unknown'}\n- Duration: ${videoInfo.duration || 'Unknown'}\n- Uploader: ${videoInfo.uploader || 'Unknown'}`;
  }
  
  if (summaryType === 'short') {
    basePrompt += `\n\nRequirements for short summary:\n- 2-3 sentences maximum\n- Focus on main topic and key takeaway\n- Be concise and direct`;
  } else if (summaryType === 'medium') {
    basePrompt += `\n\nRequirements for medium summary:\n- 1-2 paragraphs\n- Include main points and key insights\n- Mention important concepts or technologies`;
  } else { // detailed
    basePrompt += `\n\nRequirements for detailed summary:\n- Comprehensive overview\n- Structured with clear sections\n- Include technical details and explanations\n- Highlight key concepts and their applications\n- Provide actionable insights`;
  }
  
  return basePrompt;
};

// Helper function to call GPT API (based on your AISummaryService)
const callGptApi = async (prompt: string, openaiClient: OpenAI): Promise<string> => {
  try {
    const response = await openaiClient.chat.completions.create({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are an expert AI content analyst." },
        { role: "user", content: prompt }
      ],
      max_tokens: 2000,
      temperature: 0.7
    });
    return response.choices[0].message.content || '';
  } catch (error) {
    console.error("Error calling GPT API:", error);
    throw error;
  }
};

// GET /api/recordings - List recordings with pagination
app.get("/api/recordings", zValidator("query", PaginationSchema), async (c) => {
  const { page, limit } = c.req.valid("query");
  const offset = (page - 1) * limit;

  try {
    // Get total count
    const countResult = await c.env.DB.prepare(
      "SELECT COUNT(*) as count FROM recordings ORDER BY created_at DESC"
    ).first();
    
    const total = (countResult?.count as number) || 0;
    const total_pages = Math.ceil(total / limit);

    // Get recordings
    const recordings = await c.env.DB.prepare(
      "SELECT * FROM recordings ORDER BY created_at DESC LIMIT ? OFFSET ?"
    ).bind(limit, offset).all();

    const response = {
      recordings: recordings.results || [],
      total,
      page,
      limit,
      total_pages,
    };

    return c.json(RecordingsListSchema.parse(response));
  } catch (error) {
    console.error("Error fetching recordings:", error);
    return c.json({ error: "Failed to fetch recordings" }, 500);
  }
});

// GET /api/recordings/:id - Get a specific recording
app.get("/api/recordings/:id", async (c) => {
  const id = parseInt(c.req.param("id"));
  
  if (isNaN(id)) {
    return c.json({ error: "Invalid recording ID" }, 400);
  }

  try {
    const recording = await c.env.DB.prepare(
      "SELECT * FROM recordings WHERE id = ?"
    ).bind(id).first();

    if (!recording) {
      return c.json({ error: "Recording not found" }, 404);
    }

    return c.json(RecordingSchema.parse(recording));
  } catch (error) {
    console.error("Error fetching recording:", error);
    return c.json({ error: "Failed to fetch recording" }, 500);
  }
});

// POST /api/recordings - Create a new recording
app.post("/api/recordings", zValidator("json", CreateRecordingSchema), async (c) => {
  const data = c.req.valid("json");
  
  try {
    const timestamp = now();
    const result = await c.env.DB.prepare(`
      INSERT INTO recordings (title, duration_seconds, file_size_bytes, status, metadata, created_at, updated_at)
      VALUES (?, ?, ?, 'recorded', ?, ?, ?)
    `).bind(
      data.title,
      data.duration_seconds,
      data.file_size_bytes || null,
      data.metadata || null,
      timestamp,
      timestamp
    ).run();

    if (!result.success) {
      throw new Error("Failed to create recording");
    }

    const recording = await c.env.DB.prepare(
      "SELECT * FROM recordings WHERE id = ?"
    ).bind(result.meta.last_row_id).first();

    return c.json(RecordingSchema.parse(recording), 201);
  } catch (error) {
    console.error("Error creating recording:", error);
    return c.json({ error: "Failed to create recording" }, 500);
  }
});

// PUT /api/recordings/:id - Update a recording
app.put("/api/recordings/:id", zValidator("json", UpdateRecordingSchema), async (c) => {
  const id = parseInt(c.req.param("id"));
  const updates = c.req.valid("json");
  
  if (isNaN(id)) {
    return c.json({ error: "Invalid recording ID" }, 400);
  }

  try {
    // Check if recording exists
    const existing = await c.env.DB.prepare(
      "SELECT id FROM recordings WHERE id = ?"
    ).bind(id).first();

    if (!existing) {
      return c.json({ error: "Recording not found" }, 404);
    }

    // Build update query dynamically
    const updateFields: string[] = [];
    const updateValues: any[] = [];
    
    if (updates.title !== undefined) {
      updateFields.push("title = ?");
      updateValues.push(updates.title);
    }
    if (updates.status !== undefined) {
      updateFields.push("status = ?");
      updateValues.push(updates.status);
    }
    if (updates.transcription !== undefined) {
      updateFields.push("transcription = ?");
      updateValues.push(updates.transcription);
    }
    if (updates.summary_short !== undefined) {
      updateFields.push("summary_short = ?");
      updateValues.push(updates.summary_short);
    }
    if (updates.summary_medium !== undefined) {
      updateFields.push("summary_medium = ?");
      updateValues.push(updates.summary_medium);
    }
    if (updates.summary_detailed !== undefined) {
      updateFields.push("summary_detailed = ?");
      updateValues.push(updates.summary_detailed);
    }

    if (updateFields.length === 0) {
      return c.json({ error: "No fields to update" }, 400);
    }

    updateFields.push("updated_at = ?");
    updateValues.push(now());
    updateValues.push(id);

    await c.env.DB.prepare(`
      UPDATE recordings 
      SET ${updateFields.join(", ")}
      WHERE id = ?
    `).bind(...updateValues).run();

    // Return updated recording
    const recording = await c.env.DB.prepare(
      "SELECT * FROM recordings WHERE id = ?"
    ).bind(id).first();

    return c.json(RecordingSchema.parse(recording));
  } catch (error) {
    console.error("Error updating recording:", error);
    return c.json({ error: "Failed to update recording" }, 500);
  }
});

// DELETE /api/recordings/:id - Delete a recording
app.delete("/api/recordings/:id", async (c) => {
  const id = parseInt(c.req.param("id"));
  
  if (isNaN(id)) {
    return c.json({ error: "Invalid recording ID" }, 400);
  }

  try {
    const result = await c.env.DB.prepare(
      "DELETE FROM recordings WHERE id = ?"
    ).bind(id).run();

    if (!result.success) {
      return c.json({ error: "Recording not found" }, 404);
    }

    return c.json({ message: "Recording deleted successfully" });
  } catch (error) {
    console.error("Error deleting recording:", error);
    return c.json({ error: "Failed to delete recording" }, 500);
  }
});

// POST /api/recordings/:id/transcribe - Start transcription and summarization
app.post("/api/recordings/:id/transcribe", async (c) => {
  const id = parseInt(c.req.param("id"));
  
  if (isNaN(id)) {
    return c.json({ error: "Invalid recording ID" }, 400);
  }

  try {
    // Check if recording exists
    const recording = await c.env.DB.prepare(
      "SELECT * FROM recordings WHERE id = ?"
    ).bind(id).first();

    if (!recording) {
      return c.json({ error: "Recording not found" }, 404);
    }

    // Update status to processing
    await c.env.DB.prepare(
      "UPDATE recordings SET status = 'processing', updated_at = ? WHERE id = ?"
    ).bind(now(), id).run();

    // Initialize Supabase client with service role key
    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_SERVICE_ROLE_KEY);
    
    // Initialize OpenAI client
    const openaiClient = new OpenAI({
      apiKey: c.env.OPENAI_API_KEY,
    });

    // Download audio file from Supabase Storage
    const { data: audioData, error: downloadError } = await supabase.storage
      .from('recordings')
      .download(recording.file_path as string);

    if (downloadError || !audioData) {
      throw new Error(`Failed to download audio file: ${downloadError?.message || 'No data received'}`);
    }

    // Convert the downloaded data to a Blob
    const audioBlob = new Blob([await audioData.arrayBuffer()], { type: 'audio/webm' });

    // Step 1: Transcribe audio using Whisper
    console.log(`Starting transcription for recording ${id}...`);
    const transcription = await transcribeAudio(audioBlob, openaiClient);
    console.log(`Transcription completed for recording ${id}`);

    // Step 2: Generate summaries using GPT-4
    console.log(`Starting summarization for recording ${id}...`);
    const summaries = await generateSummaries(transcription, openaiClient);
    console.log(`Summarization completed for recording ${id}`);

    // Step 3: Update the recording with transcription and summaries
    await c.env.DB.prepare(`
      UPDATE recordings 
      SET transcription = ?, 
          summary_short = ?, 
          summary_medium = ?, 
          summary_detailed = ?, 
          status = 'transcribed', 
          updated_at = ?
      WHERE id = ?
    `).bind(
      transcription,
      summaries.summary_short,
      summaries.summary_medium,
      summaries.summary_detailed,
      now(),
      id
    ).run();

    return c.json({ 
      message: "Transcription and summarization completed successfully",
      recording_id: id,
      status: "transcribed",
      transcription_length: transcription.length,
      summaries_generated: Object.keys(summaries).length
    });

  } catch (error) {
    console.error("Error in transcription process:", error);
    
    // Update status to error if something went wrong
    try {
      await c.env.DB.prepare(
        "UPDATE recordings SET status = 'error', updated_at = ? WHERE id = ?"
      ).bind(now(), id).run();
    } catch (updateError) {
      console.error("Error updating recording status to error:", updateError);
    }
    
    return c.json({ 
      error: "Failed to process transcription", 
      details: error instanceof Error ? error.message : 'Unknown error',
      recording_id: id,
      status: "error"
    }, 500);
  }
});

// Health check endpoint
app.get("/health", (c) => {
  return c.json({ status: "healthy", timestamp: now() });
});

export default app;
