$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$argsLine = $args -join " "
if ($argsLine) {
    uv run --package aeo-orchestrator python ./scripts/batch_pilot.py @args
} else {
    uv run --package aeo-orchestrator python ./scripts/batch_pilot.py --dry-run
}
exit $LASTEXITCODE
