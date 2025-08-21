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

# (optional) pin container timezone; you can also set TZ in compose
ENV TZ=America/Los_Angeles

CMD ["python", "-u", "/cloudflare-ddns.py", "--repeat"]
