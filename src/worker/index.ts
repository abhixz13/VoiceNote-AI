import { Hono } from "hono";
import { cors } from "hono/cors";
import { zValidator } from "@hono/zod-validator";
import { 
  CreateRecordingSchema, 
  UpdateRecordingSchema,
  PaginationSchema,
  RecordingSchema,
  RecordingsListSchema
} from "../shared/types";

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

// POST /api/recordings/:id/transcribe - Start transcription job (placeholder)
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

    // TODO: Implement actual transcription job queue
    // For now, return a placeholder response
    return c.json({ 
      message: "Transcription job started",
      job_id: `job_${id}_${Date.now()}`,
      status: "processing"
    });
  } catch (error) {
    console.error("Error starting transcription:", error);
    return c.json({ error: "Failed to start transcription" }, 500);
  }
});

// Health check endpoint
app.get("/health", (c) => {
  return c.json({ status: "healthy", timestamp: now() });
});

export default app;
