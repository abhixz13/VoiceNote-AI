import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Save, Upload, Settings, Volume2 } from 'lucide-react';
import { useAudioRecording } from '@/hooks/useAudioRecording';
import WaveformDisplay from '@/components/WaveformDisplay';
import RecordingControls from '@/components/RecordingControls';
import RecordingTimer from '@/components/RecordingTimer';
import { v4 as uuidv4 } from 'uuid';

export default function Record() {
  const navigate = useNavigate();
  const [recordingState, recordingControls] = useAudioRecording();
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [gain, setGain] = useState(1.0);
  const [noiseReduction, setNoiseReduction] = useState(true);

  const handleSave = async () => {
    if (!recordingState.audioBlob) return;

    setSaving(true);
    try {
      const recordingTitle = title.trim() || `Recording ${new Date().toLocaleString()}`;
      
      // Create recording metadata
      const metadata = {
        notes: notes.trim(),
        gain,
        noiseReduction,
        recordingId: uuidv4(),
      };

      // Call API to create recording
      const response = await fetch('/api/recordings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: recordingTitle,
          duration_seconds: recordingState.duration,
          file_size_bytes: recordingState.audioBlob.size,
          metadata: JSON.stringify(metadata),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save recording');
      }

      const recording = await response.json();
      
      // TODO: Implement file upload to cloud storage
      console.log('Recording saved:', recording);
      
      // Reset form and navigate to recordings list
      recordingControls.clearRecording();
      setTitle('');
      setNotes('');
      navigate('/recordings');
      
    } catch (error) {
      console.error('Error saving recording:', error);
      // TODO: Show error toast
    } finally {
      setSaving(false);
    }
  };

  const handleUploadAndTranscribe = async () => {
    await handleSave();
    // TODO: Trigger transcription job
  };

  const canSave = recordingState.audioBlob && !saving;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Voice Recording
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Record high-quality audio with AI-powered transcription
          </p>
        </div>

        {/* Main Recording Interface */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-6">
            {/* Recording Timer */}
            <div className="text-center mb-8">
              <RecordingTimer
                duration={recordingState.duration}
                isRecording={recordingState.isRecording}
                isPaused={recordingState.isPaused}
              />
            </div>

            {/* Waveform Display */}
            <div className="mb-8">
              <WaveformDisplay
                amplitudeData={recordingState.amplitudeData}
                isRecording={recordingState.isRecording}
                isPaused={recordingState.isPaused}
                className="h-32"
              />
            </div>

            {/* Recording Controls */}
            <div className="flex justify-center mb-8">
              <RecordingControls
                isRecording={recordingState.isRecording}
                isPaused={recordingState.isPaused}
                hasRecording={!!recordingState.audioBlob}
                onStart={recordingControls.startRecording}
                onPause={recordingControls.pauseRecording}
                onResume={recordingControls.resumeRecording}
                onStop={recordingControls.stopRecording}
                onClear={recordingControls.clearRecording}
              />
            </div>

            {/* Error Display */}
            {recordingState.error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700">{recordingState.error}</p>
              </div>
            )}

            {/* Audio Playback */}
            {recordingState.audioUrl && (
              <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-4">
                  <Volume2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <audio controls className="flex-1" src={recordingState.audioUrl} />
                </div>
              </div>
            )}

            {/* Recording Details Form */}
            <div className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Recording Title
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter a title for your recording..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any notes about this recording..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            {/* Advanced Controls */}
            <div className="mt-6">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                <Settings className="w-4 h-4" />
                Advanced Settings
              </button>

              {showAdvanced && (
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Input Gain: {gain.toFixed(1)}x
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="2.0"
                      step="0.1"
                      value={gain}
                      onChange={(e) => setGain(parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="noiseReduction"
                      checked={noiseReduction}
                      onChange={(e) => setNoiseReduction(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="noiseReduction" className="text-sm text-gray-700 dark:text-gray-300">
                      Enable noise reduction
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            {recordingState.audioBlob && (
              <div className="flex gap-4 mt-8">
                <button
                  onClick={handleSave}
                  disabled={!canSave}
                  className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  <Save className="w-5 h-5" />
                  {saving ? 'Saving...' : 'Save Recording'}
                </button>

                <button
                  onClick={handleUploadAndTranscribe}
                  disabled={!canSave}
                  className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  <Upload className="w-5 h-5" />
                  {saving ? 'Processing...' : 'Save & Transcribe'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
