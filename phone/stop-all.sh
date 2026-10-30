#!/data/data/com.termux/files/usr/bin/bash
# stop-all.sh — stop the web terminal, tunnels, and name-app server.
# Run in Termux:  bash stop-all.sh
echo "Stopping ttyd, cloudflared, and name-app server..."
pkill -f 'ttyd -W -p 8080' 2>/dev/null
pkill -f 'cloudflared tunnel --url http://localhost:8080' 2>/dev/null
pkill -f 'cloudflared tunnel --url http://localhost:8090' 2>/dev/null
pkill -f 'node server.js' 2>/dev/null
echo "Done. Verify with: ps -A -o pid,args | grep -E 'ttyd|cloudflared|node server.js'"
