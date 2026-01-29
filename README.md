# Alfred Mission Control

Real-time dashboard for monitoring AI agent operations.

## Overview

Mission Control provides visibility into Alfred's activities:
- **Sessions**: Active and recent conversation sessions
- **Sub-Agents**: Spawned task instances and their status
- **Scheduled Tasks**: Cron jobs and upcoming runs
- **Activity Feed**: Chronological event stream

## Tech Stack

- **Frontend**: Streamlit
- **Data**: JSON files maintained by Alfred
- **Hosting**: Streamlit Cloud (planned)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Data Sources

The dashboard reads from files in `/root/clawd/memory/dashboard/`:

| File | Description |
|------|-------------|
| `status.json` | Current agent status (online, counts) |
| `sessions.json` | Active session list |
| `subagent-log.jsonl` | Sub-agent spawn/completion events |
| `activity-feed.jsonl` | Chronological activity events |

Alfred updates these files during normal operations.

## Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect repo to Streamlit Cloud
3. Set `WORKSPACE_PATH` secret if needed

### Local

```bash
export WORKSPACE_PATH=/root/clawd
streamlit run app.py
```

## Project Status

**Milestone 1** (In Progress):
- [x] Project scaffolding
- [x] Home page with status
- [x] Sessions list view
- [ ] Session detail view
- [ ] Deploy to Streamlit Cloud

See full PRD: `deliverables/projects/agent-dashboard/PRD.md`
