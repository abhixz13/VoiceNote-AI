import { useEffect, useRef } from 'react';

interface WaveformDisplayProps {
  amplitudeData: number[];
  isRecording: boolean;
  isPaused: boolean;
  className?: string;
}

export default function WaveformDisplay({ 
  amplitudeData, 
  isRecording, 
  isPaused, 
  className = "" 
}: WaveformDisplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Set styles
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    if (isRecording && !isPaused) {
      gradient.addColorStop(0, 'rgba(34, 197, 94, 0.8)'); // green-500
      gradient.addColorStop(1, 'rgba(34, 197, 94, 0.2)');
    } else if (isPaused) {
      gradient.addColorStop(0, 'rgba(251, 191, 36, 0.8)'); // amber-400
      gradient.addColorStop(1, 'rgba(251, 191, 36, 0.2)');
    } else {
      gradient.addColorStop(0, 'rgba(156, 163, 175, 0.8)'); // gray-400
      gradient.addColorStop(1, 'rgba(156, 163, 175, 0.2)');
    }
    
    ctx.fillStyle = gradient;
    ctx.strokeStyle = isRecording && !isPaused ? '#22c55e' : isPaused ? '#fbbf24' : '#9ca3af';
    ctx.lineWidth = 2;

    if (amplitudeData.length === 0) {
      // Draw baseline when no data
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
      return;
    }

    const barWidth = width / Math.max(amplitudeData.length, 50);
    const maxBarHeight = height * 0.8;

    // Draw amplitude bars
    amplitudeData.forEach((amplitude, index) => {
      const barHeight = Math.max(amplitude * maxBarHeight, 2);
      const x = index * barWidth;
      const y = (height - barHeight) / 2;

      ctx.fillRect(x, y, Math.max(barWidth - 1, 1), barHeight);
    });

    // Draw a glowing effect for active recording
    if (isRecording && !isPaused) {
      ctx.shadowColor = '#22c55e';
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

  }, [amplitudeData, isRecording, isPaused]);

  return (
    <div className={`relative ${className}`}>
      <canvas
        ref={canvasRef}
        width={800}
        height={120}
        className="w-full h-full rounded-lg bg-gray-50 dark:bg-gray-800"
        style={{ imageRendering: 'pixelated' }}
      />
      
      {amplitudeData.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {isRecording ? 'Listening for audio...' : 'Waveform will appear here'}
          </p>
        </div>
      )}
    </div>
  );
}
