# PawFect Implementation Handoff

This handoff is for configuring a local development environment and checking that the current PawFect backend and Android app work together. It documents the current repository implementation; it is not a production deployment/security guide.

## 1. What you need

- Git.
- Python 3.10+ (Python 3.12 recommended).
- MongoDB Atlas with Vector Search, or a reachable local MongoDB for limited database-backed checks.
- A Google Gemini API key with access to chat and embedding models.
- Android Studio, JDK 17, Android SDK Platform 35, and an Android emulator or Android 8.0+ device (API 26+).
- Network access to install the pinned Python and Gradle dependencies.

The Android project includes Gradle wrapper scripts, so a separate system Gradle installation is not needed. Android Studio can use its bundled JDK; otherwise set `JAVA_HOME` to JDK 17 before running Gradle.

## 2. Configure secrets and services

### Backend environment file

From the repository root in PowerShell:

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Set the four values the backend actually reads:

```dotenv
GOOGLE_API_KEY=your-google-ai-studio-api-key
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-host>/?retryWrites=true&w=majority
DATABASE_NAME=pawfect
ALLOWED_ORIGINS=*
```

| Variable | Required for | Current code behavior |
|---|---|---|
| `GOOGLE_API_KEY` | AI chat, embeddings, AI evaluations | Defaults to an empty string; provide a valid key for AI features. |
| `MONGODB_URI` | Profiles, pets, adoptions, chat persistence, and readiness | Defaults to `mongodb://localhost:27017`. |
| `DATABASE_NAME` | MongoDB database selection | Defaults to `pawfect`. Use the same name when creating the Atlas Vector Search index. |
| `ALLOWED_ORIGINS` | CORS origin allowlist | Defaults to `*` (allow all). Set a comma-separated list to restrict browser origins. |

`backend/app/config.py` calls `load_dotenv()` and reads only these four configuration variables. Start Uvicorn and seed commands with `backend/` as the working directory so `backend/.env` is found. `HOST`, `PORT`, and `DEBUG` are not read from the environment; pass the host and port to Uvicorn explicitly. The `.env` file contains secrets and must not be committed or shared.

For Atlas, create a database user, configure Network Access for the computer running the backend, and URL-encode special characters in the connection-string username/password. Atlas Vector Search is needed for the retrieval path. On startup and during seeding, the application attempts to set up the index named `vector_index`; if that is unsupported or fails, inspect the backend log and create the defined index manually using the JSON in the README or `backend/app/database/indexes.py`.

### Android API URL

By default, the Android emulator connects to:

```text
http://10.0.2.2:8000/api/v1/
```

`10.0.2.2` maps to the development computer from a standard Android emulator. A physical phone must use the computer's LAN IP (and be able to reach it). Override the URL at build time; keep the `/api/v1/` suffix and trailing slash:

```powershell
cd android
.\gradlew.bat :app:installDebug -PPAWFECT_API_BASE_URL=http://192.168.1.25:8000/api/v1/
```

Replace `192.168.1.25` with the development computer's LAN IP. Debug permits HTTP cleartext; release disables it, so configure an HTTPS endpoint for release builds. This is a Gradle property, not an Android runtime environment variable. A developer may put it in their local `android/gradle.properties`, but should not commit a machine-specific URL.

## 3. Install and start the backend

In PowerShell at the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

If PowerShell prevents activation, use the venv interpreter directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Start the API from the `backend/` directory:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Keep this terminal open. At startup the service attempts to create/verify standard MongoDB indexes and the Atlas vector index. A logged index error does not necessarily stop Uvicorn, but database-backed functions will fail until the database is reachable.

Check the liveness and readiness endpoints in a second terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health
```

Expected: liveness returns `status: alive`; readiness returns `status: healthy` and `database: connected`. A `503` readiness response means MongoDB is not available/configured. API documentation: <http://localhost:8000/docs>.

## 4. Seed the pet catalog

In another terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.scripts.seed_pets
```

