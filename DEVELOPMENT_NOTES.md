# Development Notes

## Supabase Configuration

### Row Level Security (RLS) - Recordings Table
- **Issue**: RLS was enabled on the recordings table, blocking insert operations
- **Temporary Solution**: RLS disabled for testing/development
- **Production Requirement**: Implement proper RLS policies for authenticated users
  - Allow users to insert/update/delete only their own recordings
  - Consider using user_id field for proper access control

### Database Schema Requirements
- Recordings table should include: id, title, duration_seconds, file_size_bytes, file_path, file_url, metadata, user_id, created_at, updated_at, status
- File path structure: `{userId}/{recordingId}.webm`
- Storage bucket: "recordings"

## Audio Recording Behavior
- **Expected**: Browser only captures microphone input (not system audio)
- **Phone audio**: ✅ Records properly
- **MacBook system audio**: ❌ Does not record (this is correct browser behavior)

## Testing Status
- ✅ Audio capture working
- ✅ Waveform display working  
- ✅ Timer working
- ✅ Supabase Storage upload working (after RLS fix)
- 🔄 End-to-end testing in progress
