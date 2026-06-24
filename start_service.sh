#!/bin/bash
set -e

# 📁 1. UPDATE TARGET DIRECTORY TO YOUR NEW REPOSITORY LAYOUT
cd /workspaces/cloud-extractor

echo "Cleaning up older workers..."
pkill -f uvicorn || true
pkill -f ngrok || true
sleep 2

echo "Launching Uvicorn server layer with system environment tokens..."
# Injected env parsing to ensure os.getenv("GITHUB_TOKEN") extracts perfectly inside server.py
export GITHUB_TOKEN="${GH_TOKEN:-$GITHUB_TOKEN}"
nohup python3 -m uvicorn server:app --host 0.0.0.0 --port 5000 > /tmp/server.log 2>&1 &

echo "Waiting for port 5000 socket binding..."
for i in {1..30}; do
    if ss -tulpn | grep ':5000' > /dev/null; then
        echo "SUCCESS: Port 5000 is open!"
        break
    fi
    sleep 2
done

echo "Launching Ngrok tunnel link..."
nohup ngrok http --url=whacking-rice-stubbed.ngrok-free.dev 5000 > /tmp/ngrok.log 2>&1 &

# =========================================================
# 🔥 THE STAY-ALIVE SHIELD: KEEP SCRIPT ALIVE DURING TRANSFERS
# =========================================================
echo "Shield Active: Locking shell open to prevent auto-timeout..."
while true; do
    # Check if uvicorn is still running (Python script keeps it running until upload finishes)
    if ! pgrep -f uvicorn > /dev/null; then
        echo "Server stopped processing. Exiting lock loop..."
        break
    fi
    
    echo "Keep-Alive Heartbeat: Transfer processing via /tmp partition..."
    sleep 60
done

# =========================================================
# 🛑 AUTOMATED SELF-DESTRUCT / CLOSING SEQUENCE
# =========================================================
echo "Upload complete! Sending termination signals to environment..."
pkill -f ngrok || true

echo "Closing connection and shutting down this Codespace instance."
# This kills the main active shell process cleanly, terminating the headless worker session safely!
kill -9 $$
