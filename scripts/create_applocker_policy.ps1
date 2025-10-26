# create_applocker_policy.ps1
# Run as Administrator. Produces a local AppLocker policy and sets Audit mode first.

# 1. Ensure Application Identity service is running
Start-Service -Name AppIDSvc -ErrorAction SilentlyContinue

# 2. Create default rules (Allow for Windows and Program Files)
$defaultPolicy = New-AppLockerPolicy -DefaultRule -ErrorAction Stop

# 3. Example deny rules by path (edit these paths to match your target apps)
# Use safe, app-specific paths; do NOT block system folders.
$denyRules = @()
# Example:
# $denyRules += New-AppLockerPolicy -RuleType Executable -FilePath "C:\Users\*\AppData\Local\Discord\*" -RuleName "Deny_Discord_byPath"
# $denyRules += New-AppLockerPolicy -RuleType Executable -FilePath "C:\Program Files\Spotify\*" -RuleName "Deny_Spotify_byPath"

# Merge default allow rules and optional deny rules
$merged = $defaultPolicy

# 4. Export policy to XML (audit mode)
$policyPath = "$env:ProgramData\AppLocker\applocker_audit.xml"
$merged | Export-AppLockerPolicy -Path $policyPath

Write-Output "AppLocker audit policy exported to $policyPath"
Write-Output "Policy is applied in Audit mode. Monitor Event Viewer -> Applications and Services Logs -> Microsoft -> Windows -> AppLocker -> EXE and DLL."

# 5. Apply policy (Audit mode)
Set-AppLockerPolicy -XMLPolicy $policyPath -Merge -ErrorAction SilentlyContinue
# Ensure enforcement is Audit (0)
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\SrpV2" -Name "EnforceRules" -Value 0 -PropertyType DWORD -Force | Out-Null

Write-Output "AppLocker policy applied in Audit mode."