#!/bin/sh
set -e

# Uncomment the next line once for verbose troubleshooting
# set -x

mkdir -p /root/.ssh

# Refresh known_hosts atomically so StrictHostKeyChecking can be 'yes'
ssh-keyscan -t ed25519 host.docker.internal > /tmp/kh 2>/dev/null || true
mv /tmp/kh /root/.ssh/known_hosts

# Public-key only; fail fast if key isn’t accepted (no password fallback/hangs)
exec ssh -q -o LogLevel=ERROR -o BatchMode=yes \
  -o PreferredAuthentications=publickey \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/root/.ssh/known_hosts \
  -i /ssh/airmessage_rsa \
  drewpine@host.docker.internal \
  'pkill -x AirMessage || true; sleep 5; open -a AirMessage'
