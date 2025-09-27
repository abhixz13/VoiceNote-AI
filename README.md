# VoiceNote AI

An AI-powered voice note recording and transcription application built with React, Cloudflare Workers, and modern web technologies.

## Project Structure

```
VoiceNote-AI/
├── frontend/          # React UI Application
├── backend/           # Cloudflare Workers API
├── utils/             # Shared utilities and types
└── docs/              # Documentation
```

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Cloudflare account (for backend deployment)

### Installation

1. **Install all dependencies:**
   ```bash
   npm run install:all
   ```

2. **Start development servers:**
   ```bash
   # Start frontend (React app)
   npm run dev:frontend
   
   # Start backend (Cloudflare Workers)
   npm run dev:backend
   ```

### Individual Development

**Frontend Development:**
```bash
cd frontend
npm install
npm run dev
```

**Backend Development:**
```bash
cd backend
npm install
npm run dev
```

**Utils Development:**
```bash
cd utils
npm install
npm run build
```

## Features

- 🎙️ **Voice Recording**: High-quality audio recording with real-time waveform display
- 🤖 **AI Transcription**: Automatic speech-to-text conversion
- 📝 **Smart Summaries**: AI-generated summaries at different detail levels
- 💾 **Cloud Storage**: Secure file storage with Cloudflare R2
- 🚀 **Fast Performance**: Built with modern web technologies

## Technology Stack

### Frontend
- React 19 with TypeScript
- Vite for fast development and building
- Tailwind CSS for styling
- React Router for navigation
- Lucide React for icons

### Backend
- Cloudflare Workers for serverless API
- Hono framework for routing
- D1 Database for data persistence
- R2 Storage for file management
- Zod for schema validation

### Shared
- TypeScript for type safety
- Zod for runtime validation
- Common utilities and types

## Deployment

### Frontend Deployment
The frontend can be deployed to any static hosting service:
- Vercel
- Netlify
- Cloudflare Pages

### Backend Deployment
```bash
cd backend
npm run deploy
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.