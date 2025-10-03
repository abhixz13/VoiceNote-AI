import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ArrowLeft, Play, Download, RefreshCw, Clock, FileAudio, Loader2 } from 'lucide-react';
import { RecordingType } from '../types';

export default function RecordingDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [recording, setRecording] = useState<RecordingType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'transcript' | 'short' | 'medium' | 'detailed'>('transcript');
  const [transcribing, setTranscribing] = useState(false);
  const [unifiedSummary, setUnifiedSummary] = useState<any>(null);

  // Define your Railway backend URL
  const RAILWAY_BACKEND_URL = 'https://voicenote-ai-backend.up.railway.app';

  const fetchRecording = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${id}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Recording not found');
        }
        throw new Error('Failed to fetch recording');
      }

      const data: RecordingType = await response.json();
      setRecording(data);

      // If recording is summarized, automatically fetch the unified summary
      if (data.status === 'summarized') {
        await fetchUnifiedSummary(data.recording_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recording');
    } finally {
      setLoading(false);
    }
  };

  const fetchUnifiedSummary = async (recordingId: string) => {
    try {
      // Check if there's a summary in the summaries table for this recording
      const summariesResponse = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recordingId}/summary`);
      
      if (summariesResponse.ok) {
        const summaryData = await summariesResponse.json();
        setUnifiedSummary(summaryData);
      }
    } catch (err) {
      console.warn('Failed to fetch unified summary:', err);
      // Don't set error state, just log the warning
    }
  };

  useEffect(() => {
    fetchRecording();
  }, [id]);

  const handleTranscribe = async () => {
    if (!recording) return;

    setTranscribing(true);
    try {
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recording.recording_id}/transcribe`, {
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

  const handleSummarize = async () => {
    if (!recording) return;

    setTranscribing(true); // Reuse the same loading state
    try {
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recording.recording_id}/summarize`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to generate summary');
      }

      const result = await response.json();
      
      // Refresh recording data to get updated status
      await fetchRecording();
      
      // If summaries were generated or already existed, they should now be loaded
      if (result.unified_summary) {
        setUnifiedSummary({
          unified_summary: result.unified_summary,
          summary_id: result.summary_id,
          summary_path: result.summary_path
        });
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary');
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
      case 'summarized':
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

          {/* Tabbed Content: Transcription & Summaries */}
          {(recording.transcription || unifiedSummary) && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              {/* Tab Navigation */}
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex">
                  {[
                    { 
                      key: 'transcript', 
                      label: 'Transcript', 
                      description: 'Full text transcription',
                      available: !!recording.transcription 
                    },
                    { 
                      key: 'short', 
                      label: 'Short', 
                      description: 'Executive summary',
                      available: !!(recording.summary_short || unifiedSummary?.unified_summary?.consolidated_summary?.executive_summary)
                    },
                    { 
                      key: 'medium', 
                      label: 'Medium', 
                      description: 'Balanced detail',
                      available: !!(recording.summary_medium || unifiedSummary?.unified_summary?.consolidated_summary?.key_points)
                    },
                    { 
                      key: 'detailed', 
                      label: 'Detailed', 
                      description: 'Comprehensive analysis',
                      available: !!(recording.summary_detailed || unifiedSummary?.unified_summary?.consolidated_summary?.detailed_summary)
                    },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as typeof activeTab)}
                      disabled={!tab.available}
                      className={`flex-1 px-6 py-4 text-left border-b-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                        activeTab === tab.key
                          ? 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-400'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                      }`}
                    >
                      <div className="font-medium text-sm">
                        {tab.label}
                      </div>
                      {tab.available && (
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {tab.description}
                        </div>
                      )}
                      {!tab.available && (
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          Not available
                        </div>
                      )}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-8">
                {/* Transcript Content */}
                {activeTab === 'transcript' && (
                  <div>
                    {recording.transcription ? (
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                            {recording.transcription}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <FileAudio className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500 dark:text-gray-400 mb-4">
                          Transcription not available
                        </p>
                        <button
                          onClick={handleTranscribe}
                          disabled={transcribing}
                          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                          {transcribing ? 'Generating...' : 'Generate Transcript'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Short Summary Content */}
                {activeTab === 'short' && (
                  <div>
                    {(recording.summary_short || unifiedSummary?.unified_summary?.consolidated_summary?.executive_summary) ? (
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                          Executive Summary
                        </h3>
                        <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                            {recording.summary_short || unifiedSummary?.unified_summary?.consolidated_summary?.executive_summary}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mx-auto mb-4">
                          <RefreshCw className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">
                          Short summary not available
                        </p>
                        <button
                          onClick={handleSummarize}
                          disabled={transcribing}
                          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                          {transcribing ? 'Generating...' : 'Generate Summary'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Medium Summary Content */}
                {activeTab === 'medium' && (
                  <div>
                    {(recording.summary_medium || unifiedSummary?.unified_summary?.consolidated_summary?.key_points) ? (
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                          Key Points
                        </h3>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                          Balanced detail
                        </div>
                        <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                            {recording.summary_medium || unifiedSummary?.unified_summary?.consolidated_summary?.key_points}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-4">
                          <RefreshCw className="w-6 h-6 text-green-600 dark:text-green-400" />
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">
                          Medium summary not available
                        </p>
                        <button
                          onClick={handleSummarize}
                          disabled={transcribing}
                          className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                          {transcribing ? 'Generating...' : 'Generate Summary'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Detailed Summary Content */}
                {activeTab === 'detailed' && (
                  <div>
                    {(recording.summary_detailed || unifiedSummary?.unified_summary?.consolidated_summary?.detailed_summary) ? (
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                          Detailed Summary
                        </h3>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                          Comprehensive analysis
                        </div>
                        <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                            {recording.summary_detailed || unifiedSummary?.unified_summary?.consolidated_summary?.detailed_summary}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center mx-auto mb-4">
                          <RefreshCw className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">
                          Detailed summary not available
                        </p>
                        <button
                          onClick={handleSummarize}
                          disabled={transcribing}
                          className="inline-flex items-center gap-2 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          <RefreshCw className={`w-4 h-4 ${transcribing ? 'animate-spin' : ''}`} />
                          {transcribing ? 'Generating...' : 'Generate Summary'}
                        </button>
                      </div>
                    )}
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
