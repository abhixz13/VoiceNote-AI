import { useState, useEffect, useRef } from 'react';
import { Mic, Volume2, Activity } from 'lucide-react';

interface AudioDiagnosticsProps {
  isRecording: boolean;
  analyserNode: AnalyserNode | null;
}

export default function AudioDiagnostics({ isRecording, analyserNode }: AudioDiagnosticsProps) {
  const [audioLevel, setAudioLevel] = useState(0);
  const [peakLevel, setPeakLevel] = useState(0);
  const [frequencyData, setFrequencyData] = useState<number[]>([]);
  const [rawData, setRawData] = useState<number[]>([]);
  const [isActive, setIsActive] = useState(false);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isRecording || !analyserNode) {
      setAudioLevel(0);
      setPeakLevel(0);
      setFrequencyData([]);
      setRawData([]);
      setIsActive(false);
      return;
    }

    const updateAudioData = () => {
      const bufferLength = analyserNode.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      const timeArray = new Uint8Array(bufferLength);
      
      // Get frequency data
      analyserNode.getByteFrequencyData(dataArray);
      
      // Get time domain data (raw audio)
      analyserNode.getByteTimeDomainData(timeArray);
      
      // Calculate RMS (Root Mean Square) for better audio level detection
      const sumSquares = dataArray.reduce((acc, value) => acc + value * value, 0);
      const rms = Math.sqrt(sumSquares / bufferLength);
      const normalizedLevel = rms / 255;
      
      // Calculate peak level
      const maxValue = Math.max(...dataArray);
      const peakLevel = maxValue / 255;
      
      // Update state
      setAudioLevel(normalizedLevel);
      setPeakLevel(peakLevel);
      setFrequencyData(Array.from(dataArray));
      setRawData(Array.from(timeArray));
      setIsActive(normalizedLevel > 0.001); // Consider active if level > 0.1%
      
      // Log detailed data
      console.log('Audio Diagnostics:', {
        rms: rms.toFixed(2),
        normalizedLevel: normalizedLevel.toFixed(4),
        peakLevel: peakLevel.toFixed(4),
        maxFrequency: Math.max(...dataArray),
        isActive,
        dataArrayLength: dataArray.length
      });
      
      animationRef.current = requestAnimationFrame(updateAudioData);
    };

    updateAudioData();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, analyserNode, isActive]);

  if (!isRecording) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Audio Diagnostics (Start recording to see data)
        </h3>
        <p className="text-xs text-gray-500">Microphone will be monitored when recording starts</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-4">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
        <Activity className="w-4 h-4" />
        Live Audio Diagnostics
      </h3>
      
      {/* Audio Level Display */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Audio Level (RMS)</span>
          <span className="text-xs font-mono">
            {audioLevel.toFixed(4)} ({Math.round(audioLevel * 100)}%)
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-100 ${
              audioLevel > 0.1 ? 'bg-green-500' : 
              audioLevel > 0.05 ? 'bg-yellow-500' : 
              audioLevel > 0.01 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(audioLevel * 1000, 100)}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Peak Level</span>
          <span className="text-xs font-mono">
            {peakLevel.toFixed(4)} ({Math.round(peakLevel * 100)}%)
          </span>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <Mic className={`w-4 h-4 ${isActive ? 'text-green-500' : 'text-gray-400'}`} />
          <span className="text-xs">Mic Active: {isActive ? 'Yes' : 'No'}</span>
        </div>
        <div className="flex items-center gap-1">
          <Volume2 className={`w-4 h-4 ${audioLevel > 0.01 ? 'text-green-500' : 'text-gray-400'}`} />
          <span className="text-xs">Audio Detected: {audioLevel > 0.01 ? 'Yes' : 'No'}</span>
        </div>
      </div>

      {/* Frequency Visualization */}
      <div className="space-y-2">
        <span className="text-xs text-gray-600">Frequency Analysis (Last 32 bins)</span>
        <div className="flex items-end gap-1 h-16 bg-gray-100 dark:bg-gray-800 p-2 rounded">
          {frequencyData.slice(0, 32).map((value, index) => (
            <div
              key={index}
              className="bg-blue-500 rounded-sm flex-1"
              style={{ height: `${(value / 255) * 100}%` }}
            />
          ))}
        </div>
      </div>

      {/* Raw Data Sample */}
      <div className="space-y-2">
        <span className="text-xs text-gray-600">Raw Audio Data (First 10 samples)</span>
        <div className="text-xs font-mono text-gray-500">
          {rawData.slice(0, 10).map((value, index) => (
            <span key={index} className="mr-2">{value}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
