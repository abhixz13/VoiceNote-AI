import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://lvrfxubfbqsiwcxqrmdr.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx2cmZ4dWJmYnFzaXdjeHFybWRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkwMTQ0NDMsImV4cCI6MjA3NDU5MDQ0M30.HOchmANamFiY5nV5y4UzuMzorUzdHNeEJ1lWJfBRt0k';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Storage bucket name
export const STORAGE_BUCKET = 'recordings';

// Temporary user ID for now (until authentication is implemented)
export const TEMP_USER_ID = 'temp-user';
