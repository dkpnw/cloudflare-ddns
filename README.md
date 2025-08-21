<p align="center"><a href="https://timknowsbest.com/free-dynamic-dns" target="_blank" rel="noopener noreferrer"><img width="1024" src="feature-graphic.jpg" alt="Cloudflare DDNS"/></a></p>

# 🚀 Cloudflare DDNS

Access your home network remotely via a custom domain name without a static IP!

## ⚡ Efficiency

- ❤️ Easy config. List your domains and you're done.
- 🔁 The Python runtime will re-use existing HTTP connections.
- 🗃️ Cloudflare API responses are cached to reduce API usage.
- 🤏 The Docker image is small and efficient.
- 0️⃣ Zero dependencies.
- 💪 Supports all platforms.
- 🏠 Enables low cost self hosting to promote a more decentralized internet.
- 🔒 Zero-log IP provider ([cdn-cgi/trace](https://www.cloudflare.com/cdn-cgi/trace))
- 👐 GPL-3.0 License. Open source for open audits.

## 💯 Complete Support of Domain Names, Subdomains, IPv4 & IPv6, and Load Balancing

- 🌐 Supports multiple domains (zones) on the same IP.
- 📠 Supports multiple subdomains on the same IP.
- 📡 IPv4 and IPv6 support.
- 🌍 Supports all Cloudflare regions.
- ⚖️ Supports [Cloudflare Load Balancing](https://developers.cloudflare.com/load-balancing/understand-basics/pools/).
- 🇺🇸 Made in the U.S.A.

## 📊 Stats

| Size                                                                                                                                                                                                                           | Downloads                                                                                                                                                                                         | Discord                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [![cloudflare-ddns docker image size](https://img.shields.io/docker/image-size/timothyjmiller/cloudflare-ddns?style=flat-square)](https://hub.docker.com/r/timothyjmiller/cloudflare-ddns 'cloudflare-ddns docker image size') | [![Total DockerHub pulls](https://img.shields.io/docker/pulls/timothyjmiller/cloudflare-ddns?style=flat-square)](https://hub.docker.com/r/timothyjmiller/cloudflare-ddns 'Total DockerHub pulls') | [![Official Discord Server](https://img.shields.io/discord/785778163887112192?style=flat-square)](https://discord.gg/UgGmwMvNxm 'Official Discord Server') |

## 🚦 Getting Started

First copy the example configuration file into the real one.

```bash
cp example-config.json config.json
```

Edit `config.json` and replace the values with your own.

### 🔑 Authentication methods

You can choose to use either the newer API tokens, or the traditional API keys

To generate a new API tokens, go to your [Cloudflare Profile](https://dash.cloudflare.com/profile/api-tokens) and create a token capable of **Edit DNS**. Then replace the value in

```json
"authentication":
  "api_token": "Your cloudflare API token, including the capability of **Edit DNS**"
```

Alternatively, you can use the traditional API keys by setting appropriate values for:

```json
"authentication":
  "api_key":
    "api_key": "Your cloudflare API Key",
    "account_email": "The email address you use to sign in to cloudflare",
```

### 📍 Enable or disable IPv4 or IPv6

Some ISP provided modems only allow port forwarding over IPv4 or IPv6. In this case, you would want to disable any interface not accessible via port forward.

```json
"a": true,
"aaaa": true
```

### 🎛️ Other values explained

```json
"zone_id": "The ID of the zone that will get the records. From your dashboard click into the zone. Under the overview tab, scroll down and the zone ID is listed in the right rail",
"subdomains": "Array of subdomains you want to update the A & where applicable, AAAA records. IMPORTANT! Only write subdomain name. Do not include the base domain name. (e.g. foo or an empty string to update the base domain)",
"proxied": "Defaults to false. Make it true if you want CDN/SSL benefits from cloudflare. This usually disables SSH)",
"ttl": "Defaults to 300 seconds. Longer TTLs speed up DNS lookups by increasing the chance of cached results, but a longer TTL also means that updates to your records take longer to go into effect. You can choose a TTL between 30 seconds and 1 day. For more information, see [Cloudflare's TTL documentation](https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/)",
```

## 📠 Hosting multiple subdomains on the same IP?

This script can be used to update multiple subdomains on the same IP address.

For example, if you have a domain `example.com` and you want to host additional subdomains at `foo.example.com` and `bar.example.com` on the same IP address, you can use this script to update the DNS records for all subdomains.

### ⚠️ Note

Please remove the comments after `//` in the below example. They are only there to explain the config.

Do not include the base domain name in your `subdomains` config. Do not use the [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name).

### 👉 Example 🚀

```bash
{
  "cloudflare": [
    {
      "authentication": {
        "api_token": "api_token_here", // Either api_token or api_key
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "zone_id": "your_zone_id_here",
      "subdomains": [
        {
          "name": "", // Root domain (example.com)
          "proxied": true
        },
        {
          "name": "foo", // (foo.example.com)
          "proxied": true
        },
        {
          "name": "bar", // (bar.example.com)
          "proxied": true
        }
      ]
    }
  ],
  "a": true,
  "aaaa": true,
  "purgeUnknownRecords": false,
  "ttl": 300
}
```

## 🌐 Hosting multiple domains (zones) on the same IP?

You can handle ddns for multiple domains (cloudflare zones) using the same docker container by duplicating your configs inside the `cloudflare: []` key within `config.json` like below:

### ⚠️ Note:

If you are using API Tokens, make sure the token used supports editing your zone ID.

```bash
{
  "cloudflare": [
    {
      "authentication": {
        "api_token": "api_token_here",
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "zone_id": "your_first_zone_id_here",
      "subdomains": [
        {
          "name": "",
          "proxied": false
        },
        {
          "name": "remove_or_replace_with_your_subdomain",
          "proxied": false
        }
      ]
    },
    {
      "authentication": {
        "api_token": "api_token_here",
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "zone_id": "your_second_zone_id_here",
      "subdomains": [
        {
          "name": "",
          "proxied": false
        },
        {
          "name": "remove_or_replace_with_your_subdomain",
          "proxied": false
        }
      ]
    }
  ],
  "a": true,
  "aaaa": true,
  "purgeUnknownRecords": false
}
```

## ⚖️ Load Balancing

If you have multiple IP addresses and want to load balance between them, you can use the `loadBalancing` option. This will create a CNAME record for each subdomain that points to the subdomain with the lowest IP address.

### 📜 Example config to support load balancing

```json
{
  "cloudflare": [
    {
      "authentication": {
        "api_token": "api_token_here",
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "zone_id": "your_zone_id_here",
      "subdomains": [
        {
          "name": "",
          "proxied": false
        },
        {
          "name": "remove_or_replace_with_your_subdomain",
          "proxied": false
        }
      ]
    }
  ],{
  "cloudflare": [
    {
      "authentication": {
        "api_token": "api_token_here",
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "zone_id": "your_zone_id_here",
      "subdomains": [
        {
          "name": "",
          "proxied": false
        },
        {
          "name": "remove_or_replace_with_your_subdomain",
          "proxied": false
        }
      ]
    }
  ],
  "load_balancer": [
    {
      "authentication": {
        "api_token": "api_token_here",
        "api_key": {
          "api_key": "api_key_here",
          "account_email": "your_email_here"
        }
      },
      "pool_id": "your_pool_id_here",
      "origin": "your_origin_name_here"
    }
  ],
  "a": true,
  "aaaa": true,
  "purgeUnknownRecords": false,
  "ttl": 300
}
```

### 🧹 Optional features

`purgeUnknownRecords` removes stale DNS records from Cloudflare. This is useful if you have a dynamic DNS record that you no longer want to use. If you have a dynamic DNS record that you no longer want to use, you can set `purgeUnknownRecords` to `true` and the script will remove the stale DNS record from Cloudflare.

## 🐳 Deploy with Docker Compose

Pre-compiled images are available via [the official docker container on DockerHub](https://hub.docker.com/r/timothyjmiller/cloudflare-ddns).

Modify the host file path of config.json inside the volumes section of docker-compose.yml.

```yml
version: '3.9'
services:
  cloudflare-ddns:
    image: timothyjmiller/cloudflare-ddns:latest
    container_name: cloudflare-ddns
    security_opt:
      - no-new-privileges:true
    network_mode: 'host'
    environment:
      - PUID=1000
      - PGID=1000
    volumes:
      - /YOUR/PATH/HERE/config.json:/config.json
    restart: unless-stopped
```

### ⚠️ IPv6

Docker requires network_mode be set to host in order to access the IPv6 public address.

### 🏃‍♂️ Running

From the project root directory

```bash
docker-compose up -d
```

## 🐋 Kubernetes

Create config File

```bash
cp ../../config-example.json config.json
```

Edit config.jsonon (vim, nvim, nano... )

```bash
${EDITOR} config.json
```

Create config file as Secret.

```bash
kubectl create secret generic config-cloudflare-ddns --from-file=config.json --dry-run=client -oyaml -n ddns > config-cloudflare-ddns-Secret.yaml
```

apply this secret

```bash
kubectl apply -f config-cloudflare-ddns-Secret.yaml
rm config.json # recomended Just keep de secret on Kubernetes Cluster
```

apply this Deployment

```bash
kubectl apply -f cloudflare-ddns-Deployment.yaml
```

## 🐧 Deploy with Linux + Cron

### 🏃 Running (all distros)

This script requires Python 3.5+, which comes preinstalled on the latest version of Raspbian. Download/clone this repo and give permission to the project's bash script by running `chmod +x ./start-sync.sh`. Now you can execute `./start-sync.sh`, which will set up a virtualenv, pull in any dependencies, and fire the script.

1. Upload the cloudflare-ddns folder to your home directory /home/your_username_here/

2. Run the following code in terminal

```bash
crontab -e
```

3. Add the following lines to sync your DNS records every 15 minutes

```bash
*/15 * * * * /home/your_username_here/cloudflare-ddns/start-sync.sh
```

## Building from source

Create a config.json file with your production credentials.

##Cloudflare DDNS + AirMessage Auto-Restart (Docker)

This container updates Cloudflare DNS for your changing WAN IP and SSHes into your Mac to bounce AirMessage whenever the IP changes (so iMessage connectivity stays stable).

Public image: dkpnw/cloudflare-ddns:airmessage-ssh

No local build required.

Only two files to provide: config.json (Cloudflare) and a private SSH key.

Prerequisites

Docker Desktop (macOS/Windows) or Docker Engine + Compose (Linux)

On the Mac that runs AirMessage:
System Settings → General → Sharing → enable Remote Login for your user

1) Create a project folder
mkdir -p cloudflare-ddns/secret
cd cloudflare-ddns

2) Create your Cloudflare config

Create config.json in this folder. Minimal example (IPv4 only):

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


Tip: Put multiple zones in the array if you want to update several domains at once.
proxied: false is recommended for services that expect direct IP access.

3) Generate an SSH key and authorize it on your Mac

Generate a dedicated ED25519 key for the container:

ssh-keygen -t ed25519 -f ./secret/airmessage_rsa -N '' -C 'cf-ddns→AirMessage'
chmod 600 ./secret/airmessage_rsa


Add the public half to the Mac user’s authorized keys:

cat ./secret/airmessage_rsa.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys


Keep the private key (secret/airmessage_rsa) safe. The container will mount it read-only.

4) Compose file

Create docker-compose.yml:

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


Linux notes

If host.docker.internal doesn’t exist, either:

keep network_mode: "host" and set AIRMESSAGE_SSH_HOST=127.0.0.1, or

omit host networking and set AIRMESSAGE_SSH_HOST to your host’s LAN IP.

5) Start it
docker compose up -d
docker compose logs -f


You should see your regular DDNS logs (e.g., “No change needed…”). On real IP changes you’ll see Cloudflare updates followed by an AirMessage restart.

6) Quick tests

Auth-only check (should print ok):

docker compose exec cloudflare-ddns \
  ssh -o BatchMode=yes -i /ssh/airmessage_rsa \
  "$AIRMESSAGE_SSH_USER@$AIRMESSAGE_SSH_HOST" 'echo ok'


Force an AirMessage bounce now:

docker compose exec cloudflare-ddns /usr/local/bin/restart-airmessage

7) Updating the container
docker compose pull
docker compose up -d


