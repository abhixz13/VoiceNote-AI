import { useState, useRef, useCallback, useEffect } from 'react';

export interface AudioRecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
  amplitudeData: number[];
  error: string | null;
  audioQuality: {
    sampleRate: number;
    bitRate: string;
    channels: number;
  };
}

export interface AudioRecordingControls {
  startRecording: () => Promise<void>;
  pauseRecording: () => void;
  resumeRecording: () => void;
  stopRecording: () => void;
  clearRecording: () => void;
}

export const useAudioRecording = (): [AudioRecordingState, AudioRecordingControls] => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [amplitudeData, setAmplitudeData] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [audioQuality, setAudioQuality] = useState({
    sampleRate: 44100,
    bitRate: '128 kbps',
    channels: 1,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const durationTimerRef = useRef<NodeJS.Timeout | null>(null);
  const amplitudeTimerRef = useRef<NodeJS.Timeout | null>(null);

  const updateAmplitude = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average amplitude
    const average = dataArray.reduce((acc, value) => acc + value, 0) / bufferLength;
    const normalizedAmplitude = average / 255; // Normalize to 0-1

    setAmplitudeData(prev => {
      const newData = [...prev, normalizedAmplitude];
      // Keep only last 50 amplitude readings for performance (as per Phase 1 requirements)
      return newData.slice(-50);
    });
  }, []);

  const startAmplitudeTracking = useCallback(() => {
    amplitudeTimerRef.current = setInterval(updateAmplitude, 100); // Update every 100ms
  }, [updateAmplitude]);

  const stopAmplitudeTracking = useCallback(() => {
    if (amplitudeTimerRef.current) {
      clearInterval(amplitudeTimerRef.current);
      amplitudeTimerRef.current = null;
    }
  }, []);

  const startDurationTimer = useCallback(() => {
    durationTimerRef.current = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000); // Update every second for accurate duration tracking
  }, []);

  const stopDurationTimer = useCallback(() => {
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      });
      
      streamRef.current = stream;

      // Setup audio context for amplitude tracking
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;

      // Detect audio quality from the stream
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length > 0) {
        const settings = audioTracks[0].getSettings();
        setAudioQuality({
          sampleRate: settings.sampleRate || 44100,
          bitRate: '128 kbps', // WebM Opus default
          channels: settings.channelCount || 1,
        });
      }

      // Setup media recorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        
        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
      };

      // Start recording
      mediaRecorderRef.current.start(1000); // Collect data every 1 second
      setIsRecording(true);
      setIsPaused(false);
      setDuration(0);
      setAmplitudeData([]);
      
      startDurationTimer();
      startAmplitudeTracking();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start recording');
      console.error('Error starting recording:', err);
    }
  }, [startDurationTimer, startAmplitudeTracking]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      stopDurationTimer();
      stopAmplitudeTracking();
    }
  }, [isRecording, isPaused, stopDurationTimer, stopAmplitudeTracking]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      startDurationTimer();
      startAmplitudeTracking();
    }
  }, [isRecording, isPaused, startDurationTimer, startAmplitudeTracking]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      stopDurationTimer();
      stopAmplitudeTracking();
    }
  }, [isRecording, stopDurationTimer, stopAmplitudeTracking]);

  const clearRecording = useCallback(() => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    
    setAudioBlob(null);
    setAudioUrl(null);
    setDuration(0);
    setAmplitudeData([]);
    setError(null);
    setIsRecording(false);
    setIsPaused(false);
    
    stopDurationTimer();
    stopAmplitudeTracking();
  }, [audioUrl, stopDurationTimer, stopAmplitudeTracking]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopDurationTimer();
      stopAmplitudeTracking();
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl, stopDurationTimer, stopAmplitudeTracking]);

  return [
    {
      isRecording,
      isPaused,
      duration,
      audioBlob,
      audioUrl,
      amplitudeData,
      error,
      audioQuality,
    },
    {
      startRecording,
      pauseRecording,
      resumeRecording,
      stopRecording,
      clearRecording,
    },
  ];
};
