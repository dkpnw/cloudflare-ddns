# Dockerfile (local build)
FROM python:3.13-alpine

# SSH client for restarts + local time support
RUN apk add --no-cache openssh-client tzdata ca-certificates && update-ca-certificates

# Python deps used by the script
RUN pip install --no-cache-dir requests

# Keep WORKDIR at / so CONFIG_PATH="/" + /config.json works
WORKDIR /

# App file
COPY cloudflare-ddns.py /cloudflare-ddns.py

# Defaults; TZ can be overridden by compose
ENV TZ=America/Los_Angeles

ENTRYPOINT ["python","-u","/cloudflare-ddns.py","--repeat"]
