import z from "zod";

// Recording status types
export const RecordingStatus = z.enum(['recorded', 'processing', 'transcribed', 'error']);
export type RecordingStatusType = z.infer<typeof RecordingStatus>;

// Job status types  
export const JobStatus = z.enum(['pending', 'processing', 'completed', 'failed']);
export type JobStatusType = z.infer<typeof JobStatus>;

export const JobType = z.enum(['transcription', 'summary_short', 'summary_medium', 'summary_detailed']);
export type JobTypeType = z.infer<typeof JobType>;

// Recording schema
export const RecordingSchema = z.object({
  recording_id: z.string(), // UUID field as primary key
  title: z.string(),
  duration_seconds: z.number(),
  file_size_bytes: z.number().nullable(),
  file_path: z.string().nullable(),
  status: RecordingStatus,
  transcription: z.string().nullable(),
  summary_short: z.string().nullable(),
  summary_medium: z.string().nullable(),
  summary_detailed: z.string().nullable(),
  metadata: z.string().nullable(),
  user_id: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type RecordingType = z.infer<typeof RecordingSchema>;

// Transcription job schema
export const TranscriptionJobSchema = z.object({
  id: z.number(),
  recording_id: z.string(), // UUID string to match recordings table
  status: JobStatus,
  job_type: JobType,
  result: z.string().nullable(),
  error_message: z.string().nullable(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type TranscriptionJobType = z.infer<typeof TranscriptionJobSchema>;

// API request/response schemas
export const CreateRecordingSchema = z.object({
  title: z.string().min(1),
  duration_seconds: z.number().min(0),
  file_size_bytes: z.number().optional(),
  metadata: z.string().optional(),
});

export const UpdateRecordingSchema = z.object({
  title: z.string().optional(),
  status: RecordingStatus.optional(),
  transcription: z.string().optional(),
  summary_short: z.string().optional(),
  summary_medium: z.string().optional(),
  summary_detailed: z.string().optional(),
});

export const PaginationSchema = z.object({
  page: z.string().transform(Number).pipe(z.number().min(1)).default(1),
  limit: z.string().transform(Number).pipe(z.number().min(1).max(100)).default(20),
});

export const RecordingsListSchema = z.object({
  recordings: z.array(RecordingSchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  total_pages: z.number(),
});

export type RecordingsListType = z.infer<typeof RecordingsListSchema>;

// Upload response schema
export const UploadResponseSchema = z.object({
  recording_id: z.string(), // UUID string, not number
  upload_url: z.string(),
  upload_headers: z.record(z.string(), z.string()).optional(),
});

export type UploadResponseType = z.infer<typeof UploadResponseSchema>;
