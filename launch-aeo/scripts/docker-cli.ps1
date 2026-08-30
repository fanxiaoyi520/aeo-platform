# Docker CLI helper — use native docker or WSL Ubuntu docker (no Docker Desktop)

$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-WslDistro {
    $distros = wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    foreach ($name in @("Ubuntu", "Ubuntu-22.04", "Ubuntu-24.04")) {
        if ($distros -contains $name) { return $name }
    }
    if ($distros.Count -gt 0) { return $distros[0] }
    return $null
}

function Test-DockerCli {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $ver = docker version --format "{{.Server.Version}}" 2>$null
        return [bool]$ver
    }
    return $false
}

function Test-WslDockerCli {
    $distro = Get-WslDistro
    if (-not $distro) { return $false }
    $result = wsl -d $distro -e bash -lc "command -v docker" 2>$null
    return [bool]$result
}

function Get-WslProjectPath {
    param([string]$WindowsPath)
    $distro = Get-WslDistro
    if (-not $distro) { return $null }

    $dockerDir = "D:\Software\Docker"
    if (-not (Test-Path $dockerDir)) {
        New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
    }

    # UTF-16LE preserves Chinese path names; passing via CLI corrupts encoding.
    $winPathFile = Join-Path $dockerDir "windows-project-path.txt"
    [System.IO.File]::WriteAllText($winPathFile, $WindowsPath.TrimEnd('\'), [System.Text.Encoding]::Unicode)

    $convertScript = @'
#!/bin/bash
P=$(iconv -f UTF-16LE -t UTF-8 /mnt/d/Software/Docker/windows-project-path.txt | tr -d '\r\n\357\273\277')
wslpath -a "$P" | tr -d '\r' > /mnt/d/Software/Docker/wsl-project-path.txt
'@
    $scriptPath = Join-Path $dockerDir "convert-path.sh"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllBytes($scriptPath, $utf8.GetBytes($convertScript))

    wsl -d $distro -e bash /mnt/d/Software/Docker/convert-path.sh 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { return $null }

    $wslPathFile = Join-Path $dockerDir "wsl-project-path.txt"
    if (-not (Test-Path $wslPathFile)) { return $null }
    # Read as UTF-8 bytes; avoid PowerShell console code-page mangling WSL stdout.
    $bytes = [System.IO.File]::ReadAllBytes($wslPathFile)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    return $utf8.GetString($bytes).Trim()
}

function Ensure-WslDockerDaemon {
    $distro = Get-WslDistro
    if (-not $distro) { return $false }

    $check = wsl -d $distro -e bash -lc "sudo docker info >/dev/null 2>&1 && echo ok" 2>$null
    if ($check -match "ok") { return $true }

    wsl -d $distro -e bash -lc "sudo service docker start >/dev/null 2>&1 || true; if ! sudo docker info >/dev/null 2>&1; then sudo nohup dockerd >/tmp/dockerd.log 2>&1 & sleep 3; fi; sudo docker info >/dev/null 2>&1 && echo ok" | Out-Null
    $check2 = wsl -d $distro -e bash -lc "sudo docker info >/dev/null 2>&1 && echo ok" 2>$null
    return ($check2 -match "ok")
}

function Get-WslProjectPathFile {
    param([string]$WindowsPath)
    $wslPath = Get-WslProjectPath $WindowsPath
    if (-not $wslPath) { return $null }
    return "/mnt/d/Software/Docker/wsl-project-path.txt"
}

function Invoke-WslBash {
    param(
        [Parameter(Mandatory = $true)][string]$Command
    )
    $distro = Get-WslDistro
    if (-not $distro) {
        throw "WSL Ubuntu not found. Run .\scripts\install-docker-admin.cmd first."
    }
    if (-not (Ensure-WslDockerDaemon)) {
        throw "Docker daemon not running in WSL. Run .\scripts\fix-docker-daemon.ps1"
    }
    $root = Get-ProjectRoot
    $pathFile = Get-WslProjectPathFile $root
    if (-not $pathFile) {
        throw "Cannot convert project path to WSL: $root"
    }
    $fullCmd = "ROOT=`$(tr -d '\r' < '$pathFile') && cd `"`$ROOT`" && $Command"
    wsl -d $distro -e bash -lc $fullCmd
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-WslDocker {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )
    $argLine = ($Arguments | ForEach-Object {
        if ($_ -match "\s") { "'$_'" } else { $_ }
    }) -join " "
    Invoke-WslBash -Command "sudo docker $argLine"
}

function Invoke-DockerCompose {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ComposeFile,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$EnvFile = $null
    )
    $root = Get-ProjectRoot
    if (Test-DockerCli) {
        Push-Location $root
        try {
            $composeArgs = @("compose")
            if ($EnvFile) { $composeArgs += @("--env-file", $EnvFile) }
            $composeArgs += @("-f", $ComposeFile) + $Arguments
            docker @composeArgs
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        } finally {
            Pop-Location
        }
        return
    }
    if (Test-WslDockerCli) {
        $relFile = $ComposeFile -replace "\\", "/"
        $allArgs = @("compose")
        if ($EnvFile) {
            $relEnv = $EnvFile -replace "\\", "/"
            $allArgs += @("--env-file", $relEnv)
        }
        $allArgs += @("-f", $relFile) + $Arguments
        Invoke-WslDocker -Arguments $allArgs
        return
    }
    throw @"
Docker CLI not found.

Install command-line Docker (WSL):
  .\scripts\install-docker-admin.cmd

Or run without Docker:
  .\scripts\dev-local.ps1
"@
}

function Invoke-DockerCli {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    if (Test-DockerCli) {
        & docker @Arguments
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        return
    }
    Invoke-WslDocker -Arguments $Arguments
}
