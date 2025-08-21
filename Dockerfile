# ---- Base ----
FROM python:alpine AS base

# ---- Dependencies ----
FROM base AS dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# ---- Release ----
FROM base AS release

# ✅ add ssh client + tzdata for restart script & local-time logs
RUN apk add --no-cache openssh-client tzdata ca-certificates && update-ca-certificates

WORKDIR /
COPY --from=dependencies /root/.local /root/.local
COPY cloudflare-ddns.py /cloudflare-ddns.py
# install tools needed by the restart script (keep if you don't already have this)
RUN apk add --no-cache openssh-client tzdata ca-certificates && update-ca-certificates

# write the restart script straight into the image
RUN cat > /usr/local/bin/restart-airmessage <<'SH'
#!/bin/sh
set -e
# set -x  # uncomment for one-time debugging

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
SH
RUN chmod 755 /usr/local/bin/restart-airmessage

# (optional) pin container timezone; you can also set TZ in compose
ENV TZ=America/Los_Angeles

CMD ["python", "-u", "/cloudflare-ddns.py", "--repeat"]
