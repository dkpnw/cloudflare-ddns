**Cloudflare DDNS + AirMessage Auto-Restart (Docker)**

This container updates Cloudflare DNS for your changing WAN IP and SSHes into your Mac to bounce AirMessage whenever the IP changes (so iMessage connectivity stays stable).



<big>**Public image: dkpnw/cloudflare-ddns:airmessage-ssh**</big>

No local build required.

Only three files to provide: docker-compose.yml, config.json, and a private SSH key.<br>
<br>Use _example-docker-compose.yml_ and _example-config.json_ as a starting point.

<br>

**Prerequisites**

Docker Desktop (macOS/Windows) or Docker Engine + Compose (Linux)

<br>

**On the Mac that runs AirMessage:**
System Settings → General → Sharing → enable Remote Login for your user

1) Create a project folder
```bash
mkdir -p cloudflare-ddns/secret
cd cloudflare-ddns
```

<br><br>
**2) Create your Cloudflare config**

Create config.json in this folder. Minimal example (IPv4 only; more verbose/optioned config example provided in example-config.json):
```bash
{
  "cloudflare": [
    {
      "authentication": { "api_token": "YOUR_CF_API_TOKEN" },
      "zone_id": "YOUR_ZONE_ID",
      "subdomains": [
        { "name": "home", "proxied": false }
      ]
    }
  ],
  "a": true,
  "aaaa": false,
  "purgeUnknownRecords": false,
  "ttl": 120
}
```
Tip: Put multiple zones in the array if you want to update several domains at once.
proxied: false is recommended for services that expect direct IP access.


<br><br>

**3) Generate an SSH key and authorize it on your Mac**

Generate a dedicated ED25519 key for the container:
```bash
ssh-keygen -t ed25519 -f ./secret/airmessage_rsa -N '' -C 'cf-ddns→AirMessage'
chmod 600 ./secret/airmessage_rsa
```

Add the public half to the Mac user’s authorized keys:

```bash
cat ./secret/airmessage_rsa.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Keep the private key (secret/airmessage_rsa) safe. The container will mount it read-only.


<br><br>

**4) Compose file**

Create docker-compose.yml:
```bash
version: "3.9"
services:
  cloudflare-ddns:
    image: dkpnw/cloudflare-ddns:airmessage-ssh
    pull_policy: always
    container_name: cloudflare-ddns
    network_mode: "host"                     # Docker Desktop (macOS/Windows)
    environment:
      TZ: "America/Los_Angeles"              # optional, for local-time logs
      AIRMESSAGE_SSH_USER: "YOUR_MAC_USERNAME"
      AIRMESSAGE_SSH_HOST: "host.docker.internal"
      AIRMESSAGE_RESTART_COOLDOWN: "10"      # seconds between restarts if needed
      AIRMESSAGE_RESTART_CMD: "/usr/local/bin/restart-airmessage"
      # (optional) customize the remote command:
      # AIRMESSAGE_REMOTE_CMD: "pkill -x AirMessage || true; sleep 5; open -a AirMessage"
    volumes:
      - ./config.json:/config.json:ro
      - ./secret/airmessage_rsa:/ssh/airmessage_rsa:ro
    restart: always
```

<br>
**Linux notes**

If host.docker.internal doesn’t exist, either:

keep network_mode: "host" and set AIRMESSAGE_SSH_HOST=127.0.0.1, or

omit host networking and set AIRMESSAGE_SSH_HOST to your host’s LAN IP.


<br><br>

**5) Start it**
```bash
docker compose up -d
docker compose logs -f
```

You should see your regular DDNS logs (e.g., “No change needed…”). On real IP changes you’ll see Cloudflare updates followed by an AirMessage restart.


<br><br>

**6) Quick tests**

Auth-only check (should print ok):
```bash
docker compose exec cloudflare-ddns \
  ssh -o BatchMode=yes -i /ssh/airmessage_rsa \
  "$AIRMESSAGE_SSH_USER@$AIRMESSAGE_SSH_HOST" 'echo ok'
```
<br>
Force an AirMessage bounce now:
```bash
docker compose exec cloudflare-ddns /usr/local/bin/restart-airmessage
```


<br><br><br>

**7) Updating the container**
```bash
docker compose pull
docker compose up -d
```

With restart: always, it will also come back automatically after host reboots (ensure Docker Desktop is set to “Start at login”).

<br><br>


**Troubleshooting**

_Permission denied (publickey)._<br>
Re-append the public key to ~/.ssh/authorized_keys on the Mac; ensure perms 600.
<br><br>
_Host key verification failed._<br>
The image’s restart helper auto-refreshes host keys each run; if you still see this, ensure you’re using the published image (no local script override) and the command is /usr/local/bin/restart-airmessage.
<br><br>
_Config read error_<br>
Make sure your compose mounts ./config.json:/config.json (exact path) and the JSON is valid.
<br><br>
_No logs after reboot_<br>
Ensure Docker Desktop itself starts at login, and your compose has restart: always.
<br><br><br>



**Advanced (optional)**

Change the restart command with AIRMESSAGE_REMOTE_CMD if your app name/path differs.

Adjust AIRMESSAGE_RESTART_COOLDOWN to rate-limit restarts on flappy connections.

Set your own time zone via TZ for local timestamps in logs.


<br><br>

**Security notes**

The container uses public-key only SSH with BatchMode=yes (no password prompts).

It refreshes host keys automatically, so OS updates on the Mac won’t break the SSH step.

Keep your private key in secret/airmessage_rsa safe; never commit it to version control.

That’s it—drop in config.json, generate the key, set your username in the compose file, and you’re live.
