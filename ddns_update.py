"""
Poll external IP and update a GoDaddy DNS A record when it changes

Required env vars:
    GODADDY_API_KEY     - from GoDaddy dev portal
    GODADDY_API_SECRET  - from GoDaddy dev portal
    GODADDY_DOMAIN      - e.g. "example.com"
    GODADDY_RECORD_NAME - e.g. "@" for root or "blog" for "blog.example.com"

Optional env vars:
    DDNS_POLL_INTERVAL  - seconds between checks (default 300)
    DDNIS_IP_SERVICE.   - URL returning plain-text IPv4 (default : https://api4.ipify.org)
"""

import os
import time
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

GODADDY_API_BASE = "https://api.godaddy.com/v1"
POLL_INTERVAL = int(os.environ.get("DDNS_POLL_INTERVAL", 300))
IP_SERVICE = os.environ.get("DDNS_IP_SERVICE", "https://api4.ipify.org")

def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required env var not set: {name}")
    return value

def get_external_ip():
    resp = requests.get(IP_SERVICE, timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


def get_current_record(domain, name, headers):
    url = f"{GODADDY_API_BASE}/domains/{domain}/records/A/{name}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    records = resp.json()
    if not records:
        raise RuntimeError(f"No A record found for {name}.{domain}")
    return records[0]["data"]

def update_record(domain, name, ip, headers):
    url = f"{GODADDY_API_BASE}/domains/{domain}/records/A/{name}"
    resp = requests.put(url, json={"data": ip, "ttl": 600}, headers=headers, timeout=10)
    resp.raise_for_status()

def main():
    api_key = require_env("GODADDY_API_KEY")
    api_secret = require_env("GODADDY_API_SECRET")
    domain = require_env("GODADDY_DOMAIN")
    record = require_env("GODADDY_RECORD_NAME")

    headers = {
        "Authorization": f"sso-key {api_key}.{api_secret}",
        "Content-Type": "application/json"
    }

    log.info(f"Starting DDNS monitor for {record}.{domain} (poll every {POLL_INTERVAL} seconds")

    last_ip = None

    while True:
        try:
            current_ip = get_external_ip()
            if current_ip != last_ip:
                dns_ip = get_current_record(domain, record, headers)

                if current_ip != dns_ip:
                    update_record(domain, record, current_ip, headers)
                    log.info(f"Updated {record}.{domain}: {dns_ip} -> {current_ip}")
                else:
                    log.info(f"IP confirmed {current_ip} (no DNS change needed)")
                last_ip = current_ip
        except requests.RequestException as e:
            log.warning(f"Request failed: {e}")
        except Exception as e:
            log.error(f"Unexpected error: {e}")






