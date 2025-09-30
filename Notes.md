# Frontend / UI Stack

| Tool / Technology       | Role / Purpose                                                                                                                                                             |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| React                   | Core frontend framework. Handles UI components, state management, and rendering. All recording buttons, waveform, timer, and placeholders are React components.          |
| TypeScript              | Superset of JavaScript that adds static typing. Ensures fewer bugs, better IDE support, and more maintainable code. Used throughout frontend.                            |
| Mocha (visual IDE)      | AI-assisted frontend code generator. Generated initial React/TS components and page structure.                                                                             |
| CSS / Styled Components | Handles layout, spacing, responsive design.                                                                                                                                |
| Vercel / Netlify        | Hosting / deployment platform. Frontend is deployed for testing and demonstration. Free tier sufficient for Phase 1.                                                     |

---

# Development Workflow & Version Control

## Branching Strategy
- **`main` branch**: Represents the stable, production-ready version of the application.
- **Feature branches**: Developers create these from `main` (or a `development` branch if used) to work on individual features or bug fixes in isolation.

## Alignment to Avoid Version Mismatches
- **Merging & Pull Requests (PRs)**: Changes from feature branches are integrated into `main` via PRs, which include code reviews and automated checks.
- **Continuous Integration (CI)**: Automated builds and tests run on every code push/PR to catch issues early.
- **Continuous Deployment (CD)**: Automated deployment to environments (e.g., Vercel for frontend) upon merging into `main`.
- **Dependency Locking**: `package-lock.json` ensures consistent dependency versions across all environments and development setups.

---

# AI/ML Backend Stack

| Tool / Technology       | Role / Purpose                                                                                                                                                             |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FastAPI (Python)        | Core backend framework for AI services. Handles transcription and summarization API endpoints. Deployed on Railway.                                                       |
| OpenAI Whisper         | Speech-to-text model for transcribing audio recordings. Converts .webm audio files to text.                                                                               |
| OpenAI GPT-4           | Large language model for generating summaries. Creates executive summaries, key points, and detailed summaries from transcriptions.                                      |
| Text Preprocessing Agent| Single function that handles cleaning, normalization, and semantic chunking of Whisper transcriptions. Prepares text for optimal summarization by GPT-4.                 |
| Supabase (Python client)| Database and storage access. Stores recording metadata, file paths, transcriptions, and generated summaries. Uses service role key for backend operations.               |
| Railway                | Hosting platform for Python backend services. Provides automatic deployments from Git and environment variable management.                                                |