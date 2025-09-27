interface RecordingTimerProps {
  duration: number;
  isRecording: boolean;
  isPaused: boolean;
  className?: string;
}

export default function RecordingTimer({ 
  duration, 
  isRecording, 
  isPaused, 
  className = "" 
}: RecordingTimerProps) {
  
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const centiseconds = Math.floor((seconds % 1) * 100);

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;
    }
  };

  const getStatusColor = () => {
    if (isRecording && !isPaused) return 'text-red-500';
    if (isPaused) return 'text-amber-500';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getStatusText = () => {
    if (isRecording && !isPaused) return 'Recording';
    if (isPaused) return 'Paused';
    return 'Stopped';
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${
          isRecording && !isPaused 
            ? 'bg-red-500 animate-pulse' 
            : isPaused 
              ? 'bg-amber-500' 
              : 'bg-gray-400'
        }`} />
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>
      
      <div className="text-2xl font-mono font-bold text-gray-900 dark:text-gray-100">
        {formatTime(duration)}
      </div>
    </div>
  );
}
