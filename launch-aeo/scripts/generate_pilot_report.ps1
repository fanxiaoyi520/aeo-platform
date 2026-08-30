$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
uv run --package aeo-orchestrator python ./scripts/generate_pilot_report.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
