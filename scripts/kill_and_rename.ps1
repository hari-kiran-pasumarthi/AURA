# kill_and_rename.ps1
# Kills running processes matching keywords, finds exe paths, renames them to .blocked and saves a backup manifest.
# Run as Administrator.

$Keywords = @("discord","spotify","netflix","whatsapp","tiktok","youtube","steam","epic")
$SearchPaths = @("C:\Program Files","C:\Program Files (x86)", "$env:LOCALAPPDATA", "$env:APPDATA", "C:\ProgramData")
$BackupDir = "$env:ProgramData\distraction_blocker_backups"
New-Item -Path $BackupDir -ItemType Directory -Force | Out-Null

# 1) kill processes by name
$killed = @()
Get-Process | Where-Object { $n = $_.ProcessName.ToLower(); $Keywords | ForEach-Object { if ($n -match $_) { $true } } } | ForEach-Object {
    try { Stop-Process -Id $_.Id -Force -ErrorAction Stop; $killed += @{ name = $_.ProcessName; pid = $_.Id } } catch { }
}

# 2) find candidate exe paths
$candidates = @()
foreach ($base in $SearchPaths) {
    if (Test-Path $base) {
        Get-ChildItem -Path $base -Recurse -ErrorAction SilentlyContinue -Filter *.exe | ForEach-Object {
            $full = $_.FullName.ToLower()
            foreach ($k in $Keywords) { if ($full -match $k) { $candidates += $_.FullName; break } }
        }
    }
}
$candidates = $candidates | Sort-Object -Unique

# 3) rename with backup
$renamed = @()
foreach ($exe in $candidates) {
    try {
        $fileName = [IO.Path]::GetFileName($exe)
        $backupPath = Join-Path $BackupDir ($fileName + "." + (Get-Date -Format "yyyyMMddHHmmss") + ".bak")
        Copy-Item -Path $exe -Destination $backupPath -Force
        Rename-Item -Path $exe -NewName ($fileName + ".blocked") -ErrorAction Stop
        $renamed += @{ original = $exe; backup = $backupPath; blocked = ($exe + ".blocked") }
    } catch {
        # ignore failures (permissions / protected folders)
    }
}

# manifest
$manifest = @{
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    killed = $killed
    candidates = $candidates
    renamed = $renamed
}
$manifestPath = Join-Path $BackupDir "state_manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Out-File -FilePath $manifestPath -Encoding UTF8

Write-Output "ok"
Write-Output "killed: $($killed.Count) processes"
Write-Output "candidates found: $($candidates.Count)"
Write-Output "renamed: $($renamed.Count) files"
Write-Output "manifest saved to $manifestPath"