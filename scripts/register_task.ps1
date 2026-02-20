param(
    [string]$TaskName = "ScrapperDailyDigest",
    [string]$RunAt = "08:00"
)

$scriptPath = (Resolve-Path "$PSScriptRoot\run_daily.ps1").Path
$timezone = (tzutil /g).Trim()

if ($timezone -ne "Korea Standard Time") {
    Write-Warning "Current timezone is '$timezone'. For Asia/Seoul 08:00, use Korea Standard Time."
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

schtasks /Create /TN $TaskName /TR $taskCommand /SC DAILY /ST $RunAt /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create scheduled task: $TaskName"
}

Write-Host "Scheduled task '$TaskName' created at $RunAt (local machine time)."

