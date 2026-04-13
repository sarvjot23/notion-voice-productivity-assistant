# Voice Productivity Assistant — Setup Guide

## Prerequisites

- Python 3.11+
- Docker Desktop (for n8n)
- ngrok (free tier is fine)
- Accounts: ElevenLabs, Todoist, Google Cloud, Notion

---

## Step 1 — Get your API keys

### ElevenLabs
1. Sign up at elevenlabs.io
2. Go to **Profile** → **API Keys** → copy your key
3. You'll get the Agent ID later (Step 6)

### Todoist
1. Go to todoist.com → **Settings** → **Integrations** → **Developer**
2. Copy your **API token**

### Google Calendar
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable **Google Calendar API** (APIs & Services → Enable APIs)
4. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON — you'll use the `client_id` and `client_secret` values

### Notion
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration** → give it a name → copy the **Internal Integration Secret**
3. You'll get the Database ID in Step 4

---

## Step 2 — Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in:

```ini
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_WEBHOOK_SECRET=make_up_any_random_string   # e.g. openssl rand -hex 20

TODOIST_API_TOKEN=your_token_here

GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

NOTION_API_KEY=secret_your_integration_token

N8N_PASSWORD=choose_a_password_for_the_n8n_ui
N8N_WEBHOOK_SECRET=make_up_any_random_string
```

Leave these as-is for now — they'll be filled automatically:
```ini
ELEVENLABS_AGENT_ID=        # filled after Step 6
NOTION_NOTES_DATABASE_ID=   # filled after Step 4
GOOGLE_TOKEN_FILE=.google_token.json
```

Copy `.env.example` to the project root too (needed for Docker):
```bash
cp .env.example .env
# Set N8N_PASSWORD= in the root .env to match backend/.env
```

---

## Step 3 — Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## Step 4 — Set up Google Calendar OAuth

This is a one-time flow. A browser window will open asking you to authorize the app.

```bash
# Run from the backend/ directory
python ../scripts/setup_google_oauth.py
```

Follow the browser prompt → grant Calendar access → the token is saved to `.google_token.json`.

---

## Step 5 — Set up Notion database

### Connect your integration to a page first
1. Open Notion → navigate to any top-level page you want the notes database to live under
2. Click **...** (More) → **Add connections** → select your integration

### Run the seed script
```bash
# Find your page ID: it's the 32-char hex string in the page's URL
# e.g. notion.so/My-Page-abc123def456... → page ID is abc123def456...
python ../scripts/seed_notion_db.py --parent-page-id YOUR_PAGE_ID
```

The script prints the new database ID. Copy it into `backend/.env`:
```ini
NOTION_NOTES_DATABASE_ID=the_id_printed_by_the_script
```

---

## Step 6 — Start n8n (memory layer)

```bash
# From project root
docker compose up -d
```

n8n is now running at **http://localhost:5678**.

1. Log in with username `admin` and the `N8N_PASSWORD` you set
2. Go to **Workflows** → **Add workflow** → top-right menu (three dots or **+**) → **Import from file** → select `n8n/memory_store_workflow.json` → **Save**
3. Go back to **Workflows** → **Add workflow** → **Import from file** → select `n8n/memory_retrieve_workflow.json` → **Save**
4. Each workflow has an **Active** toggle in the top-right of the editor (shows as inactive/grey by default). Flip it to on for both. This is what enables the webhook URL to accept requests.

No extra nodes to install — the workflows use n8n's built-in static data storage.

---

## Step 7 — Start the backend

```bash
# From the backend/ directory
uvicorn main:app --reload
```

Verify it's working:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## Step 8 — Expose the backend publicly

ElevenLabs' cloud needs to reach your local backend. In a new terminal:

```bash
ngrok http 8000
```

Copy the `https://` URL it gives you (e.g. `https://abc123.ngrok.io`).

---

## Step 9 — Create the ElevenLabs agent

```bash
# From the backend/ directory
python ../scripts/create_elevenlabs_agent.py --backend-url https://YOUR-NGROK-ID.ngrok.io
```

The script prints the Agent ID. Copy it into `backend/.env`:
```ini
ELEVENLABS_AGENT_ID=the_id_printed_by_the_script
```

---

## Step 10 — Configure the frontend

Open `frontend/app.js` and set your Agent ID on line 13:

```javascript
const AGENT_ID = "your_agent_id_here";
```

---

## Step 11 — Run the assistant

Open `frontend/index.html` directly in your browser (or serve it with any static server):

```bash
# Option A: open directly
start frontend/index.html    # Windows
open frontend/index.html     # Mac

# Option B: serve with Python (fixes some CORS edge cases)
cd frontend && python -m http.server 3000
# Then open http://localhost:3000
```

Click **Start** (or press **Space**), speak naturally, and the assistant will respond.

---

## Verify everything works

Run the integration test suite:

```bash
# From the backend/ directory (with the server running)
python ../scripts/test_pipeline.py
```

Expected output:
```
[Backend Health]
  ✓ GET /health

[Todoist]
  ✓ create_task
  ✓ list_tasks

[Google Calendar]
  ✓ create_event
  ✓ list_events

[Notion]
  ✓ create_note

[Memory / n8n]
  ✓ memory_store
  ✓ memory_retrieve
```

Test individual services if something fails:
```bash
python ../scripts/test_pipeline.py --service todoist
python ../scripts/test_pipeline.py --service gcal
python ../scripts/test_pipeline.py --service notion
python ../scripts/test_pipeline.py --service memory
```

---

## Example voice commands to try

| Say this... | What happens |
|---|---|
| "Add a task: review the Henderson proposal by Friday" | Creates Todoist task due Friday |
| "Schedule a meeting with Sarah tomorrow at 2pm" | Creates Google Calendar event |
| "Take a note: project ideas — use AI for onboarding" | Creates Notion page |
| "What's on my calendar this week?" | Reads back upcoming events |
| "What tasks do I have today?" | Reads back today's Todoist tasks |

---

## Troubleshooting

**Mic access denied**
Browser requires HTTPS or localhost for microphone. Use `http://localhost:3000` (not a file:// path).

**ElevenLabs can't reach backend**
- Confirm ngrok is running and the URL in the agent config is correct
- If ngrok URL changed (free tier), re-run `create_elevenlabs_agent.py --update --backend-url NEW_URL`

**Google Calendar errors**
- Token expired: re-run `setup_google_oauth.py`
- Quota error: check Google Cloud Console quotas

**n8n memory not working**
- The backend degrades gracefully — tool calls still work without memory
- Check n8n at http://localhost:5678 → verify both workflows are Active
- Check Docker is running: `docker compose ps`

**Agent ID not found / 404**
- Verify `ELEVENLABS_AGENT_ID` in `backend/.env` matches the dashboard
- Check ElevenLabs dashboard → Conversational AI → your agent

---

## Updating the agent after code changes

If you change tool endpoints or the system prompt:
```bash
python scripts/create_elevenlabs_agent.py \
  --backend-url https://YOUR-NGROK-ID.ngrok.io \
  --update
```

## Stopping everything

```bash
# Stop n8n
docker compose down

# Stop backend: Ctrl+C in that terminal
# Stop ngrok: Ctrl+C in that terminal
```
