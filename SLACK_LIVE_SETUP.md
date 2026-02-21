# Slack Live Setup Guide (Local BacklogAI + Local Jira)

This guide helps you run a real end-to-end Slack flow with your current local setup.

## Current Assumptions
- BacklogAI backend runs locally on port `8001`
- Jira runs locally on port `8081`
- Cloudflare quick tunnel URL for BacklogAI:
  - 📋 `https://taxi-copying-powered-recorded.trycloudflare.com`
- Cloudflare quick tunnel URL for Jira:
  - 📋 `https://electricity-relationships-activists-clubs.trycloudflare.com`

> Tip: GitHub shows a copy button on fenced code blocks. Use it for commands below.

> Note: Quick tunnel URLs are temporary. If the tunnel restarts, update Slack callback URLs with the new URL.

---

## 1) Configure Slack callback URLs

### What
Set where Slack sends command and interaction requests.

### Why
Without callback URLs, Slack cannot reach your backend.

### How
1. Open 📋 `https://api.slack.com/apps`
2. If you do not have an app yet:
   - Click **Create New App**
   - Choose **From scratch**
   - Enter app name (for example: `BacklogAI Bot`)
   - Select your workspace and click **Create App**
3. Select your Slack app
4. In the app settings page, use this navigation path:
   - **Left Sidebar** -> **Features** -> **Slash Commands**
   - If you cannot find it, scroll the sidebar and expand **Features**
5. In **Slash Commands**:
   - Click **Create New Command** (or edit existing)
   - Command: `/backlogai`
   - Short description: `Generate backlog story preview`
    - Usage hint: `opens input modal`
    - Request URL:
      - 📋 `https://taxi-copying-powered-recorded.trycloudflare.com/slack/commands`
   - Click **Save**
6. In the left sidebar, open **Interactivity & Shortcuts**
   - Enable Interactivity
   - Request URL:
      - 📋 `https://taxi-copying-powered-recorded.trycloudflare.com/slack/interactions`
   - Click **Save Changes**

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
📋 Copy into project `.env`:

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

📋 Copy and run:

```bash
pkill -f "uvicorn app.main:app" || true

nohup env PYTHONPATH="/Users/rameshk/Desktop/projects/BacklogAI/backend" JIRA_URL="http://localhost:8081" \
/Users/rameshk/Desktop/projects/BacklogAI/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 \
> /tmp/backlogai-backend-8001.log 2>&1 &
```

Quick checks:

📋 Copy and run:

```bash
curl http://127.0.0.1:8001/health
curl https://taxi-copying-powered-recorded.trycloudflare.com/health
curl https://electricity-relationships-activists-clubs.trycloudflare.com
```

Both should respond successfully.

---

## 5) Run end-to-end validation in Slack

### What
Run the real user flow.

### Why
Confirms Slack -> BacklogAI -> Jira integration works end-to-end.

### How
1. In Slack channel, run 📋 `/backlogai`
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

- **Cannot find Slash Commands panel**
  - Open your app at `https://api.slack.com/apps`
  - Select your app first (panel appears only inside an app)
  - In left sidebar, expand **Features** and choose **Slash Commands**
  - If needed, refresh browser after app creation

- **Command works but no preview**
  - Check backend logs: `/tmp/backlogai-backend-8001.log`
  - Verify `SLACK_BOT_TOKEN` and `chat:write` scope

- **Preview appears but Sync fails**
  - Check Jira availability at `http://localhost:8081`
  - Verify Jira credentials in `.env`

- **Tunnel URL changed**
  - Update Slack command and interactivity URLs with the new tunnel URL
  - Use quick checklist: [`SLACK_QUICK_TUNNEL_CHECKLIST.md`](./SLACK_QUICK_TUNNEL_CHECKLIST.md)
