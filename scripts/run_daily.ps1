param(
    [switch]$DryRun
)

$projectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonCmd = if (Test-Path $venvPython) { $venvPython } else { "python" }

Set-Location $projectRoot

$args = @("-m", "scrapper.main")
if ($DryRun) {
    $args += "--dry-run"
}

& $pythonCmd @args
exit $LASTEXITCODE

