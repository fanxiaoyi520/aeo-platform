# Shared helpers for dev-start.ps1 / dev-stop.ps1

$ErrorActionPreference = "Stop"

function Get-DevRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-DevStateDir {
    $dir = Join-Path (Get-DevRoot) ".dev"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    return $dir
}

function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            Set-Item -Path "env:$($parts[0].Trim())" -Value $parts[1].Trim()
        }
    }
}

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSec = 90
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            # keep polling
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Get-ServicePidFile {
    param([string]$Name)
    return Join-Path (Get-DevStateDir) "$Name.pid"
}

function Get-ServiceLogFile {
    param([string]$Name)
    return Join-Path (Get-DevStateDir) "$Name.log"
}

function Stop-PortListeners {
    param([int]$Port)
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $connections) { return }
        foreach ($conn in $connections) {
            $procId = $conn.OwningProcess
            cmd /c "taskkill /PID $procId /T /F >nul 2>&1"
            Write-Host "  stopped PID $procId on port $Port" -ForegroundColor Gray
        }
        Start-Sleep -Seconds 2
    }
}

function Stop-DevService {
    param([string]$Name, [int]$Port)
    $pidFile = Get-ServicePidFile $Name
    if (Test-Path $pidFile) {
        $procId = [int](Get-Content $pidFile -Raw).Trim()
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
    Stop-PortListeners -Port $Port
}

function Start-DevService {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string[]]$Command,
        [int]$Port
    )

    if (Test-PortListening $Port) {
        Write-Host "  $Name already on :$Port — restarting" -ForegroundColor Yellow
        Stop-DevService -Name $Name -Port $Port
    }

    $logFile = Get-ServiceLogFile $Name
    $pidFile = Get-ServicePidFile $Name
    if (Test-Path $logFile) { Remove-Item $logFile -Force -ErrorAction SilentlyContinue }

    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command") + ($Command -join "; ")
    $proc = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList $argList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput $logFile

    Set-Content -Path $pidFile -Value $proc.Id -Encoding ascii
    Write-Host "  started $Name (PID $($proc.Id))" -ForegroundColor Green
    return $true
}

function Write-DevStatus {
    $apiUp = Test-PortListening 8000
    $webUp = Test-PortListening 3000
    Write-Host ""
    Write-Host "Service status:" -ForegroundColor Cyan
    Write-Host ("  API  :{0} http://127.0.0.1:8000" -f ($(if ($apiUp) { " up " } else { " down" })))
    Write-Host ("  Web  :{0} http://127.0.0.1:3000" -f ($(if ($webUp) { " up " } else { " down" })))
    Write-Host ("  Logs : $(Get-DevStateDir)")
}
