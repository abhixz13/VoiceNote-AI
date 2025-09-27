
CREATE TABLE recordings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  duration_seconds INTEGER NOT NULL,
  file_size_bytes INTEGER,
  file_path TEXT,
  status TEXT NOT NULL DEFAULT 'recorded', -- recorded, processing, transcribed, error
  transcription TEXT,
  summary_short TEXT,
  summary_medium TEXT,
  summary_detailed TEXT,
  metadata TEXT, -- JSON blob for additional data
  user_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transcription_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recording_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
  job_type TEXT NOT NULL, -- transcription, summary_short, summary_medium, summary_detailed
  result TEXT,
  error_message TEXT,
  started_at DATETIME,
  completed_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recordings_user_id ON recordings(user_id);
CREATE INDEX idx_recordings_status ON recordings(status);
CREATE INDEX idx_recordings_created_at ON recordings(created_at DESC);
CREATE INDEX idx_transcription_jobs_recording_id ON transcription_jobs(recording_id);
CREATE INDEX idx_transcription_jobs_status ON transcription_jobs(status);
