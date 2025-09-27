import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Play, Trash2, Clock, FileAudio, ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import { RecordingType, RecordingsListType } from '../types';

export default function Recordings() {
  const navigate = useNavigate();
  const [recordings, setRecordings] = useState<RecordingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleting, setDeleting] = useState<number | null>(null);

  const limit = 10;

  const fetchRecordings = async (page: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/recordings?page=${page}&limit=${limit}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch recordings');
      }

      const data: RecordingsListType = await response.json();
      setRecordings(data.recordings);
      setCurrentPage(data.page);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recordings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings(currentPage);
  }, [currentPage]);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    setDeleting(id);
    try {
      const response = await fetch(`/api/recordings/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete recording');
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
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              My Recordings
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {total} recording{total !== 1 ? 's' : ''} total
            </p>
          </div>
          <button
            onClick={() => navigate('/record')}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Recording
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
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
                  {recordings.map((recording) => (
                    <div
                      key={recording.id}
                      className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
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

                          {recording.summary_short && (
                            <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                              {recording.summary_short}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={() => navigate(`/recordings/${recording.id}`)}
                            className="inline-flex items-center gap-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors dark:bg-blue-900 dark:hover:bg-blue-800 dark:text-blue-300"
                          >
                            <Play className="w-4 h-4" />
                            View
                          </button>
                          
                          <button
                            onClick={() => handleDelete(recording.id)}
                            disabled={deleting === recording.id}
                            className="inline-flex items-center gap-1 bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-red-900 dark:hover:bg-red-800 dark:text-red-300"
                          >
                            <Trash2 className="w-4 h-4" />
                            {deleting === recording.id ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
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
