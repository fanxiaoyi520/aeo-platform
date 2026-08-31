@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "INSTALLER=%~dp0install-docker-cli.ps1"

echo ========================================
echo  AEO Platform - Docker CLI Installer
echo  Data: %%LOCALAPPDATA%%\aeo-platform\docker
echo  Override: set AEO_DOCKER_ROOT
echo ========================================
echo.

echo Requesting administrator privileges...
echo If UAC appears, click YES.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$code = 1; try { $p = Start-Process powershell -Verb RunAs -Wait -PassThru -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%INSTALLER%'); if ($p) { $code = $p.ExitCode } } catch { Write-Host $_.Exception.Message -ForegroundColor Red }; exit $code"

set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo [SUCCESS] Docker CLI install completed.
    echo Log: %%LOCALAPPDATA%%\aeo-platform\docker\install.log
) else (
    echo [FAILED] Exit code: %RC%
    echo Check the admin PowerShell window and install.log under %%LOCALAPPDATA%%\aeo-platform\docker
)
echo.
pause
exit /b %RC%
