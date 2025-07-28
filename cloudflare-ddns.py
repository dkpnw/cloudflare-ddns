#!/usr/bin/env python3
#   cloudflare-ddns.py
#   Summary: Access your home network remotely via a custom domain name without a static IP!
#   Description: Access your home network remotely via a custom domain
#                Access your home network remotely via a custom domain
#                A small, 🕵️ privacy centric, and ⚡
#                lightning fast multi-architecture Docker image for self hosting projects.

__version__ = "1.0.3"

import json
import os
import signal
import sys
import threading
import time
import requests
import subprocess, shlex, json, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo(os.getenv("TZ","UTC"))
CONFIG_PATH = os.environ.get('CONFIG_PATH', os.getcwd())
RESTART_CMD = os.getenv("AIRMESSAGE_RESTART_CMD")
RESTART_COOLDOWN = int(os.getenv("AIRMESSAGE_RESTART_COOLDOWN", "300"))
_last_restart = 0

class GracefulExit:
    def __init__(self):
        self.kill_now = threading.Event()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print("🛑 Stopping main thread...")
        self.kill_now.set()


def deleteEntries(type):
    # Helper function for deleting A or AAAA records
    # in the case of no IPv4 or IPv6 connection, yet
    # existing A or AAAA records are found.
    for option in config["cloudflare"]:
        answer = cf_api(
            "zones/" + option['zone_id'] +
            "/dns_records?per_page=100&type=" + type,
            "GET", option)
        if answer is None or answer["result"] is None:
            time.sleep(5)
            return
        for record in answer["result"]:
            identifier = str(record["id"])
            cf_api(
                "zones/" + option['zone_id'] + "/dns_records/" + identifier,
                "DELETE", option)
            print("🗑️ Deleted stale record " + identifier)


def getIPs():
    a = None
    aaaa = None
    global ipv4_enabled
    global ipv6_enabled
    global purgeUnknownRecords
    if ipv4_enabled:
        try:
            a = requests.get(
                "https://1.1.1.1/cdn-cgi/trace").text.split("\n")
            a.pop()
            a = dict(s.split("=") for s in a)["ip"]
        except Exception:
            global shown_ipv4_warning
            if not shown_ipv4_warning:
                shown_ipv4_warning = True
                print("🧩 IPv4 not detected via 1.1.1.1, trying 1.0.0.1")
            # Try secondary IP check
            try:
                a = requests.get(
                    "https://1.0.0.1/cdn-cgi/trace").text.split("\n")
                a.pop()
                a = dict(s.split("=") for s in a)["ip"]
            except Exception:
                global shown_ipv4_warning_secondary
                if not shown_ipv4_warning_secondary:
                    shown_ipv4_warning_secondary = True
                    print("🧩 IPv4 not detected via 1.0.0.1. Verify your ISP or DNS provider isn't blocking Cloudflare's IPs.")
                if purgeUnknownRecords:
                    deleteEntries("A")
    if ipv6_enabled:
        try:
            aaaa = requests.get(
                "https://[2606:4700:4700::1111]/cdn-cgi/trace").text.split("\n")
            aaaa.pop()
            aaaa = dict(s.split("=") for s in aaaa)["ip"]
        except Exception:
            global shown_ipv6_warning
            if not shown_ipv6_warning:
                shown_ipv6_warning = True
                print("🧩 IPv6 not detected via 1.1.1.1, trying 1.0.0.1")
            try:
                aaaa = requests.get(
                    "https://[2606:4700:4700::1001]/cdn-cgi/trace").text.split("\n")
                aaaa.pop()
                aaaa = dict(s.split("=") for s in aaaa)["ip"]
            except Exception:
                global shown_ipv6_warning_secondary
                if not shown_ipv6_warning_secondary:
                    shown_ipv6_warning_secondary = True
                    print("🧩 IPv6 not detected via 1.0.0.1. Verify your ISP or DNS provider isn't blocking Cloudflare's IPs.")
                if purgeUnknownRecords:
                    deleteEntries("AAAA")
    ips = {}
    if (a is not None):
        ips["ipv4"] = {
            "type": "A",
            "ip": a
        }
    if (aaaa is not None):
        ips["ipv6"] = {
            "type": "AAAA",
            "ip": aaaa
        }
    return ips