The current seed source defines 36 records. It creates 768-dimensional embeddings using Gemini when a seed record does not already have a valid embedding, reuses valid existing embeddings, and skips seeding when the existing pet count is already at least the number of seed records. Initial embedding generation may take several minutes and consume API quota. If the seed reports a database or model error, fix the corresponding URI/key and retry.

Confirm that the catalog endpoint returns pets:

```powershell
$pets = Invoke-RestMethod 'http://localhost:8000/api/v1/pets?limit=5'
$pets | Select-Object _id, name, species, breed
```

The API response omits embedding vectors. Keep one returned `_id` for the evaluation/adoption checks below.

## 5. Run automated tests and builds

### Backend tests

With the backend virtual environment active and current directory `backend/`:

```powershell
pytest -q
```

The checked-in backend suite tests API health/catalog behavior, retrieval constraints and fallbacks, vector-index configuration, and error handling. These tests use fakes for database/AI boundaries; they do not prove a live Atlas or Gemini integration works.

### Android checks

Open the `android/` directory in Android Studio and wait for Gradle sync, or run from PowerShell:

```powershell
cd android
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug :app:assembleRelease :app:lintDebug
```

Expected: all tasks succeed. The current Android JVM unit tests cover API DTO serialization; they are not Compose UI or instrumentation tests. The debug APK is `android/app/build/outputs/apk/debug/app-debug.apk`. The release APK produced by the project is unsigned unless signing is separately configured.

## 6. Backend API smoke checks

Run these checks while the API is up and after the pet catalog has been seeded. They create or update test data in the configured database; use a development database. Run the PowerShell blocks in the same terminal session because later checks reuse `$petId`, `$suffix`, and `$user`.

### Check catalog and pet details

```powershell
$pets = Invoke-RestMethod 'http://localhost:8000/api/v1/pets?limit=5'
$petId = $pets[0]._id
Invoke-RestMethod "http://localhost:8000/api/v1/pets/$petId"
```

Expected: a list of pet records and a detail object for the selected pet.

### Check signup, profile, and saved pets

Use a unique test email to avoid colliding with an existing user:

```powershell
$suffix = [guid]::NewGuid().ToString('N').Substring(0, 8)
$signupBody = @{
    email = "pawfect-test-$suffix@example.com"
    password = "local-test-only"
    name = "PawFect Test"
    housing_type = "apartment"
    has_children = $false
    has_other_pets = $false
    energy_budget = 3
} | ConvertTo-Json
$user = Invoke-RestMethod -Method Post `
    -Uri 'http://localhost:8000/api/v1/users/auth/signup' `
    -ContentType 'application/json' -Body $signupBody
$user
Invoke-RestMethod "http://localhost:8000/api/v1/users/$($user.user_id)/profile"
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/users/$($user.user_id)/favorite/$petId"
Invoke-RestMethod "http://localhost:8000/api/v1/users/$($user.user_id)/saved-pets"
```

Expected: the signup response includes `user_id`, name, email, and a synthetic token; the profile request returns a profile; the favorite endpoint toggles the pet on; the saved-pets endpoint includes that pet. Repeating the favorite POST toggles it off.

### Check compatibility evaluation

```powershell
$evalBody = @{
    session_id = "handoff-$suffix"
    pet_id = $petId
    housing_type = "apartment"
    has_children = $false
    has_other_pets = $false
    energy_budget = 3
    notes = "Local implementation handoff check"
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri 'http://localhost:8000/api/v1/matches/direct-eval' `
    -ContentType 'application/json' -Body $evalBody
