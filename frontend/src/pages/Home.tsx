import { Mic, FileAudio, Brain, ArrowRight, Play, Zap } from 'lucide-react';
import { useNavigate } from 'react-router';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center shadow-lg">
                <Mic className="w-10 h-10 text-white" />
              </div>
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                <Brain className="w-3 h-3 text-white" />
              </div>
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            VoiceNote AI
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
            Transform your voice into intelligent insights with AI-powered 
            <br className="hidden md:block" />
            transcription and smart summaries
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/record')}
              className="inline-flex items-center gap-3 bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
            >
              <Mic className="w-6 h-6" />
              Start Recording
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => navigate('/recordings')}
              className="inline-flex items-center gap-3 bg-white hover:bg-gray-50 text-gray-900 px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl border border-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-white dark:border-gray-600"
            >
              <FileAudio className="w-6 h-6" />
              View Recordings
            </button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
            Powerful Features
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center mb-6">
                <Mic className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                High-Quality Recording
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Crystal-clear audio capture with real-time waveform visualization, 
                noise reduction, and customizable recording settings.
              </p>
            </div>
            
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-6">
                <FileAudio className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                AI Transcription
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Accurate speech-to-text conversion powered by advanced AI models, 
                supporting multiple languages and accents.
              </p>
            </div>
            
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mb-6">
                <Brain className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Smart Summaries
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                Generate short, medium, and detailed summaries automatically to 
                extract key insights and action items from your recordings.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div className="bg-white dark:bg-gray-800 py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-12">
              How It Works
            </h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Mic className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  1. Record
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Capture high-quality audio with our intuitive recording interface
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  2. Process
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  AI automatically transcribes and analyzes your audio content
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  3. Insights
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Get intelligent summaries and actionable insights instantly
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
            Ready to get started?
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Start recording and experience the power of AI-enhanced voice notes
          </p>
          <button
            onClick={() => navigate('/record')}
            className="inline-flex items-center gap-3 bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
          >
            <Play className="w-6 h-6" />
            Create Your First Recording
          </button>
        </div>
      </div>
    </div>
  );
}