With restart: always, it will also come back automatically after host reboots (ensure Docker Desktop is set to “Start at login”).

Troubleshooting

Permission denied (publickey).
Re-append the public key to ~/.ssh/authorized_keys on the Mac; ensure perms 600.

Host key verification failed.
The image’s restart helper auto-refreshes host keys each run; if you still see this, ensure you’re using the published image (no local script override) and the command is /usr/local/bin/restart-airmessage.

Config read error
Make sure your compose mounts ./config.json:/config.json (exact path) and the JSON is valid.

No logs after reboot
Ensure Docker Desktop itself starts at login, and your compose has restart: always.

Advanced (optional)

Change the restart command with AIRMESSAGE_REMOTE_CMD if your app name/path differs.

Adjust AIRMESSAGE_RESTART_COOLDOWN to rate-limit restarts on flappy connections.

Set your own time zone via TZ for local timestamps in logs.

Security notes

The container uses public-key only SSH with BatchMode=yes (no password prompts).

It refreshes host keys automatically, so OS updates on the Mac won’t break the SSH step.

Keep your private key in secret/airmessage_rsa safe; never commit it to version control.

That’s it—drop in config.json, generate the key, set your username in the compose file, and you’re live.

### 💖 Please Note

The optional `docker-build-all.sh` script requires Docker experimental support to be enabled.

