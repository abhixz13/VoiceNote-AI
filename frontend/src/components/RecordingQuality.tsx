import { Mic } from 'lucide-react';

interface RecordingQualityProps {
  sampleRate: number;
  bitRate: string;
  channels: number;
  isRecording: boolean;
  className?: string;
}

export default function RecordingQuality({
  sampleRate,
  bitRate,
  channels,
  isRecording,
  className = ""
}: RecordingQualityProps) {
  
  const formatSampleRate = (rate: number): string => {
    if (rate >= 1000) {
      return `${(rate / 1000).toFixed(1)}kHz`;
    }
    return `${rate}Hz`;
  };

  const getChannelLabel = (channelCount: number): string => {
    return channelCount === 1 ? 'Mono' : channelCount === 2 ? 'Stereo' : `${channelCount}ch`;
  };

  const getQualityLevel = (sampleRate: number): string => {
    if (sampleRate >= 48000) return 'High';
    if (sampleRate >= 44100) return 'Good';
    if (sampleRate >= 22050) return 'Standard';
    return 'Low';
  };

  const getQualityColor = (sampleRate: number): string => {
    if (sampleRate >= 48000) return 'text-green-600';
    if (sampleRate >= 44100) return 'text-blue-600';
    if (sampleRate >= 22050) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      {/* Audio Quality Info */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <Mic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        <div className="text-sm">
          <span className={`font-medium ${getQualityColor(sampleRate)}`}>
            {getQualityLevel(sampleRate)} Quality
          </span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">
            {formatSampleRate(sampleRate)} • {bitRate} • {getChannelLabel(channels)}
          </span>
        </div>
      </div>

      {/* Recording Status Indicator */}
      {isRecording && (
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium text-red-600">
            Recording
          </span>
        </div>
      )}
    </div>
  );
}
