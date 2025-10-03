import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Play, Trash2, Clock, FileAudio, ChevronLeft, ChevronRight, Plus, Download, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { RecordingType } from '../types';
import { supabase, STORAGE_BUCKET } from '../lib/supabaseClient';

export default function Recordings() {
  const navigate = useNavigate();
  const [recordings, setRecordings] = useState<RecordingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [expandedRecordings, setExpandedRecordings] = useState<Set<string>>(new Set());
  const [activeSummaryTab, setActiveSummaryTab] = useState<{[key: string]: 'transcript' | 'executive' | 'keypoints' | 'detailed'}>({});
  const [summaryData, setSummaryData] = useState<{[key: string]: any}>({});

  const limit = 10;
  const RAILWAY_BACKEND_URL = 'https://voicenote-ai-backend.up.railway.app';

  const fetchRecordings = async (page: number) => {
    setLoading(true);
    setError(null);
    
    try {
      // Calculate offset for pagination
      const offset = (page - 1) * limit;
      
      // Fetch recordings directly from Supabase
      const { data: recordingsData, error: recordingsError, count } = await supabase
        .from('recordings')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      if (recordingsError) {
        throw new Error(`Failed to fetch recordings: ${recordingsError.message}`);
      }

      // Calculate pagination info
      const total = count || 0;
      const totalPages = Math.ceil(total / limit);
      
      setRecordings(recordingsData || []);
      setCurrentPage(page);
      setTotalPages(totalPages);
      setTotal(total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recordings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings(currentPage);
  }, [currentPage]);

  const handleDelete = async (recording: RecordingType) => {
    if (!confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    setDeleting(recording.recording_id);
    try {
      // Use the backend API for proper cascading delete
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recording.recording_id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete recording' }));
        throw new Error(errorData.detail || 'Failed to delete recording');
      }

      const result = await response.json();
      
      // Show success message
      setSuccessMessage(`Successfully deleted recording: ${recording.title}`);
      
      // Log any storage warnings
      if (result.storage_warnings && result.storage_warnings.length > 0) {
        console.warn('Storage cleanup warnings:', result.storage_warnings);
      }

      // Refresh the current page
      await fetchRecordings(currentPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete recording');
    } finally {
      setDeleting(null);
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
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleSummarize = async (recording: RecordingType) => {
    setSummarizing(recording.recording_id);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recording.recording_id}/summarize`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to generate summary' }));
        throw new Error(errorData.detail || 'Failed to generate summary');
      }

      const result = await response.json();
      
      // Handle different response types
      if (result.already_existed) {
        setSuccessMessage('Summaries already exist for this recording.');
      } else {
        setSuccessMessage('Summary generation completed successfully!');
      }
      
      // Refresh recordings to get updated status and content
      await fetchRecordings(currentPage);
      
      // Fetch the summary data
      await fetchSummaryData(recording.recording_id);
      
      // Auto-expand the recording to show the summary
      const newExpanded = new Set(expandedRecordings);
      newExpanded.add(recording.recording_id);
      setExpandedRecordings(newExpanded);
      
      // Set default tab to transcript
      setActiveSummaryTab(prev => ({ ...prev, [recording.recording_id]: 'transcript' }));
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary');
    } finally {
      setSummarizing(null);
    }
  };

  const handleDownload = async (recording: RecordingType) => {
    if (!recording.file_path) {
      alert('No audio file available for download');
      return;
    }

    try {
      // Get signed URL for download
      const { data, error } = await supabase.storage
        .from(STORAGE_BUCKET)
        .createSignedUrl(recording.file_path, 60); // 60 seconds expiry

      if (error) {
        throw new Error(`Failed to get download URL: ${error.message}`);
      }

      // Download the file
      const response = await fetch(data.signedUrl);
      if (!response.ok) {
        throw new Error('Failed to download audio file');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${recording.title}.webm`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading audio:', error);
      alert(`Error downloading audio: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'recorded':
        return 'Recorded';
      case 'processing':
        return 'Processing';
      case 'transcribed':
        return 'Transcribed';
      case 'error':
        return 'Error';
      default:
        return status;
    }
  };

  const toggleRecordingExpansion = async (recordingId: string) => {
    const newExpanded = new Set(expandedRecordings);
    if (newExpanded.has(recordingId)) {
      newExpanded.delete(recordingId);
    } else {
      newExpanded.add(recordingId);
      // Set default tab to transcript if not already set
      if (!activeSummaryTab[recordingId]) {
        setActiveSummaryTab(prev => ({ ...prev, [recordingId]: 'transcript' }));
      }
      // Fetch summary data if we don't have it yet
      if (!summaryData[recordingId]) {
        await fetchSummaryData(recordingId);
      }
    }
    setExpandedRecordings(newExpanded);
  };

  const setSummaryTab = (recordingId: string, tab: 'transcript' | 'executive' | 'keypoints' | 'detailed') => {
    setActiveSummaryTab(prev => ({ ...prev, [recordingId]: tab }));
  };

  const fetchSummaryData = async (recordingId: string) => {
    try {
      const response = await fetch(`${RAILWAY_BACKEND_URL}/api/recordings/${recordingId}/summary`);
      if (response.ok) {
        const data = await response.json();
        setSummaryData(prev => ({ ...prev, [recordingId]: data.unified_summary }));
        return data.unified_summary;
      }
    } catch (err) {
      console.warn('Failed to fetch summary data:', err);
    }
    return null;
  };

  const hasSummaryContent = (recording: RecordingType) => {
    // Check if we have summary data from storage or transcription in recordings table
    const storedSummary = summaryData[recording.recording_id];
    return recording.transcription || 
           (storedSummary && storedSummary.consolidated_summary) ||
           recording.status === 'summarized';
  };

  const getSummaryContent = (recording: RecordingType, type: 'transcript' | 'executive' | 'keypoints' | 'detailed') => {
    const storedSummary = summaryData[recording.recording_id];
    
    switch (type) {
      case 'transcript':
        return recording.transcription;
      case 'executive':
        return storedSummary?.consolidated_summary?.executive_summary || recording.summary_short;
      case 'keypoints':
        return storedSummary?.consolidated_summary?.key_points || recording.summary_medium;
      case 'detailed':
        return storedSummary?.consolidated_summary?.detailed_summary || recording.summary_detailed;
      default:
        return null;
    }
  };

  if (loading && recordings.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading recordings...</p>
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            My Recordings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {total} recording{total !== 1 ? 's' : ''} total
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Success Display */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-700">{successMessage}</p>
          </div>
        )}

        <div className="max-w-4xl mx-auto">
          {recordings.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-12 text-center">
              <FileAudio className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No recordings yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Start by creating your first voice recording
              </p>
              <button
                onClick={() => navigate('/record')}
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Recording
              </button>
            </div>
          ) : (
            <>
              {/* Recordings List */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {recordings.map((recording) => {
                    const isExpanded = expandedRecordings.has(recording.recording_id);
                    const currentTab = activeSummaryTab[recording.recording_id] || 'transcript';
                    const hasContent = hasSummaryContent(recording);
                    
                    return (
                      <div key={recording.recording_id} className="border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                        <div className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                                  {recording.title}
                                </h3>
                                <span className={getStatusBadge(recording.status)}>
                                  {getStatusText(recording.status)}
                                </span>
                              </div>
                              
                              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
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

                              {recording.summary_short && !isExpanded && (
                                <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                                  {recording.summary_short}
                                </p>
                              )}
                            </div>

                            <div className="flex items-center gap-2 ml-4">
                              <button
                                onClick={() => navigate(`/recordings/${recording.recording_id}`)}
                                className="inline-flex items-center gap-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors dark:bg-blue-900 dark:hover:bg-blue-800 dark:text-blue-300"
                              >
                                <Play className="w-4 h-4" />
                                View
                              </button>
                              
                              {hasContent && (
                                <button
                                  onClick={() => toggleRecordingExpansion(recording.recording_id)}
                                  className="inline-flex items-center gap-1 bg-green-100 hover:bg-green-200 text-green-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors dark:bg-green-900 dark:hover:bg-green-800 dark:text-green-300"
                                >
                                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                  {isExpanded ? 'Hide' : 'Show'} Summary
                                </button>
                              )}
                              
                              {!hasContent && (
                                <button
                                  onClick={() => handleSummarize(recording)}
                                  disabled={summarizing === recording.recording_id}
                                  className="inline-flex items-center gap-1 bg-purple-100 hover:bg-purple-200 text-purple-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-purple-900 dark:hover:bg-purple-800 dark:text-purple-300"
                                >
                                  <Sparkles className="w-4 h-4" />
                                  {summarizing === recording.recording_id ? 'Processing...' : 'Summarize'}
                                </button>
                              )}
                              
                              {recording.file_path && (
                                <button
                                  onClick={() => handleDownload(recording)}
                                  className="inline-flex items-center gap-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300"
                                >
                                  <Download className="w-4 h-4" />
                                  Download
                                </button>
                              )}
                              
                              <button
                                onClick={() => handleDelete(recording)}
                                disabled={deleting === recording.recording_id}
                                className="inline-flex items-center gap-1 bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-red-900 dark:hover:bg-red-800 dark:text-red-300"
                              >
                                <Trash2 className="w-4 h-4" />
                                {deleting === recording.recording_id ? 'Deleting...' : 'Delete'}
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Expandable Summary Section */}
                        {isExpanded && hasContent && (
                          <div className="px-6 pb-6 bg-gray-50 dark:bg-gray-800">
                            {/* Tab Navigation */}
                            <div className="border-b border-gray-200 dark:border-gray-600 mb-4">
                              <nav className="flex space-x-8">
                                {[
                                  { key: 'transcript', label: 'Transcript', available: !!getSummaryContent(recording, 'transcript') },
                                  { key: 'executive', label: 'Executive Summary', available: !!getSummaryContent(recording, 'executive') },
                                  { key: 'keypoints', label: 'Key Points', available: !!getSummaryContent(recording, 'keypoints') },
                                  { key: 'detailed', label: 'Detailed Summary', available: !!getSummaryContent(recording, 'detailed') },
                                ].map((tab) => (
                                  <button
                                    key={tab.key}
                                    onClick={() => setSummaryTab(recording.recording_id, tab.key as any)}
                                    disabled={!tab.available}
                                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                                      currentTab === tab.key && tab.available
                                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                                    }`}
                                  >
                                    {tab.label}
                                  </button>
                                ))}
                              </nav>
                            </div>

                            {/* Tab Content */}
                            <div className="bg-white dark:bg-gray-700 rounded-lg p-4">
                              {currentTab === 'transcript' && getSummaryContent(recording, 'transcript') && (
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Transcription</h4>
                                  <div className="prose prose-sm max-w-none">
                                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                      {getSummaryContent(recording, 'transcript')}
                                    </p>
                                  </div>
                                </div>
                              )}

                              {currentTab === 'executive' && getSummaryContent(recording, 'executive') && (
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Executive Summary</h4>
                                  <div className="prose prose-sm max-w-none">
                                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                                      {getSummaryContent(recording, 'executive')}
                                    </p>
                                  </div>
                                </div>
                              )}

                              {currentTab === 'keypoints' && getSummaryContent(recording, 'keypoints') && (
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Key Points</h4>
                                  <div className="prose prose-sm max-w-none">
                                    <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                      {getSummaryContent(recording, 'keypoints')}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {currentTab === 'detailed' && getSummaryContent(recording, 'detailed') && (
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Detailed Summary</h4>
                                  <div className="prose prose-sm max-w-none">
                                    <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                      {getSummaryContent(recording, 'detailed')}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Show message if no content for current tab */}
                              {((currentTab === 'transcript' && !getSummaryContent(recording, 'transcript')) ||
                                (currentTab === 'executive' && !getSummaryContent(recording, 'executive')) ||
                                (currentTab === 'keypoints' && !getSummaryContent(recording, 'keypoints')) ||
                                (currentTab === 'detailed' && !getSummaryContent(recording, 'detailed'))) && (
                                <div className="text-center py-8">
                                  <p className="text-gray-500 dark:text-gray-400 mb-4">
                                    This content is not available yet.
                                  </p>
                                  <button
                                    onClick={() => handleSummarize(recording)}
                                    disabled={summarizing === recording.recording_id}
                                    className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                                  >
                                    <Sparkles className="w-4 h-4" />
                                    {summarizing === recording.recording_id ? 'Processing...' : 'Generate Summary'}
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Showing {((currentPage - 1) * limit) + 1} to {Math.min(currentPage * limit, total)} of {total} recordings
                  </p>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1 || loading}
                      className="inline-flex items-center gap-1 bg-white hover:bg-gray-50 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </button>
                    
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Page {currentPage} of {totalPages}
                    </span>
                    
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages || loading}
                      className="inline-flex items-center gap-1 bg-white hover:bg-gray-50 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
