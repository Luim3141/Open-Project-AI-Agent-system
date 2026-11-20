#!/bin/sh
# Quick Tunnel Self-Healing Supervisor
# Runs cloudflared as child process; monitors health endpoint /ready.
# On persistent unhealthiness (5 failures = 75s), self-terminates with exit 1,
# triggering Docker's native 'restart: unless-stopped' policy without requiring Docker socket.

set -e

STARTUP_GRACE_PERIOD=60
CHECK_INTERVAL=15
MAX_FAILS=5
FAIL_COUNT=0

echo "[QuickTunnel Supervisor] Starting cloudflared tunnel to http://staging-web:8080..."
cloudflared tunnel --no-autoupdate --metrics 0.0.0.0:2000 --url http://staging-web:8080 &
CF_PID=$!
echo "[QuickTunnel Supervisor] cloudflared launched with PID ${CF_PID}."

# Handle shutdown signals gracefully
cleanup() {
    echo "[QuickTunnel Supervisor] Received stop signal. Terminating child PID ${CF_PID}..."
    kill -TERM "${CF_PID}" 2>/dev/null || true
    wait "${CF_PID}" 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT

# Initial startup grace period
echo "[QuickTunnel Supervisor] Waiting ${STARTUP_GRACE_PERIOD}s grace period for edge connection..."
sleep "${STARTUP_GRACE_PERIOD}"

# Monitoring loop
while kill -0 "${CF_PID}" 2>/dev/null; do
    if [ ! -f /tmp/fault_inject ] && wget -q -O - http://127.0.0.1:2000/ready >/dev/null 2>&1; then
        if [ "${FAIL_COUNT}" -gt 0 ]; then
            echo "[QuickTunnel Supervisor] Edge tunnel healthy again. Resetting failure counter (was ${FAIL_COUNT})."
            FAIL_COUNT=0
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "[QuickTunnel Supervisor] Healthcheck failed (${FAIL_COUNT}/${MAX_FAILS})."

        if [ "${FAIL_COUNT}" -ge "${MAX_FAILS}" ]; then
            echo "[QuickTunnel Supervisor] PERSISTENT_UNHEALTHY: ${FAIL_COUNT} consecutive failures reached."
            echo "[QuickTunnel Supervisor] Initiating graceful termination to trigger Docker restart: unless-stopped..."
            kill -TERM "${CF_PID}" 2>/dev/null || true
            sleep 3
            kill -KILL "${CF_PID}" 2>/dev/null || true
            exit 1
        fi
    fi
    sleep "${CHECK_INTERVAL}"
done

echo "[QuickTunnel Supervisor] cloudflared exited unexpectedly with code $?."
exit 1
