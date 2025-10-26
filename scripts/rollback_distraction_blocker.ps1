# rollback_distraction_blocker.ps1
# Run as Administrator. Restores backed-up EXEs and removes hosts entries recorded earlier.

$BackupDir = "$env:ProgramData\distraction_blocker_backups"
$manifestPath = Join-Path $BackupDir "state_manifest.json"
$hostsRecord = Join-Path $BackupDir "hosts_block_record.json"
$HostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"

# 1) restore renamed files
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    foreach ($item in $manifest.renamed) {
        try {
            $blockedPath = $item.blocked
            $origPath = $item.original
            $backup = $item.backup
            if (Test-Path $backup) {
                Copy-Item -Path $backup -Destination $origPath -Force
                # remove blocked file if it still exists
                if (Test-Path $blockedPath) { Remove-Item -Path $blockedPath -Force -ErrorAction SilentlyContinue }
            }
        } catch { }
    }
    Remove-Item $manifestPath -ErrorAction SilentlyContinue
}

# 2) remove hosts entries
if (Test-Path $hostsRecord) {
    $rec = Get-Content $hostsRecord -Raw | ConvertFrom-Json
    if (Test-Path $HostsFile) {
        $lines = Get-Content $HostsFile -ErrorAction SilentlyContinue
        $filtered = $lines | Where-Object { $line = $_; -not ($rec.added | ForEach-Object { $line -match [regex]::Escape($_) } ) }
        $filtered | Out-File -FilePath $HostsFile -Encoding ASCII
    }
    Remove-Item $hostsRecord -ErrorAction SilentlyContinue
}

Write-Output "ok"
Write-Output "restore complete"