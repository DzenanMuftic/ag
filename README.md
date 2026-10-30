# AG — Mobile Automation Toolkit

Self-hosted tools that run on an Android phone (Termux) and are exposed to the
internet via Cloudflare quick tunnels.

## Projects

### 1. `email-alerts/` — AI Email Auto-Responder
Reads an inbox over IMAP, detects "important" emails, drafts a sales reply in
**Bosnian** using the **DeepSeek** API, and sends the result to **Telegram**.
Runs every 5 minutes via cron.

- **Flow:** inbox → filter important → DeepSeek (Bosnian sales reply) → Telegram
- **Scheduler:** cron (`*/5 * * * *`)
- **Optional auto-send:** the reply can be emailed back to the sender via SMTP
  by setting `AUTO_SEND=true` (default is `false` = send draft to Telegram only).

**Setup**

1. `cp email-alerts/.env.example email-alerts/.env` and fill in your values.
2. Run once to test: `python3 email-alerts/email_alerts.py --dry-run`
3. Run for real: `python3 email-alerts/email_alerts.py`
4. Schedule with cron:
   ```sh
   echo '*/5 * * * * python3 ~/email-alerts/email_alerts.py >> ~/email-alerts/cron.log 2>&1' | crontab -
   ```

**"Important" filter rules** (edit `KEYWORDS`, `IMPORTANT_SENDERS`, `BLOCKLIST`):
- Critical senders (bounces, service alerts, support)
- Action keywords in subject/body (`invoice`, `suspended`, `password reset`, …)
- Newsletters / marketing are ignored

### 2. `name-app/` — Name Greeting Web App
A tiny self-contained web app (enter a name → shows it on screen). Served by a
dependency-free Node.js server.

```sh
cd name-app && node server.js   # serves on http://localhost:8090
```

### 3. `phone/` — Helper Scripts (Termux)
- `start-terminal.sh` — expose a web terminal (ttyd) for remote access
- `start-app.sh` — start the name app + open a public tunnel
- `stop-all.sh` — stop the terminal, tunnels and app server

## Security
- **Never commit `.env`** (real credentials). Use `.env.example` as a template.
- Cloudflare quick tunnels have no uptime guarantee and the URL changes on restart.

## Tested on
Snapdragon 7s Gen 3 · 8 cores · Adreno 810 · 12 GB RAM (Redmi Note 14 Pro)