```

Expected: a pet name, a score from 0 to 100, pros, caveats, and a reasoning summary. The endpoint attempts an AI evaluation and can use a documented heuristic fallback if the model call fails; a successful response alone does not prove Gemini was used.

### Check adoption application and status

```powershell
$adoptionBody = @{
    user_id = $user.user_id
    pet_id = $petId
    applicant_name = $user.name
    applicant_email = $user.email
    applicant_phone = "555-0100"
    housing_details = "Apartment; local test only"
    household_members = "No children or other pets"
    notes = "Delete this test application if no longer needed"
} | ConvertTo-Json
$application = Invoke-RestMethod -Method Post `
    -Uri 'http://localhost:8000/api/v1/adoptions/apply' `
    -ContentType 'application/json' -Body $adoptionBody
$application
Invoke-RestMethod "http://localhost:8000/api/v1/adoptions/$($application.application_id)/status"
```

Expected: application data including `application_id` and an initial `stage_status`, followed by the same application's status. The API does not provide an application deletion endpoint.

### Check chat

Chat requires a reachable MongoDB and a working Gemini configuration. A non-streaming request is:

```powershell
$chatBody = @{
    session_id = "handoff-$suffix"
    user_id = $user.user_id
    message = "I live in an apartment and would like a calm companion."
    stream = $false
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri 'http://localhost:8000/api/v1/chat/message' `
    -ContentType 'application/json' -Body $chatBody
```

Expected: a response message and chat state fields. To try SSE, run:

```powershell
$sseBody = @{
    session_id = "handoff-sse-$suffix"
    user_id = $user.user_id
    message = "I live in a house and enjoy daily walks."
    stream = $true
} | ConvertTo-Json -Compress
curl.exe -N 'http://localhost:8000/api/v1/chat/message' `
    -H 'Content-Type: application/json' `
    -H 'Accept: text/event-stream' `
    --data-binary $sseBody
```

The server emits `typing`, `token`, optional `quick_replies`/`matches`, and terminal `done` events (or `error` on failure).

## 7. End-to-end Android smoke test

1. Leave the backend running; confirm `/health` is healthy and `/api/v1/pets?limit=1` returns a pet.
2. In Android Studio, open `android/`, sync Gradle, start an emulator, and run the `app` configuration. For the standard emulator, keep the default `10.0.2.2` URL.
3. If using a physical device or a non-default host port, install with `-PPAWFECT_API_BASE_URL=...` as described above. Ensure the phone can reach the computer and the computer firewall permits the API port.
4. On the welcome screen, try **Sign up** with a fresh test email, then complete onboarding. Verify successful navigation into the app.
5. Open Home/catalog. Confirm real pet entries load; tap one and verify its details and image.
6. Save a pet, open Matches or Saved Pets, and confirm the saved state appears. Toggle it off and confirm it is removed.
7. Open compatibility for a pet. Confirm loading completes and a score, explanation, pros, and caveats are shown.
8. Open AI Chat and send a lifestyle answer. Confirm a response arrives. Continue answering questions and verify that matches appear when intake is complete. Check backend logs for Gemini/API errors if it stalls or fails.
9. Submit a test adoption application and verify that a status/progress view appears. The API persists this test record and does not expose a delete operation.
10. Open Profile, change a supported preference, save, leave and return to check persistence. Log out and log in again to check the app's local session flow.

If a request fails, inspect the Android app state/error text, the Uvicorn console, and Android Studio Logcat filtered to `com.pawfect.app` / `AndroidRuntime`. For emulator connectivity, use `http://10.0.2.2:8000/health/live` from the emulator browser; `localhost` inside Android points to the emulator, not the development computer.

## 8. Important implementation limits

- Backend login is demo-style: the supplied password is not validated, login may create a profile, and the returned token is synthetic. Authentication is not suitable for protecting production data.
- The Android app keeps session and chat state locally. The backend persists chat turns but has no endpoint for retrieving chat history.
- Catalog and other app features use backend data; there is no client-side sample-pet fallback.
- API/manual smoke tests need real services and may incur Gemini usage. Unit tests use test doubles and do not replace these checks.
- Release cleartext traffic is disabled and the generated release APK is unsigned.
