#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import urllib.request
import tarfile
import zipfile
import json
import re
from urllib.parse import urlparse
from datetime import datetime
import socket

GITHUB_API_RELEASES = "https://api.github.com/repos/xmrig/xmrig/releases/latest"

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

def detect_system():
    os_name = platform.system().lower()
    arch_map = {
        'x86_64': 'x64', 'amd64': 'x64',
        'i386': 'x86', 'i686': 'x86',
        'aarch64': 'arm64', 'arm64': 'arm64'
    }
    arch = arch_map.get(platform.machine().lower(), 'x64')

    ubuntu_codename = ""
    if os_name == "linux":
        try:
            with open("/etc/os-release") as f:
                m = re.search(r'VERSION_CODENAME=(\w+)', f.read())
                if m:
                    ubuntu_codename = m.group(1)
        except:
            pass
    return os_name, arch, ubuntu_codename

def parse_xmrig_version(output):
    m = re.search(r'\b\d+\.\d+\.\d+\b', output)
    return m.group(0) if m else None

def search_xmrig(search_dir):
    for root, _, files in os.walk(search_dir):
        for name in files:
            if name.lower() in ('xmrig', 'xmrig.exe'):
                path = os.path.join(root, name)
                try:
                    output = subprocess.check_output([path, "--version"], text=True)
                    version = parse_xmrig_version(output)
                    if version:
                        return version
                except:
                    continue
    return None

def fetch_latest_github_release():
    with urllib.request.urlopen(GITHUB_API_RELEASES) as resp:
        data = json.load(resp)
        version = data["tag_name"].lstrip("v")
        assets = data.get("assets", [])
        return version, assets

def select_asset(assets, os_name, arch, ubuntu_codename=""):
    candidates = []
    if os_name == "linux":
        if ubuntu_codename:
            candidates.append(f"{ubuntu_codename}-{arch}")
        candidates.append(f"noble-{arch}")
        candidates.append(f"static-{arch}")
    elif os_name == "windows":
        candidates.append(f"windows-{arch}")
    elif os_name == "macos":
        candidates.append(f"macos-{arch}")
    else:
        die(f"Unsupported OS: {os_name}")

    for suffix in candidates:
        for asset in assets:
            if suffix in asset["name"]:
                return asset["browser_download_url"]
    die("No suitable asset found for your system.")

def download_and_extract(url, dest_dir):
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(dest_dir, filename)
    print(f"Downloading {filename}...")
    urllib.request.urlretrieve(url, filepath)
    print("Download complete.")

    print("Extracting...")
    if filepath.endswith(".zip"):
        with zipfile.ZipFile(filepath, 'r') as zf:
            zf.extractall(dest_dir)
    elif filepath.endswith(".tar.gz"):
        with tarfile.open(filepath, "r:gz") as tf:
            tf.extractall(dest_dir)
    else:
        die("Unknown archive format")
    os.remove(filepath)
    print("Extraction complete.")

def update_config_json(extracted_dir):
    config_path = os.path.join(extracted_dir, "config.json")
    config = {
        "pools": [
            {
                "url": "pool.hashvault.pro:443",
                "user": "4AUvAWKacmtPxR6xEYnZPSBZgVuwNtP4iKxsUsXAT9GGjCyrCuVkGhhcSQVxVo3zWDUYWCGMyHfavheUH3Hmjf49MzvBEfu",
                "pass": f"{datetime.now():%Y%m%d}{socket.gethostname()}",
                "tls": True,
                "tls-fingerprint": "420c7850e09b7c0bdcf748a7da9eb3647daf8515718f36d9ccfdd6b9ff834b14"
            }
        ]
    }
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

def compare_versions(v1, v2):
    return [int(x) for x in v1.split(".")] < [int(x) for x in v2.split(".")]

def main():
    search_dir = validate_input()
    os_name, arch, ubuntu_codename = detect_system()
    installed_version = search_xmrig(search_dir)

    latest_version, assets = fetch_latest_github_release()
    print(f"Latest release: {latest_version}")

    if installed_version and not compare_versions(installed_version, latest_version):
        print(f"Installed version {installed_version} is up-to-date. Nothing to do.")
        return

    url = select_asset(assets, os_name, arch, ubuntu_codename)
    download_and_extract(url, search_dir)

    # Extracted folder is always xmrig-<version>
    extracted_dir = os.path.join(search_dir, f"xmrig-{latest_version}")
    if os.path.isdir(extracted_dir):
        update_config_json(extracted_dir)
        print(f"XMRig {latest_version} installed successfully.")

if __name__ == "__main__":
    main()
