#!/usr/bin/env python3
# cloudflare-ddns.py
# Summary: Access your home network remotely via a custom domain name without a static IP!

__version__ = "1.0.2"

import json
import os
import signal
import sys
import threading
import time
import requests
from string import Template

# Global warning flags for IPv4 and IPv6
shown_ipv4_warning = False
shown_ipv4_warning_secondary = False
shown_ipv6_warning = False
shown_ipv6_warning_secondary = False

CONFIG_PATH = os.environ.get('CONFIG_PATH', os.getcwd())
ENV_VARS = {key: value for (key, value) in os.environ.items() if key.startswith('CF_DDNS_')}

class GracefulExit:
    def __init__(self):
        self.kill_now = threading.Event()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print("🛑 Stopping main thread...")
        self.kill_now.set()

def deleteEntries(type):
    for option in config["cloudflare"]:
        answer = cf_api(f"zones/{option['zone_id']}/dns_records?per_page=100&type={type}", "GET", option)
        if answer and answer.get("result"):
            for record in answer["result"]:
                identifier = record["id"]
                cf_api(f"zones/{option['zone_id']}/dns_records/{identifier}", "DELETE", option)
                print(f"🗑️ Deleted stale record {identifier}")

def getIPs():
    ips = {}
    # IPv4 Handling
    if ipv4_enabled:
        try:
            a = fetchIP("https://1.1.1.1/cdn-cgi/trace")
            print(f"✅ Detected IPv4: {a}")
            ips["ipv4"] = {"type": "A", "ip": a}
        except Exception:
            print("🧩 IPv4 not detected. Trying backup...")
            try:
                a = fetchIP("https://1.0.0.1/cdn-cgi/trace")
                print(f"✅ Detected IPv4 from backup: {a}")
                ips["ipv4"] = {"type": "A", "ip": a}
            except Exception:
                print("🧩 IPv4 not detected via backup. Verify your ISP or DNS provider.")
                if purgeUnknownRecords:
                    deleteEntries("A")
    else:
        print("⚙️ IPv4 is disabled in the configuration. Skipping IPv4 operations.")

    # IPv6 Handling
    if ipv6_enabled:
        try:
            aaaa = fetchIP("https://[2606:4700:4700::1111]/cdn-cgi/trace")
            print(f"✅ Detected IPv6: {aaaa}")
            ips["ipv6"] = {"type": "AAAA", "ip": aaaa}
        except Exception:
            print("🧩 IPv6 not detected. Trying backup...")
            try:
                aaaa = fetchIP("https://[2606:4700:4700::1001]/cdn-cgi/trace")
                print(f"✅ Detected IPv6 from backup: {aaaa}")
                ips["ipv6"] = {"type": "AAAA", "ip": aaaa}
            except Exception:
                print("🧩 IPv6 not detected via backup. Verify your ISP or DNS provider.")
                if purgeUnknownRecords:
                    deleteEntries("AAAA")
    else:
        print("⚙️ IPv6 is disabled in the configuration. Skipping IPv6 operations.")

    return ips

def fetchIP(url):
    response = requests.get(url).text.split("\n")
    response.pop()
    return dict(s.split("=") for s in response)["ip"]

def handleIPError(ip_type, record_type):
    if ip_type == "IPv6" and not ipv6_enabled:
        return  # Skip logging or actions for disabled IPv6
    print(f"🧩 {ip_type} not detected. Verify your ISP or DNS provider isn't blocking Cloudflare.")
    if purgeUnknownRecords:
        deleteEntries(record_type)

def commitRecord(ip):
    global ttl
    for option in config["cloudflare"]:
        subdomains = option["subdomains"]
        response = cf_api(f"zones/{option['zone_id']}", "GET", option)
        if response and response.get("result"):
            base_domain_name = response["result"]["name"]
            for subdomain in subdomains:
                fqdn, record = prepareDNSRecord(subdomain, base_domain_name, ip, option)
                try:
                    processDNSRecord(fqdn, record, ip["type"], option)
                    print(f"✅ Successfully updated {ip['type']} record for {fqdn} to {ip['ip']}")
                except Exception as e:
                    print(f"❌ Failed to update {ip['type']} record for {fqdn}: {e}")

def prepareDNSRecord(subdomain, base_domain_name, ip, option):
    name = subdomain.get("name", subdomain).strip().lower()
    proxied = subdomain.get("proxied", option.get("proxied", False))  # Use default False if not set
    fqdn = f"{name}.{base_domain_name}" if name and name != '@' else base_domain_name
    record = {"type": ip["type"], "name": fqdn, "content": ip["ip"], "proxied": proxied, "ttl": ttl}
    return fqdn, record

def processDNSRecord(fqdn, record, record_type, option):
    dns_records = cf_api(f"zones/{option['zone_id']}/dns_records?per_page=100&type={record_type}", "GET", option)
    if dns_records and dns_records.get("result"):
        identifier = None
        modified = False
        for r in dns_records["result"]:
            if r["name"] == fqdn:
                identifier = r["id"]
                modified = r['content'] != record['content'] or r['proxied'] != record['proxied']
        if identifier and modified:
            print(f"📡 Updating record {record}")
            cf_api(f"zones/{option['zone_id']}/dns_records/{identifier}", "PUT", option, {}, record)
        elif not identifier:
            print(f"➕ Adding new record {record}")
            cf_api(f"zones/{option['zone_id']}/dns_records", "POST", option, {}, record)

def cf_api(endpoint, method, config, headers={}, data=None):
    headers = buildHeaders(config)
    url = f"https://api.cloudflare.com/client/v4/{endpoint}"
    try:
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"😡 Error with {method} request to {url}: {e}")
        return None

def buildHeaders(config):
    if "api_token" in config["authentication"]:
        return {"Authorization": f"Bearer {config['authentication']['api_token']}"}
    else:
        return {
            "X-Auth-Email": config["authentication"]["api_key"]["account_email"],
            "X-Auth-Key": config["authentication"]["api_key"]["api_key"],
        }

def updateIPs(ips):
    print(f"🔄 Updating IPs: {ips}")
    for ip in ips.values():
        try:
            commitRecord(ip)
            print(f"✅ Successfully updated {ip['type']} record to {ip['ip']}")
        except Exception as e:
            print(f"❌ Failed to update {ip['type']} record: {e}")

if __name__ == '__main__':
    print("🚀 Starting Cloudflare DDNS Updater")
    if sys.version_info < (3, 5):
        raise Exception("🐍 This script requires Python 3.5+")

    ipv4_enabled = True
    ipv6_enabled = True
    purgeUnknownRecords = False

    try:
        with open(os.path.join(CONFIG_PATH, "config.json")) as config_file:
            config_content = config_file.read()
            config = json.loads(Template(config_content).safe_substitute(ENV_VARS))
            print("✅ Config loaded successfully")
    except Exception as e:
        print(f"😡 Error loading config.json: {e}")
        time.sleep(10)
        sys.exit(1)

    ttl = config.get("ttl", 300)
    ttl = max(ttl, 1)
    print(f"🔄 TTL set to {ttl} seconds")

    killer = GracefulExit()
    while not killer.kill_now.is_set():
        try:
            ips = getIPs()
            updateIPs(ips)
            # Wait for the specified TTL or until a stop signal is received
            killer.kill_now.wait(ttl)
        except KeyboardInterrupt:
            killer.kill_now.set()
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(10)

    print("🛑 Shutting down Cloudflare DDNS Updater.")


