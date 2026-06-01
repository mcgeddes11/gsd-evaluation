"""
Poll external IP and update a DNS A record when it changes

Required env vars:
-- GODADDY --
    DDNS_PROVIDER = godaddy
    GODADDY_API_KEY     - from GoDaddy dev portal
    GODADDY_API_SECRET  - from GoDaddy dev portal
    GODADDY_DOMAIN      - e.g. "example.com"
    GODADDY_RECORD_NAME - e.g. "@" for root or "blog" for "blog.example.com"

-- Cloudflare
    DDNS_PROVIDER = cloudflare
    CLOUDFLARE_API_TOKEN - scoped to Zone:DNS:Edit for the target zone
    DDNS_DOMAIN          - e.g. "example.com"
    DDNS_RECORD_NAME     - e.g. "@" for root


Optional env vars:
    DDNS_POLL_INTERVAL  - seconds between checks (default 300)
    DDNIS_IP_SERVICE.   - URL returning plain-text IPv4 (default : https://api4.ipify.org)
"""

import os
import time
import logging
import requests
from pkg_resources import require

logging.basicConfig(
    level=logging.INFO,
    format="(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

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


# GODADDY

class GoDaddyProvider:
    API_BASE = "https://api.godaddy.com/v1"


    def __init__(self):
        self.domain = require_env("DDNS_DOMAIN")
        self.record = require_env("DDNS_RECORD_NAME")
        self.headers = {
            "Authorization": f"sso-key {require_env("GODADDY_API_KEY")}:{require_env("GODADDY_API_SECRET")}",
            "Content-Type": "application/json"
        }

    def get_current_ip(self):
        url = f"{self.API_BASE}/domains/{self.domain}/records/A/{self.name}"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        records = resp.json()
        if not records:
            raise RuntimeError(f"No A record found for {self.record}.{self.domain}")
        return records[0]["data"]

    def set_ip(self, ip):
        url = f"{self.API_BASE}/domains/{self.domain}/records/A/{self.record}"
        resp = requests.put(url, json={"data": ip, "ttl": 600}, headers=self.headers, timeout=10)
        resp.raise_for_status()

    def label(self):
        return f"{self.record}.{self.domain} (GoDaddy)"


class CloudFlareProvider:
    API_BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self):
        self.domain = require_env("DDNS_DOMAIN")
        self.record = require_env("DDNS_RECORD_NAME")
        self.headers = {
            "Authorization": f"Bearer {require_env("CLOUDFLARE_API_TOKEN")}",
            "Content-Type": "application/json"
        }
        self._zone_id = None
        self._record_id = None


    def _get_zone_id(self):
        if self._zone_id:
            return self._zone_id
        resp = requests.get(
            f"{self.API_BASE}/zones",
            headers=self.headers,
            params={"name": self.domain},
            timeout=10
        )
        resp.raise_for_status()
        zones = resp.json().get("result", [])
        if not zones:
            raise RuntimeError(f"No CloudFlare zones for domain: {self.domain}")
        self._zone_id = zones[0]["id"]
        return self._zone_id

    def _get_record(self):
        record_name = self.domain if self.record == "@" else f"{self.record}.{self.domain}"
        resp = requests.get(
            f"{self.API_BASE}/zones/{self._get_zone_id()}/dns_records",
            headers=self.headers,
            params={"type": "A", "name": record_name},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        if not results:
            raise RuntimeError(f"No A record found for {record_name}")
        return results[0]

    def get_current_ip(self):
        return self._get_record()["content"]

    def set_ip(self, ip):
        record = self._get_record()
        resp = requests.patch(
            f"{self.API_BASE}/zones/{self._get_zone_id()}/dns_records/{record["id"]}",
            headers=self.headers,
            json={"content": ip},
            timeout=10,
        )

    def label(self):
        return f"{self.record}.{self.domain} (CloudFlare)"

## MAIN
PROVIDERS = {
    "godaddy": GoDaddyProvider,
    "cloudflare": CloudFlareProvider
}

def main():
    provider_name = require_env("DDNS_PROVIDER").lower()
    if provider_name not in PROVIDERS:
        raise RuntimeError(f"Unknown DDNS_PROVIDER {provider_name}. Choose {",".join(PROVIDERS)}")
    provider = PROVIDERS[provider_name]()

    log.info(f"Starting DDNS monitor for {provider.lower()} (poll every {POLL_INTERVAL}s)")
    last_ip = None

    while True:
        try:
            current_ip = get_external_ip()
            if current_ip != last_ip:
                dns_ip = provider.get_current_ip()

                if current_ip != dns_ip:
                    provider.set_ip(current_ip)
                    log.info(f"Updated {provider.label}: {dns_ip} -> {current_ip}")
                else:
                    log.info(f"IP confirmed {current_ip} (no DNS change needed)")
                last_ip = current_ip
        except requests.RequestException as e:
            log.warning(f"Request failed: {e}")
        except Exception as e:
            log.error(f"Unexpected error: {e}")