def commitRecord(ip):
    global ttl
    
    successes = 0
    failures = 0
    anything_changed = False          # <- master flag

    for option in config["cloudflare"]:
        subdomains   = option["subdomains"]
        zone_id      = option["zone_id"]
        zone_changed = False

        response = cf_api(f"zones/{zone_id}", "GET", option)
        if not (response and response["result"].get("name")):
            time.sleep(5)
            continue

        base_domain_name = response["result"]["name"]

        for subdomain in subdomains:
            try:
                name    = subdomain["name"].lower().strip()
                proxied = subdomain["proxied"]
            except Exception:
                name    = subdomain
                proxied = option["proxied"]

            fqdn = base_domain_name if name in ("", "@") else f"{name}.{base_domain_name}"
            record = {
                "type":    ip["type"],
                "name":    fqdn,
                "content": ip["ip"],
                "proxied": proxied,
                "ttl":     ttl
            }

            dns_records = cf_api(
                f"zones/{zone_id}/dns_records?per_page=100&type={ip['type']}",
                "GET", option)

            identifier = None
            modified   = False
            duplicate_ids = []

            if dns_records:
                for r in dns_records["result"]:
                    if r["name"] == fqdn:
                        if identifier:
                            if r["content"] == ip["ip"]:
                                duplicate_ids.append(identifier)
                                identifier = r["id"]
                            else:
                                duplicate_ids.append(r["id"])
                        else:
                            identifier = r["id"]
                            if (r["content"] != record["content"] or
                                    r["proxied"] != record["proxied"]):
                                modified = True

            # ----- add / update -----------------------------------------
            if identifier:
                if modified:
                    print(f"📡 Updating record {record}")
                    cf_api(f"zones/{zone_id}/dns_records/{identifier}",
                           "PUT", option, {}, record)
                    zone_changed = True
            else:
                print(f"➕ Adding new record {record}")
                cf_api(f"zones/{zone_id}/dns_records", "POST", option, {}, record)
                zone_changed = True

            # ----- purge duplicates ------------------------------------
            if purgeUnknownRecords:
                for dup_id in duplicate_ids:
                    print(f"🗑️ Deleting stale record {dup_id}")
                    cf_api(f"zones/{zone_id}/dns_records/{dup_id}", "DELETE", option)

        # ---- per‑zone heartbeat ---------------------------------------
        if not zone_changed:
            now = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now}  ℹ️  No change needed for {len(subdomains)} "
                  f"subdomains in zone {base_domain_name} ({ip['type']})")

        anything_changed = anything_changed or zone_changed

    return anything_changed

    return True

def updateLoadBalancer(ip):
    """
    Update the address of a Cloudflare Load‑Balancer pool origin
    when the detected WAN IP has changed.

    If the config has no "load_balancer" section, silently skip.
    """
    lb_options = config.get("load_balancer")
    if not lb_options:
        return  # no LB configured → nothing to do

    for option in lb_options:
        try:
            # Fetch all pools in the account
            pools = cf_api("user/load_balancers/pools", "GET", option)
            if not pools or "result" not in pools:
                continue

            # Locate the desired pool
            pool_id = option["pool_id"]
            pool_map = {p["id"]: i for i, p in enumerate(pools["result"])}
            pool_idx = pool_map.get(pool_id)
            if pool_idx is None:
                continue  # pool not found

            origins = pools["result"][pool_idx]["origins"]

            # Locate the desired origin within the pool
            origin_name = option["origin"]
            origin_map = {o["name"]: i for i, o in enumerate(origins)}
            origin_idx = origin_map.get(origin_name)
            if origin_idx is None:
                continue  # origin not found

            # Update the origin's address if it differs
            if origins[origin_idx]["address"] != ip["ip"]:
                origins[origin_idx]["address"] = ip["ip"]
                data = {"origins": origins}

                print(f"📡 Updating LB Pool '{origin_name}' "
                      f"to {ip['ip']} (pool {pool_id})")
                cf_api(f"user/load_balancers/pools/{pool_id}",
                       "PATCH", option, {}, data)

        except Exception as exc:
            print(f"⚠️  Load balancer update error: {exc}")  

def cf_api(endpoint, method, config, headers={}, data=False):
    api_token = config['authentication']['api_token']
    if api_token != '':
        headers = {
            "Authorization": "Bearer " + api_token, **headers
        }
    else:
        headers = {
            "X-Auth-Email": config['authentication']['api_key']['account_email'],
            "X-Auth-Key": config['authentication']['api_key']['api_key'],
        }
    try:
        if (data == False):
            response = requests.request(
                method, "https://api.cloudflare.com/client/v4/" + endpoint, headers=headers)
        else:
            response = requests.request(
                method, "https://api.cloudflare.com/client/v4/" + endpoint,
                headers=headers, json=data)

        if response.ok:
            return response.json()
        else:
            print("😡 Error sending '" + method +
                  "' request to '" + response.url + "':")
            print(response.text)
            return None
    except Exception as e:
        print("😡 An exception occurred while sending '" +
              method + "' request to '" + endpoint + "': " + str(e))
        return None


