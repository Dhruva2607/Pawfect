# PawFect — AI Pet Matchmaker

PawFect is a Kotlin/Jetpack Compose Android client and a FastAPI backend. The backend serves the pet catalog, profile and saved-pet operations, compatibility evaluations, adoption applications, and an AI-guided chat experience. MongoDB stores application data; Google Gemini powers chat, embeddings, and AI compatibility evaluations.

For a reproducible environment setup and a hands-on verification checklist, see [Implementation Handoff](IMPLEMENTATION_HANDOFF.md).

## Project layout

```text
Pawfect/
├── android/                 # Android Studio project (Kotlin, Jetpack Compose)
│   ├── app/src/main/        # App, API/data layers, screens, resources
│   ├── app/src/test/        # JVM unit tests
│   └── gradlew[.bat]        # Gradle wrapper
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── database/        # MongoDB connection and index setup
│   │   ├── models/          # Pydantic data models
│   │   ├── routers/         # REST and SSE endpoints
│   │   ├── scripts/         # Pet catalog seeding script
│   │   └── services/        # Gemini, LangGraph, retrieval
│   ├── tests/               # Backend pytest tests
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── .gitignore
├── README.md
└── IMPLEMENTATION_HANDOFF.md
```

## Requirements

- Python 3.10 or later (3.12 recommended).
- MongoDB reachable by the backend. MongoDB Atlas with Vector Search is required for vector-based recommendations; a local MongoDB instance can be used for basic database-backed API checks.
- A Google Gemini API key for chat, embedding generation, and AI evaluations.
- Android Studio, JDK 17, and Android SDK Platform 35 to build and run the Android app.
- Git.

The Android project uses Gradle 9.8.2 (via its checked-in wrapper), Android Gradle Plugin 8.7.2, Kotlin 2.0.21, `minSdk 26`, and Java/Kotlin JVM target 17.

## Configure the backend

From the repository root, create a private backend environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` and set:

```dotenv
GOOGLE_API_KEY=your-google-ai-studio-api-key
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-host>/?retryWrites=true&w=majority
DATABASE_NAME=pawfect
ALLOWED_ORIGINS=*
```

These are the only environment variables read by the backend configuration in `backend/app/config.py`. `GOOGLE_API_KEY` defaults to an empty string, `MONGODB_URI` defaults to `mongodb://localhost:27017`, `DATABASE_NAME` defaults to `pawfect`, and `ALLOWED_ORIGINS` defaults to `*` (all origins; set a comma-separated list to restrict CORS). A valid Gemini key and a reachable MongoDB are needed for full functionality. `HOST`, `PORT`, and `DEBUG` are not read from `.env`; choose the bind address and port in the Uvicorn command.

For MongoDB Atlas, create a database user and allow the backend host's IP address in Network Access. Do not expose a database to all IP addresses except as a temporary, deliberate development choice. URL-encode special characters in the MongoDB username/password when constructing the connection URI.

### Optional Atlas Vector Search setup

At startup the backend attempts to create or verify the `vector_index` on the `pets` collection. If your Atlas deployment requires manual creation, use Atlas Search / Vector Search and the following definition:

```json
{
  "fields": [
    { "type": "vector", "path": "embedding", "numDimensions": 768, "similarity": "cosine" },
    { "type": "filter", "path": "species" },
    { "type": "filter", "path": "good_with_other_pets" },
    { "type": "filter", "path": "good_with_kids" },
    { "type": "filter", "path": "housing_requirement" },
    { "type": "filter", "path": "energy_level" }
  ]
}
```

Use the index name `vector_index`, database name matching `DATABASE_NAME`, and collection `pets`. The seeding script also attempts the index setup.

## Run the backend

Commands below assume PowerShell from the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The first startup checks/creates MongoDB indexes. It logs index setup failures and continues running, but database-backed features will not work until MongoDB is available and configured. Open:

- Liveness: <http://localhost:8000/health/live> — process-only check.
- Readiness: <http://localhost:8000/health> — returns `200` when MongoDB responds to `ping`, otherwise `503`.
- Swagger: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

