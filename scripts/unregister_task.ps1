param(
    [string]$TaskName = "ScrapperDailyDigest"
)

schtasks /Delete /TN $TaskName /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to delete scheduled task: $TaskName"
}

Write-Host "Scheduled task '$TaskName' removed."

