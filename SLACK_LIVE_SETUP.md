# Slack Live Setup Guide (Local BacklogAI + Local Jira)

This guide helps you run a real end-to-end Slack flow with your current local setup.

## Current Assumptions
- BacklogAI backend runs locally on port `8001`
- Jira runs locally on port `8081`
- Cloudflare quick tunnel URL for BacklogAI:
  - `https://acts-destination-dayton-insertion.trycloudflare.com`

> Note: Quick tunnel URLs are temporary. If the tunnel restarts, update Slack callback URLs with the new URL.

---

## 1) Configure Slack callback URLs

### What
Set where Slack sends command and interaction requests.

### Why
Without callback URLs, Slack cannot reach your backend.

### How
1. Open `https://api.slack.com/apps`
2. Select your Slack app
3. Go to **Slash Commands**
   - Create/edit command: `/backlogai`
   - Request URL:
     - `https://acts-destination-dayton-insertion.trycloudflare.com/slack/commands`
4. Go to **Interactivity & Shortcuts**
   - Enable Interactivity
   - Request URL:
     - `https://acts-destination-dayton-insertion.trycloudflare.com/slack/interactions`

---

## 2) Add required scopes and reinstall Slack app

### What
Grant bot permissions to receive commands and post messages.

### Why
Missing scopes block Slack flows even if endpoints are correct.

### How
1. Slack app settings -> **OAuth & Permissions**
2. Under **Bot Token Scopes**, add:
   - `commands`
   - `chat:write`
   - Optional: `channels:history`, `users:read`
3. Click **Install to Workspace** or **Reinstall to Workspace**
4. Copy **Bot User OAuth Token** (`xoxb-...`) for Step 3

---

## 3) Configure local `.env`

### What
Provide Slack credentials to backend.

### Why
Backend needs these to verify Slack requests and post replies.

### How
Add/update in project `.env`:

```properties
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_INTEGRATION_ENABLED=true
```

Where to find signing secret:
- Slack app settings -> **Basic Information** -> **App Credentials** -> `Signing Secret`

---

## 4) Restart backend to load env vars

### What
Restart backend process.

### Why
Existing process does not auto-load changed `.env` values.

### How
From repo root:

```bash
pkill -f "uvicorn app.main:app" || true

nohup env PYTHONPATH="/Users/rameshk/Desktop/projects/BacklogAI/backend" JIRA_URL="http://localhost:8081" \
/Users/rameshk/Desktop/projects/BacklogAI/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 \
> /tmp/backlogai-backend-8001.log 2>&1 &
```

Quick checks:

```bash
curl http://127.0.0.1:8001/health
curl https://acts-destination-dayton-insertion.trycloudflare.com/health
```

Both should respond successfully.

---

## 5) Run end-to-end validation in Slack

### What
Run the real user flow.

### Why
Confirms Slack -> BacklogAI -> Jira integration works end-to-end.

### How
1. In Slack channel, run `/backlogai`
2. Fill modal inputs and submit
3. Confirm Story Preview appears
4. Click **Sync to JIRA**
5. Confirm Slack posts Jira key + URL
6. Open Jira URL and verify issue exists

---

## Troubleshooting

- **Invalid Slack signature**
  - Check `SLACK_SIGNING_SECRET`
  - Confirm Slack callbacks hit the same tunnel URL configured in app settings

- **Command works but no preview**
  - Check backend logs: `/tmp/backlogai-backend-8001.log`
  - Verify `SLACK_BOT_TOKEN` and `chat:write` scope

- **Preview appears but Sync fails**
  - Check Jira availability at `http://localhost:8081`
  - Verify Jira credentials in `.env`

- **Tunnel URL changed**
  - Update Slack command and interactivity URLs with the new tunnel URL
