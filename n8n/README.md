# n8n Memory Workflows

These workflows provide persistent cross-session memory for the voice assistant via SQLite.

## Setup

### 1. Start n8n

```bash
# From project root
docker compose up -d
```

n8n UI will be available at http://localhost:5678.
Login with the credentials you set in `.env` (`N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`).

### 2. Import Workflows

1. Open http://localhost:5678
2. Go to **Workflows** → **Import from file**
3. Import `memory_store_workflow.json`
4. Import `memory_retrieve_workflow.json`
5. Activate both workflows (toggle in top-right of each workflow editor)

### 3. Note the Webhook URLs

After importing and activating, n8n will show the production webhook URLs:
- Store: `http://localhost:5678/webhook/memory/store`
- Retrieve: `http://localhost:5678/webhook/memory/retrieve`

These should match what you have in your backend `.env`:
```ini
N8N_MEMORY_STORE_PATH=/webhook/memory/store
N8N_MEMORY_RETRIEVE_PATH=/webhook/memory/retrieve
```

## Workflow Details

Both workflows use n8n's built-in **Static Workflow Data** (`$getWorkflowStaticData`) — no community nodes or external database required. Data is stored inside n8n's own internal database and persists across container restarts as long as the `n8n_data` volume exists.

### memory_store
- Receives POST from backend `/tools/memory/store`
- Appends the turn to the session's history (capped at 20 turns per session)
- Returns `{ success: true, session_id, turn_count }`

### memory_retrieve
- Receives POST from backend `/tools/memory/get`
- Returns the 5 most recent turns for the session
- Extracts a `known_contacts` map from transcript history

## Data shape (in-memory)

```json
{
  "sessions": {
    "<session_id>": [
      {
        "transcript": "Add a meeting with Sarah tomorrow",
        "action_taken": "create_event",
        "result_summary": "Event created",
        "timestamp": "2026-03-14T10:00:00Z"
      }
    ]
  }
}
```
