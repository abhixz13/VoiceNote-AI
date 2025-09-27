import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ArrowLeft, Play, Download, RefreshCw, Clock, FileAudio, Loader2 } from 'lucide-react';
import { RecordingType } from '../../../utils/types/types';

export default function RecordingDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [recording, setRecording] = useState<RecordingType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'short' | 'medium' | 'detailed'>('short');
  const [transcribing, setTranscribing] = useState(false);

  const fetchRecording = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/recordings/${id}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Recording not found');
        }
        throw new Error('Failed to fetch recording');
      }

      const data: RecordingType = await response.json();
      setRecording(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recording');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecording();
  }, [id]);

  const handleTranscribe = async () => {
    if (!recording) return;

    setTranscribing(true);
    try {
      const response = await fetch(`/api/recordings/${recording.id}/transcribe`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to start transcription');
      }

      // Refresh recording data
      await fetchRecording();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start transcription');
    } finally {
      setTranscribing(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium";
    
    switch (status) {
      case 'recorded':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300`;
      case 'processing':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300`;
      case 'transcribed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300`;
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading recording...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !recording) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <FileAudio className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {error || 'Recording not found'}
              </h2>
              <button
                onClick={() => navigate('/recordings')}
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Recordings
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/recordings')}
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Recordings
          </button>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Recording Info */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {recording.title}
                </h1>
                <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {formatDuration(recording.duration_seconds)}
                  </div>
                  <span>{formatDate(recording.created_at)}</span>
                  {recording.file_size_bytes && (
                    <span>
                      {(recording.file_size_bytes / 1024 / 1024).toFixed(1)} MB
                    </span>
                  )}
                </div>
              </div>
              <span className={getStatusBadge(recording.status)}>
                {recording.status.charAt(0).toUpperCase() + recording.status.slice(1)}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 mb-6">
              <button className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                <Play className="w-4 h-4" />
                Play Audio
              </button>
              <button className="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300">
                <Download className="w-4 h-4" />
                Download
              </button>
              <button
                onClick={handleTranscribe}
                disabled={transcribing}
                className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                {transcribing ? 'Processing...' : 'Re-transcribe'}
              </button>
            </div>

            {/* Metadata */}
            {recording.metadata && (
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Recording Notes
                </h3>
                <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {JSON.parse(recording.metadata).notes || 'No notes added'}
                </pre>
              </div>
            )}
          </div>

          {/* Transcription */}
          {recording.transcription && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Transcription
              </h2>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {recording.transcription}
                </p>
              </div>
            </div>
          )}

          {/* Summaries */}
          {(recording.summary_short || recording.summary_medium || recording.summary_detailed) && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                AI Summaries
              </h2>

              {/* Tabs */}
              <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
                {[
                  { key: 'short', label: 'Short', available: !!recording.summary_short },
                  { key: 'medium', label: 'Medium', available: !!recording.summary_medium },
                  { key: 'detailed', label: 'Detailed', available: !!recording.summary_detailed },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as typeof activeTab)}
                    disabled={!tab.available}
                    className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      activeTab === tab.key
                        ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-600 dark:text-white'
                        : 'text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Summary Content */}
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg min-h-[120px]">
                {activeTab === 'short' && recording.summary_short && (
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {recording.summary_short}
                  </p>
                )}
                {activeTab === 'medium' && recording.summary_medium && (
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {recording.summary_medium}
                  </p>
                )}
                {activeTab === 'detailed' && recording.summary_detailed && (
                  <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {recording.summary_detailed}
                  </div>
                )}
                {!recording[`summary_${activeTab}` as keyof RecordingType] && (
                  <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">
                      {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} summary not available
                    </p>
                    <button
                      onClick={handleTranscribe}
                      disabled={transcribing}
                      className="mt-2 inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 dark:text-blue-400 text-sm"
                    >
                      <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                      Generate Summary
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* No transcription yet */}
          {!recording.transcription && recording.status === 'recorded' && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
              <FileAudio className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No transcription yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Start transcription to generate text and AI summaries
              </p>
              <button
                onClick={handleTranscribe}
                disabled={transcribing}
                className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <RefreshCw className={`w-5 h-5 ${transcribing ? 'animate-spin' : ''}`} />
                {transcribing ? 'Starting Transcription...' : 'Start Transcription'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
