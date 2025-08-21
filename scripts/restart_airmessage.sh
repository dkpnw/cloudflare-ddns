#!/bin/sh
set -e
USER="${AIRMESSAGE_SSH_USER:?set AIRMESSAGE_SSH_USER}"
HOST="${AIRMESSAGE_SSH_HOST:-host.docker.internal}"
REMOTE_CMD="${AIRMESSAGE_REMOTE_CMD:-pkill -x AirMessage || true; sleep 5; open -a AirMessage}"

mkdir -p /root/.ssh
ssh-keyscan -t ed25519 "$HOST" > /tmp/kh 2>/dev/null || true
mv /tmp/kh /root/.ssh/known_hosts

exec ssh -q -o LogLevel=ERROR -o BatchMode=yes \
  -o PreferredAuthentications=publickey \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/root/.ssh/known_hosts \
  -i /ssh/airmessage_rsa \
  "$USER@$HOST" "$REMOTE_CMD"