def updateIPs(ips):
    changed = False
    for ip in ips.values():
        if commitRecord(ip):              # bubbles up True/False
            changed = True
        if "load_balancer" in config:
            updateLoadBalancer(ip)
    return changed
    
def maybe_restart_airmessage():
    """
    Restart AirMessage via the command in AIRMESSAGE_RESTART_CMD,
    but only if the cooldown has elapsed.  Uses a timeout so it
    can never hang the main loop.
    """
    global _last_restart

    if not RESTART_CMD:            # feature disabled
        return

    now = time.time()
    if now - _last_restart < RESTART_COOLDOWN:
        print(f"⏱️  AirMessage restart cooling down ({RESTART_COOLDOWN}s)")
        return

    print("🔁  Restarting AirMessage…")
    try:
        subprocess.run(
            RESTART_CMD,
            shell=True,                 # execute the whole string as‑is
            check=True,
            timeout=30,                 # prevent indefinite hang
            stdout=subprocess.DEVNULL,  # hide ssh output
            stderr=subprocess.PIPE      # capture errors for logging
        )
        _last_restart = now
        print("✅  AirMessage restart succeeded")

    except subprocess.TimeoutExpired:
        print("❌  AirMessage restart FAILED – ssh command timed out (30 s)")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore").strip()
        print(f"❌  AirMessage restart FAILED (exit {e.returncode}): {err}")

    except Exception as e:
        print(f"❌  AirMessage restart FAILED: {e}")


if __name__ == '__main__':
    shown_ipv4_warning = False
    shown_ipv4_warning_secondary = False
    shown_ipv6_warning = False
    shown_ipv6_warning_secondary = False
    ipv4_enabled = True
    ipv6_enabled = True
    purgeUnknownRecords = False

    if sys.version_info < (3, 5):
        raise Exception("🐍 This script requires Python 3.5+")

    config = None
    try:
        with open(os.path.join(CONFIG_PATH, "config.json")) as config_file:
            config = json.loads(config_file.read())
    except:
        print("😡 Error reading config.json")
        # wait 10 seconds to prevent excessive logging on docker auto restart
        time.sleep(10)

    if config is not None:
        try:
            ipv4_enabled = config["a"]
            ipv6_enabled = config["aaaa"]
        except:
            ipv4_enabled = True
            ipv6_enabled = True
            print("⚙️ Individually disable IPv4 or IPv6 with new config.json options. Read more about it here: https://github.com/timothymiller/cloudflare-ddns/blob/master/README.md")
        try:
            purgeUnknownRecords = config["purgeUnknownRecords"]
        except:
            purgeUnknownRecords = False
            print("⚙️ No config detected for 'purgeUnknownRecords' - defaulting to False")
        try:
            ttl = int(config["ttl"])
        except:
            ttl = 300  # default Cloudflare TTL
            print(
                "⚙️ No config detected for 'ttl' - defaulting to 300 seconds (5 minutes)")
        if ttl < 30:
            ttl = 1  #
            print("⚙️ TTL is too low - defaulting to 1 (auto)")
        if (len(sys.argv) > 1):
            if (sys.argv[1] == "--repeat"):
                if ipv4_enabled and ipv6_enabled:
                    print(
                        "🕰️ Updating IPv4 (A) & IPv6 (AAAA) records every " + str(ttl) + " seconds")
                elif ipv4_enabled and not ipv6_enabled:
                    print("🕰️ Updating IPv4 (A) records every " +
                          str(ttl) + " seconds")
                elif ipv6_enabled and not ipv4_enabled:
                    print("🕰️ Updating IPv6 (AAAA) records every " +
                          str(ttl) + " seconds")
                next_time = time.time()
                killer = GracefulExit()
                prev_ips = None
                last_ips = None
                
                while True:
                    ips_this_loop = getIPs()
                    changed = updateIPs(ips_this_loop)

                    # Restart AirMessage only if the WAN IP really changed
                    if changed:
                        maybe_restart_airmessage()
                    else:
                        print("🔸  AirMessage restart not required")
                    
                    last_ips = ips_this_loop.copy()

                    if killer.kill_now.wait(ttl):
                        break
            else:
                print("❓ Unrecognized parameter '" +
                      sys.argv[1] + "'. Stopping now.")
        else:
            updateIPs(getIPs())
