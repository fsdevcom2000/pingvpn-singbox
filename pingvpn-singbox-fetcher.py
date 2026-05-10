#!/usr/bin/env python3

"""
PingVPN to sing-box proxy fetcher

Automatically fetches free proxy servers from PingVPN API and generates
sing-box config with urltest for fastest node selection.

Usage:
    python3 pingvpn-singbox-updater.py

Config:
    config.yaml in the same directory with paths, DNS and TUN settings.

Requirements:
    sing-box installed, systemd service running.

Author: fsdevcom2000

URL: https://github.com/fsdevcom2000/pingvpn-singbox/

"""

import json
import requests
import tempfile
import os
import subprocess
import logging
import yaml
import time
from logging.handlers import RotatingFileHandler

API_HOST = "https://api-2.pingvpn.com"
APP_ID = "1"


# PINGVPN CLIENT
session = requests.Session()


def get_latest_chrome_user_agent():
    url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
    try:
        data = requests.get(url, timeout=5).json()
        version = data["channels"]["Stable"]["version"]
        return (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{version} Safari/537.36"
        )
    except Exception:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

session.headers.update({
    "User-Agent": get_latest_chrome_user_agent()
})


def safe_post(url, **kwargs):
    try:
        resp = session.post(url, timeout=10, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}")


def safe_get(url, **kwargs):
    try:
        resp = session.get(url, timeout=10, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}")


def get_ping_vpn_servers():
    signup_url = f"{API_HOST}/v2/{APP_ID}/private/user/customer/sign_up/free"
    token_url = f"{API_HOST}/v2/token"
    list_url = f"{API_HOST}/v2/{APP_ID}/private/user/customer/vpn_list"

    signup = safe_post(signup_url, json={"email": "", "first_name": "", "last_name": ""})
    customer_id = signup.get("customer_id")
    if not customer_id:
        raise RuntimeError("customer_id missing in signup response")

    token = safe_post(token_url, data={"customer_id": customer_id})
    access_token = token.get("access_token")
    if not access_token:
        raise RuntimeError("access_token missing in token response")

    servers = safe_get(list_url, headers={"Authorization": f"Bearer {access_token}"})
    return servers


# YAML CONFIG
def load_yaml_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


# LOGGING
def setup_logging(log_path):
    logger = logging.getLogger("updater")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(fmt)

    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

    return logger


# BUILD SING-BOX CONFIG (ALL PINGVPN NODES)
def build_config(nodes, dns, tun):
    outbounds = [
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
    ]

    tags = []

    for i, n in enumerate(nodes):
        tag = f"n{i}"
        tags.append(tag)

        outbounds.append({
            "type": "http",
            "tag": tag,
            "server": n["server"],
            "server_port": n["server_port"],
            "username": n["username"],
            "password": n["password"]
        })

    outbounds.append({
        "type": "urltest",
        "tag": "proxy",
        "outbounds": tags,
        "url": "http://www.gstatic.com/generate_204",
        "interval": "60s",
        "tolerance": 50,
        "interrupt_exist_connections": True
    })

    return {
        "log": {"level": "info"},
        "dns": {"servers": dns},
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun",
                **tun
            }
        ],
        "outbounds": outbounds,
        "route": {
            "final": "proxy",
            "default_domain_resolver": dns[0]["tag"]
        }
    }



# WRITE CONFIG + CHECK
def write(cfg, config_path, log):
    f = tempfile.NamedTemporaryFile(delete=False, mode="w")
    json.dump(cfg, f, indent=2)
    f.close()

    r = subprocess.run(
        ["sing-box", "check", "-c", f.name],
        capture_output=True
    )

    if r.returncode != 0:
        log.error(r.stderr.decode())
        os.unlink(f.name)
        return False

    os.replace(f.name, config_path)
    return True


# RESTART SERVICE
def restart_service(service, log, timeout=10):
    log.info(f"[+] restarting service: {service}")

    r = subprocess.run(["systemctl", "restart", service])
    if r.returncode != 0:
        log.error(f"failed to restart {service}")
        return False

    for i in range(timeout):
        status = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True
        )

        if status.stdout.strip() == "active":
            log.info(f"[+] service {service} is running")
            return True

        time.sleep(1)

    log.error(f"service {service} did not start within {timeout}s")


    status_full = subprocess.run(
        ["systemctl", "status", service],
        capture_output=True,
        text=True
    )
    log.error(status_full.stdout)

    return False

# MAIN
def main():
    cfg = load_yaml_config()

    CONFIG_PATH = cfg["paths"]["config"]
    LOG_PATH = cfg["paths"]["log"]
    SERVICE = cfg["service"]
    DNS = cfg["dns"]
    TUN = cfg["tun"]

    log = setup_logging(LOG_PATH)

    log.info("[+] fetching PingVPN nodes")

    try:
        raw = get_ping_vpn_servers()
    except Exception as e:
        log.error(f"PingVPN error: {e}")
        return

    if not raw or "regions" not in raw:
        log.error("no nodes received")
        return

    regions = raw["regions"]
    log.info(f"[+] total nodes: {len(regions)}")

    nodes = []
    for r in regions:
        nodes.append({
            "server": r["ip_address"],
            "server_port": r["squid_default_port"],
            "username": r["username"],
            "password": r["password"]
        })

    log.info("[+] building config")
    cfg_json = build_config(nodes, DNS, TUN)

    log.info("[+] writing config")
    if not write(cfg_json, CONFIG_PATH, log):
        return

    if not restart_service(SERVICE, log):
        log.error("[!] service restart failed")
        return

    log.info("[+] done")


if __name__ == "__main__":
    main()
