# Session Notes — Mobile Web App + LLM Check

Date: 2026-10-30
Phone: Redmi 24115RA8EG (Redmi Note 14 Pro, global) — Termux on Android
Working machine (AI side): Ubuntu 24.04, /opt/mobitel

---

## 1. Goal
Create a small web app (enter name → show name on screen), run it **on the phone**,
and expose it to the internet.

## 2. What was done
1. Probed the existing "DeepSeek" endpoint
   `https://integration-broadcast-crossword-leaving.trycloudflare.com/v1/chat`
   → it is a Node/Express **relay** (`~/deepseek-relay/server.js`, port 3000) that
   forwards to the cloud `https://api.deepseek.com/chat/completions`. It is **NOT** a
   local LLM — the phone does zero inference.
2. Set up remote shell access to the phone:
   - Installed `ttyd` and `cloudflared` (pkg install).
   - `ttyd -W -p 8080 bash`  (note: `-W` = writable, required)
   - `cloudflared tunnel --url http://localhost:8080` (separate session)
   - Drove the terminal over WebSocket (`wss://.../ws`, subprotocol `tty`) using
     a Node `ws` client. ttyd protocol: first byte = command ('{' = JSON init
     `{"columns":..,"rows":..}`, '0' = input, '0' = output, '1'/'2' = title/prefs).
3. Built the app and deployed to the phone:
   - `~/name-app/index.html`  (self-contained HTML/CSS/JS app)
   - `~/name-app/server.js`   (Node http server, port 8090, CommonJS)
   - Started detached: `setsid nohup node server.js > ~/name-app/server.log 2>&1 &`
   - Exposed: `setsid nohup cloudflared tunnel --url http://localhost:8090 > ~/name-app/tunnel.log 2>&1 &`
4. Verified the app is reachable from the internet (HTTP 200, 5109 bytes).
5. Checked phone hardware + local-LLM capability (see section 6).

## 3. Key files on the phone (Termux)
```
~/name-app/index.html    # the web app (name input -> "Hello, {name}! 🎉")
~/name-app/server.js     # serves index.html on port 8090
~/name-app/server.log    # app server output
~/name-app/tunnel.log    # app tunnel output (contains current URL)
~/deepseek-relay/        # existing DeepSeek relay (port 3000) - unrelated to app
```

## 4. URLs (all Cloudflare QUICK tunnels — TEMPORARY, change on restart)
| Purpose | URL |
|---|---|
| Name app (public) | https://bases-feelings-hence-explicitly.trycloudflare.com |
| DeepSeek relay | https://integration-broadcast-crossword-leaving.trycloudflare.com |
| Web terminal (AI access) | https://pipes-noted-wives-offset.trycloudflare.com (now stopped) |

To get a fresh URL at any time, run the corresponding `cloudflared tunnel --url ...`
command and read the printed URL.

## 5. How to reconnect the AI (web terminal)
On the phone, in Termux:
```sh
ttyd -W -p 8080 bash                      # session 1 (leave running)
cloudflared tunnel --url http://localhost:8080   # session 2 (leave running)
```
Then share the new `https://....trycloudflare.com` URL.

## 6. Phone specs + local-LLM capability
- SoC: Qualcomm Snapdragon 7s Gen 3 (SM7635, 4nm)
- CPU: 8 cores = 4x Cortex-A720 @ 2.4-2.5 GHz + 4x Cortex-A520 @ 1.8 GHz
- GPU: Adreno 810 (Vulkan-capable)
- RAM: 12 GB (11.1 GiB) + 12 GB zram (MIUI "Memory Extension")
- Storage: 465 GB, ~383 GB free

Local LLM assessment:
- 1.5B Q4 ~1.2 GB → 20-40 tok/s  ✅
- 3B   Q4 ~2.5 GB → 10-20 tok/s  ✅ recommended
- 4B   Q4 ~3 GB   → 8-15 tok/s   ✅
- 7-8B Q4_K_M ~4.5 GB → 4-8 tok/s (CPU) / up to ~15 (Vulkan)  ⚠️ reboot first, or use Q4_K_S
- 14B  Q4 ~9 GB   → 2-4 tok/s    ❌ too tight

zram/swap does NOT help inference speed. Available RAM right now ≈ 4.7 GB.
Termux processes are tiny (~210 MB total) — not the bottleneck.

## 7. Cleanup / stop commands (on the phone)
```sh
# stop the web terminal + its tunnel (do this after AI access)
kill 19667 21225
# stop the name app + its tunnel (when done with the app)
kill 23861 24126
# stop the DeepSeek relay (only if you want)
kill 9223
# find current PIDs anytime:
ps -A -o pid,args | grep -E 'ttyd|cloudflared|node server.js' | grep -v grep
```
Note: PIDs change after reboot — re-list before killing.

## 8. Keep-alive tips (Android)
- `termux-wake-lock` in Termux to prevent CPU sleep.
- Disable battery optimization for Termux (Settings → Apps → Termux → Battery → Unrestricted).
- Quick tunnels have no uptime guarantee; for a permanent URL use a named tunnel (needs Cloudflare account).
