# block_domains_hosts.ps1
# Run as Administrator. Adds domain -> 0.0.0.0 entries to hosts file and records what was added.

$Domains = @("web.whatsapp.com","whatsapp.com","www.whatsapp.com","netflix.com","www.netflix.com","youtube.com","www.youtube.com")
$HostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"
$RecordDir = "$env:ProgramData\distraction_blocker_backups"
New-Item -Path $RecordDir -ItemType Directory -Force | Out-Null
$added = @()

$existing = ""
if (Test-Path $HostsFile) { $existing = Get-Content $HostsFile -Raw -ErrorAction SilentlyContinue }

foreach ($d in $Domains) {
    if ($existing -notmatch [regex]::Escape($d)) {
        Add-Content -Path $HostsFile -Value "0.0.0.0 $d"
        $added += $d
    }
}

$record = @{
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    added = $added
}
$record | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $RecordDir "hosts_block_record.json") -Encoding UTF8

Write-Output "ok"
Write-Output "domains added: $($added.Count)"