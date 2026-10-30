#!/data/data/com.termux/files/usr/bin/bash
# start-terminal.sh — expose a web terminal so the AI can connect.
# Run in Termux:  bash start-terminal.sh
ttyd -W -p 8080 bash &
TTYD_PID=$!
sleep 2
cloudflared tunnel --url http://localhost:8080
