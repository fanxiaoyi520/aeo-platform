$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

$root = Get-ProjectRoot
$bashScript = Join-Path $PSScriptRoot "backup.sh"

if (-not (Test-Path $bashScript)) {
    throw "Missing backup.sh"
}

if (Get-Command bash -ErrorAction SilentlyContinue) {
    Push-Location $root
    try {
        bash "./scripts/backup.sh"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
    exit 0
}

if (Test-WslDockerCli) {
    Invoke-WslBash -Command "bash ./scripts/backup.sh"
    exit 0
}

throw "bash not found. Install WSL Ubuntu (.\scripts\install-docker-admin.cmd) or Git Bash."
