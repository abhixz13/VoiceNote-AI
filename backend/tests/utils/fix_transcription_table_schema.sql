-- Fix the transcription table schema
-- This script should be run in your Supabase SQL editor

-- First, let's see the current schema (run this to check):
-- \d transcription;

-- Option 1: If the table is empty or you can recreate it
-- DROP TABLE IF EXISTS transcription;

-- Create the transcription table with proper schema
CREATE TABLE IF NOT EXISTS transcription (
  transcription_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  recording_id UUID NOT NULL,
  user_id TEXT NOT NULL,
  transcription_path TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Foreign key constraint (if recordings table uses UUID)
  CONSTRAINT fk_transcription_recording 
    FOREIGN KEY (recording_id) 
    REFERENCES recordings(recording_id)
    ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transcription_recording_id ON transcription(recording_id);
CREATE INDEX IF NOT EXISTS idx_transcription_user_id ON transcription(user_id);
CREATE INDEX IF NOT EXISTS idx_transcription_created_at ON transcription(created_at DESC);

-- Option 2: If you want to alter the existing table instead of recreating
-- (Only run this if the table exists and has the wrong schema)
-- ALTER TABLE transcription 
-- ALTER COLUMN transcription_id SET DEFAULT gen_random_uuid();

-- If transcription_id is not UUID type, you might need to:
-- ALTER TABLE transcription 
-- ALTER COLUMN transcription_id TYPE UUID USING transcription_id::UUID;
-- ALTER TABLE transcription 
-- ALTER COLUMN transcription_id SET DEFAULT gen_random_uuid();
