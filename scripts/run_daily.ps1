param(
    [switch]$DryRun,
    [string]$LogDir = "logs"
)

$projectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonCmd = if (Test-Path $venvPython) { $venvPython } else { "python" }

Set-Location $projectRoot

$args = @("-m", "scrapper.main")
if ($DryRun) {
    $args += "--dry-run"
}

$resolvedLogDir = if ([System.IO.Path]::IsPathRooted($LogDir)) {
    $LogDir
} else {
    Join-Path $projectRoot $LogDir
}

New-Item -ItemType Directory -Path $resolvedLogDir -Force | Out-Null

$mode = if ($DryRun) { "dryrun" } else { "run" }
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $resolvedLogDir ("scrapper-{0}-{1}.log" -f $mode, $timestamp)

Write-Host "Log file: $logPath"
$previousPythonWarnings = $env:PYTHONWARNINGS
if ([string]::IsNullOrWhiteSpace($previousPythonWarnings)) {
    $env:PYTHONWARNINGS = "ignore::ResourceWarning"
} else {
    $env:PYTHONWARNINGS = "{0},ignore::ResourceWarning" -f $previousPythonWarnings
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& $pythonCmd @args *> $logPath
$ErrorActionPreference = $previousErrorActionPreference
Get-Content -Path $logPath | Out-Host

if ($null -eq $previousPythonWarnings) {
    Remove-Item Env:PYTHONWARNINGS -ErrorAction SilentlyContinue
} else {
    $env:PYTHONWARNINGS = $previousPythonWarnings
}
$exitCode = $LASTEXITCODE

$errorPatterns = @(
    "Traceback (most recent call last):",
    "Pipeline failed:",
    "| ERROR |",
    "ModuleNotFoundError",
    "SMTPAuthenticationError",
    "Authentication failed"
)
$warningPatterns = @(
    "| WARNING |",
    "Error to search using bing backend:",
    "ConnectionError:",
    "Run completed | dry_run=True searched=0 selected=0 summarized=0"
)

$errorHits = @()
foreach ($pattern in $errorPatterns) {
    $matches = Select-String -Path $logPath -Pattern $pattern -SimpleMatch
    if ($matches) {
        $errorHits += $matches
    }
}

$warningHits = @()
foreach ($pattern in $warningPatterns) {
    $matches = Select-String -Path $logPath -Pattern $pattern -SimpleMatch
    if ($matches) {
        $warningHits += $matches
    }
}

if ($exitCode -ne 0 -or $errorHits.Count -gt 0) {
    Write-Host "Log check: issue detected."
    if ($errorHits.Count -gt 0) {
        Write-Host "Matched error lines:"
        $errorHits | ForEach-Object { Write-Host ("  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim()) }
    }
} elseif ($warningHits.Count -gt 0) {
    Write-Host "Log check: warning found."
    Write-Host "Matched warning lines:"
    $warningHits | ForEach-Object { Write-Host ("  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim()) }
} else {
    Write-Host "Log check: no obvious issue."
}

$runCompletedLine = Select-String -Path $logPath -Pattern "Run completed |" -SimpleMatch | Select-Object -Last 1
if ($runCompletedLine) {
    $line = $runCompletedLine.Line
    if ($line -match "summary_failed=(\d+)") {
        $failedCount = [int]$matches[1]
        if ($failedCount -gt 0) {
            Write-Host ("Summary quality: degraded (summary_failed={0})" -f $failedCount)
            if ($line -match "summary_failed_reasons=(.+) sent_email=") {
                Write-Host ("Summary failed reasons: {0}" -f $matches[1])
            }
        } else {
            Write-Host "Summary quality: OK (summary_failed=0)"
        }
    }
}

exit $exitCode