Docker Hub has experimental support for multi-architecture builds. Their official blog post specifies easy instructions for building with [Mac and Windows versions of Docker Desktop](https://docs.docker.com/docker-for-mac/multi-arch/).

1. Choose build platform

- Multi-architecture (experimental) `docker-build-all.sh`

- Linux/amd64 by default `docker-build.sh`

2. Give your bash script permission to execute.

```bash
sudo chmod +x ./docker-build.sh
```

```bash
sudo chmod +x ./docker-build-all.sh
```

3. At project root, run the `docker-build.sh` script.

Recommended for local development

```bash
./docker-build.sh
```

Recommended for production

```bash
./docker-build-all.sh
```

### Run the locally compiled version

```bash
docker run -d timothyjmiller/cloudflare_ddns:latest
```

## Supported Platforms

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Kubernetes](https://kubernetes.io/docs/tasks/tools/)
- [Python 3](https://www.python.org/downloads/)
- [Systemd](https://www.freedesktop.org/wiki/Software/systemd/)

## 📜 Helpful links

- [Cloudflare API token](https://dash.cloudflare.com/profile/api-tokens)
- [Cloudflare zone ID](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-IP-address-)
- [Cloudflare zone DNS record ID](https://support.cloudflare.com/hc/en-us/articles/360019093151-Managing-DNS-records-in-Cloudflare)

## License

This Template is licensed under the GNU General Public License, version 3 (GPLv3).

## Author

Timothy Miller, forked and customized by Drew Pine (using GPT-o3 and 5)

[View my GitHub profile 💡](https://github.com/timothymiller)

[View my personal website 💻](https://timknowsbest.com)
    
    
AirMessage Restarter Instructions (Added by Drew Pine https://github.com/dkpnw)
