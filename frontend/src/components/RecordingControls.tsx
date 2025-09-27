import { Mic, Square, Pause, Play, Trash2 } from 'lucide-react';

interface RecordingControlsProps {
  isRecording: boolean;
  isPaused: boolean;
  hasRecording: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onClear: () => void;
  disabled?: boolean;
}

export default function RecordingControls({
  isRecording,
  isPaused,
  hasRecording,
  onStart,
  onPause,
  onResume,
  onStop,
  onClear,
  disabled = false
}: RecordingControlsProps) {
  
  const getRecordingButtonProps = () => {
    if (isRecording && !isPaused) {
      return {
        onClick: onPause,
        icon: Pause,
        label: 'Pause',
        className: 'bg-amber-500 hover:bg-amber-600 text-white animate-pulse'
      };
    } else if (isRecording && isPaused) {
      return {
        onClick: onResume,
        icon: Play,
        label: 'Resume',
        className: 'bg-green-500 hover:bg-green-600 text-white'
      };
    } else {
      return {
        onClick: onStart,
        icon: Mic,
        label: 'Start Recording',
        className: 'bg-red-500 hover:bg-red-600 text-white'
      };
    }
  };

  const recordingButton = getRecordingButtonProps();
  const RecordingIcon = recordingButton.icon;

  return (
    <div className="flex items-center gap-4">
      <button
        onClick={recordingButton.onClick}
        disabled={disabled}
        className={`
          inline-flex items-center justify-center w-16 h-16 rounded-full 
          transition-all duration-200 transform hover:scale-105 focus:outline-none 
          focus:ring-4 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed
          ${recordingButton.className}
        `}
        title={recordingButton.label}
      >
        <RecordingIcon className="w-6 h-6" />
      </button>

      {isRecording && (
        <button
          onClick={onStop}
          disabled={disabled}
          className="
            inline-flex items-center justify-center w-12 h-12 rounded-full 
            bg-gray-600 hover:bg-gray-700 text-white transition-all duration-200 
            transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-gray-300 
            focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed
          "
          title="Stop Recording"
        >
          <Square className="w-5 h-5" />
        </button>
      )}

      {hasRecording && !isRecording && (
        <button
          onClick={onClear}
          disabled={disabled}
          className="
            inline-flex items-center justify-center w-12 h-12 rounded-full 
            bg-red-100 hover:bg-red-200 text-red-600 transition-all duration-200 
            transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-red-300 
            focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed
            dark:bg-red-900 dark:hover:bg-red-800 dark:text-red-400
          "
          title="Clear Recording"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
