#!/data/data/com.termux/files/usr/bin/bash
# start-app.sh — run the name app + expose it publicly.
# Run in Termux:  bash start-app.sh
cd ~/name-app || exit 1

# start the app server (detached)
setsid nohup node server.js > ~/name-app/server.log 2>&1 < /dev/null &
sleep 2

# expose it with a fresh quick tunnel (prints the public URL)
cloudflared tunnel --url http://localhost:8090
