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

---

# Recent Backend Fixes (by Gemini 2.5 Flash)

## 1. Supabase Client Initialization Error
1.  **What's the problem**: When initializing the Supabase client, the application encountered a `TypeError: __init__() got an unexpected keyword argument 'proxy'`. This error prevented the backend from establishing a connection to Supabase, rendering all database and storage operations non-functional.
2.  **Root cause of the problem**: A version incompatibility existed between the installed `supabase` client (version 2.3.0) and its underlying `gotrue` and `httpx`/`httpcore` dependencies. The `create_client` function was implicitly attempting to pass a `proxy` argument during client instantiation, but the constructor of the internal HTTP client no longer supported this parameter.
3.  **Finding**: Despite attempts to clear proxy-related environment variables, the error persisted, suggesting an internal conflict within the library versions. Efforts to upgrade the `supabase` package failed due to SSL certificate verification issues during `pip` installation.
4.  **Solution/Fix**: The `supabase` client was downgraded to a known compatible version (`2.0.3`) using `pip install supabase==2.0.3 --force-reinstall --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org`. This action correctly aligned `supabase` with compatible versions of `gotrue`, `httpx`, and `httpcore`, resolving the `TypeError`.
5.  **Learning**: Strict dependency management and version pinning are crucial in Python projects, especially for libraries with complex underlying HTTP client interactions. `TypeError` related to `__init__` arguments often indicates an API change between versions, necessitating careful version selection.

## 2. Transcription Table Metadata Not Updated (null value for transcription_id)
1.  **What's the problem**: Although audio transcription and storage to the Supabase bucket were successful, no corresponding metadata records were being created or updated in the `transcription` table. The error encountered was `null value in column "transcription_id" of relation "transcription" violates not-null constraint`.
2.  **Root cause of the problem**: The `transcription_id` column in the Supabase `transcription` table was defined as `NOT NULL` but was not configured to auto-generate a UUID by default. Consequently, the application's `INSERT` statements, which did not explicitly provide a value for `transcription_id`, failed due to this constraint violation.
3.  **Finding**: The database schema for the `transcription` table was missing the `DEFAULT gen_random_uuid()` clause for the `transcription_id` column. The Python client, with the older `supabase` version, did not automatically handle UUID generation for this field during insertion.
4.  **Solution/Fix**: Modified the `backend/transcription_service.py` file to explicitly generate a UUID for `transcription_id` using `import uuid; transcription_id = str(uuid.uuid4())` and include this generated UUID in the `insert_data` dictionary before sending it to Supabase. This ensured that the `NOT NULL` constraint was always satisfied. A one-off script (`backend/fix_transcription_schema.py`) was used to insert the missing record for the test case and update the recording status.
5.  **Learning**: Database schema design must align with application logic and ORM/client capabilities. For primary keys intended to be UUIDs, configuring `DEFAULT gen_random_uuid()` in the database schema is best practice. If application-side generation is chosen, it must be explicitly implemented for all inserts.

## 3. Incorrect Transcription Path in Supabase Metadata
1.  **What's the problem**: The `transcription_path` stored in the Supabase `transcription` table was incomplete, showing only the object path within the bucket (e.g., `dd177ad1-.../transcription.txt`) instead of the full reference including the storage bucket name (e.g., `Transcription/dd177ad1-.../transcription.txt`).
2.  **Root cause of the problem**: The application code was constructing the `transcription_path` for database storage using only the `transcription_object_path` (the path *within* the "Transcription" bucket) and was not prepending the actual bucket name to this path.
3.  **Finding**: While the file was correctly uploaded to the "Transcription" storage bucket, the corresponding database entry contained an ambiguous path, which could lead to issues when attempting to retrieve the file using the stored path.
4.  **Solution/Fix**: Modified `backend/transcription_service.py` to create a `transcription_full_path` variable by explicitly prepending the bucket name (`"Transcription/"`) to the `transcription_object_path`. This `transcription_full_path` was then used when inserting the record into the `transcription` table. A one-off script (`backend/fix_transcription_path.py`) was also created and run to update the existing erroneous record in the database.
5.  **Learning**: For consistent and unambiguous file referencing, especially when dealing with multiple storage buckets, ensure that database fields storing file locations contain full, absolute paths or sufficiently detailed relative paths that include the bucket context. This improves clarity and simplifies retrieval logic.

---

# Setting Up Integration Tests (Calling Real Services)

## Purpose
Integration tests verify that different modules or services in your application work together as expected. Unlike unit tests, they interact with **real external dependencies** (databases, APIs, storage services) to ensure the entire system flow is correct.

## Key Differences from Unit Tests
-   **No Mocking**: External services (like Supabase, OpenAI) are *not* mocked. The test makes actual API calls and interacts with real resources.
-   **Environment Dependence**: Requires a correctly configured environment (e.g., `.env` file with actual API keys and URLs).
-   **Resource State**: Tests often rely on a specific state of external resources (e.g., a recording existing in the database and storage).
-   **Slower Execution**: Due to real network calls and I/O operations.
-   **Potential for Side Effects**: May create/modify/delete real data, necessitating careful cleanup strategies.

## Setup Requirements
1.  **Environment Variables**: Ensure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, etc., are correctly loaded (e.g., from a `.env` file in the project root or backend directory). The integration test script (`backend/test_transcription_integration.py`) explicitly loads these using `python-dotenv`.
2.  **Database and Storage Data**: The test assumes the existence of specific data (e.g., a `recording_id` in the `recordings` table with an associated audio file in Supabase Storage).
3.  **Python Path**: The project root (or appropriate parent directory) must be added to `sys.path` to allow absolute imports of application modules (e.g., `from backend.transcription_service import TranscriptionService`).

## Example Structure (referencing `backend/test_transcription_integration.py`)

An effective integration test for the transcription service typically includes:

1.  **Environment Setup**: Loading `.env` variables.
2.  **Service Initialization**: Creating instances of the real services (e.g., `TranscriptionService()`).
3.  **Pre-test Checks**: Optionally verifying connectivity to external services (Supabase, OpenAI) before running the main test logic.
4.  **Execution of Core Logic**: Calling the actual method being tested (e.g., `await service.transcribe_recording(recording_id)`).
5.  **Assertions**: Verifying the outcomes by checking real database entries, storage contents, or API responses. For instance, querying the `transcription` table and `Transcription` storage bucket to confirm metadata and file creation.
6.  **Cleanup (Optional but Recommended)**: Deleting any data created during the test to maintain a clean test environment (e.g., deleting transcription records from the database and files from storage).

## Key Learnings from Debugging
-   **Early Environment Variable Check**: Always verify that critical environment variables are set before proceeding, providing clear error messages if they are missing.
-   **Step-by-Step Verification**: When issues arise, break down the integration flow into smaller, verifiable steps (e.g., test Supabase connection, then OpenAI connection, then full service). This helps pinpoint the exact failure point.
-   **Error Parsing**: Carefully examine error messages from external services or clients (like `TypeError: __init__() got an unexpected keyword argument 'proxy'` or SQL constraint violations) to understand the underlying compatibility or schema issues.
-   **Dependency Versioning**: Be mindful of the versions of all integrated libraries. Incompatible versions can lead to subtle and hard-to-diagnose runtime errors (as seen with the Supabase client and its HTTP dependencies).
-   **Database Schema Alignment**: Ensure your application's data insertion logic perfectly matches the database schema constraints (e.g., explicitly providing UUIDs if the column is not auto-generating).