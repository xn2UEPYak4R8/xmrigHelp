# xmrigHelp

A smart, auto-updating script for [XMRig](https://xmrig.com/).  
Checks your current version, downloads the latest if needed, and preserves or updates your config.

## ✅ Features

- Auto-detects OS (Linux, macOS, Windows)
- Downloads and extracts the latest XMRig release

## 🚀 Usage

### Run locally:
```bash
python3 script.py <dir>
```

### Or run directly:

### Linux / macOS
```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/xn2UEPYak4R8/xmrigHelp/main/script.py)" <dir>
```

Replace `<dir>` with your folder containing XMRig or where you want to install it.

## ℹ️ Note

Sometimes older XMRig versions perform better on certain hardware.  
**Run both old and new versions to compare hash rates before deleting.**