The backend API prefix is `/api/v1`.

### Seed the pet catalog

With the backend virtual environment active and the correct `.env` in `backend/`:

```powershell
python -m app.scripts.seed_pets
```

The script seeds 36 defined pet records and creates 768-dimensional Gemini embeddings for records that need them. It reuses existing valid embeddings and skips the seed when the existing catalog already contains at least the seed record count. Initial embedding generation may take time and use Gemini API quota.

## Run the Android app

1. Start the backend and confirm `http://localhost:8000/health` reports `"status": "healthy"`.
2. Open the `android/` directory in Android Studio and allow Gradle sync to finish.
3. Use an Android emulator or a physical Android device.
4. The default API base URL is `http://10.0.2.2:8000/api/v1/`, which routes from the standard Android emulator to the host computer's port 8000.

To run from PowerShell with a different backend URL:

```powershell
cd android
.\gradlew.bat :app:installDebug -PPAWFECT_API_BASE_URL=http://192.168.1.25:8000/api/v1/
```

Replace the example address with the host's LAN IP when using a physical device; the phone and computer must be able to reach each other. Keep the trailing slash. Debug builds allow HTTP cleartext; release builds do not, so use HTTPS for release. The API URL is a Gradle project property, not an Android runtime environment variable. It can also be stored in `android/gradle.properties` for local development; do not commit machine-specific URLs.

Build a debug APK:

```powershell
cd android
.\gradlew.bat :app:assembleDebug
```

The APK is written to `android/app/build/outputs/apk/debug/app-debug.apk`. Release builds are unsigned unless signing is configured:

```powershell
.\gradlew.bat :app:assembleRelease
```

## Android app capabilities

The app includes welcome/onboarding and authentication screens, a pet catalog, AI chat, match and saved-pet views, pet details, compatibility evaluation, adoption application/status, and profile/preferences. It uses Retrofit/JSON for REST requests, OkHttp SSE for streaming chat, Hilt for dependency injection, and local persisted session/chat state.

The app uses live API responses; it does not bundle a fallback pet catalog. Chat history is stored locally in the app as well as being saved by the backend; the backend currently has no chat-history retrieval endpoint.

## Backend API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health/live` | Liveness check |
| `GET` | `/health` | MongoDB readiness check |
| `GET` | `/api/v1/pets` | List pets; optional `species`, `size`, `good_with_kids`, `limit` filters |
| `GET` | `/api/v1/pets/{id}` | Pet details |
| `POST` | `/api/v1/chat/message` | JSON response or SSE stream (`stream: true`) |
| `POST` | `/api/v1/matches/direct-eval` | Evaluate one pet against lifestyle preferences |
| `POST` | `/api/v1/users/auth/signup` | Create/update a user profile |
| `POST` | `/api/v1/users/auth/login` | Demo-style login/profile lookup |
| `GET` / `PUT` | `/api/v1/users/{id}/profile` | Read/update a profile |
| `POST` | `/api/v1/users/{id}/favorite/{petId}` | Toggle a saved pet |
| `GET` | `/api/v1/users/{id}/saved-pets` | List saved pets |
| `POST` | `/api/v1/adoptions/apply` | Submit an adoption application |
| `GET` | `/api/v1/adoptions/{id}/status` | Read application status |

Interactive request/response schemas are available at `/docs`. The current authentication implementation is not production authentication: passwords are not validated, login can create a profile, and the returned token is synthetic. Do not use it to protect real user data without implementing proper authentication and authorization.

## Verification commands

Backend tests (from `backend/`, with dev requirements installed):

```powershell
pytest -q
```

Android unit tests, builds, and lint (from `android/`, with JDK 17 selected):

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug :app:assembleRelease :app:lintDebug
```

These automated tests do not replace a live integration test. For a step-by-step backend and app smoke test, including expected results and limitations, see [Implementation Handoff](IMPLEMENTATION_HANDOFF.md).
