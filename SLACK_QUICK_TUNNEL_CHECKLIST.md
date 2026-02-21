# 30-Second Slack Quick Tunnel Checklist

Use this only when the `trycloudflare.com` URL changes.

## When the URL changes
Quick tunnel URLs can change when:
- machine restart or user logout/login (tunnel process restarts)
- `cloudflared` process is restarted or crashed
- laptop/network reconnect causes tunnel process restart
- you manually start a new quick tunnel session

> Quick note: `trycloudflare.com` quick tunnels are ephemeral by design. For stable URLs across restarts, use a named tunnel with your own domain.

## Get the new URL fast
Run:

```bash
python3 - <<'PY'
from pathlib import Path
log = Path('/tmp/cf-backlogai.log')
if not log.exists():
    print('No tunnel log found. Start tunnel first.')
else:
    lines = log.read_text(errors='ignore').splitlines()
    urls = [l.split('https://',1)[1].strip() for l in lines if 'trycloudflare.com' in l and 'https://' in l]
    if urls:
        print('https://' + urls[-1].split()[0])
    else:
        print('No URL found in log yet.')
PY
```

## Update Slack in under 30 seconds
1. Open `https://api.slack.com/apps` and select your app.
2. **Slash Commands** -> `/backlogai` -> set Request URL:
   - `https://<new-url>.trycloudflare.com/slack/commands`
3. **Interactivity & Shortcuts** -> set Request URL:
   - `https://<new-url>.trycloudflare.com/slack/interactions`
4. Save both pages.
5. Test in Slack with `/backlogai`.

## Quick health check

```bash
curl https://<new-url>.trycloudflare.com/health
```

Expected: HTTP `200` with API health payload.
