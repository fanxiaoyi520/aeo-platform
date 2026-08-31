$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "apps\api")

$env:DB_URL_SYNC = if ($env:DB_URL_SYNC) { $env:DB_URL_SYNC } else { "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo" }
uv run alembic upgrade head
