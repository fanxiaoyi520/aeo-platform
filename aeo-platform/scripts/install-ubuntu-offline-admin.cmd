@echo off
setlocal
chcp 65001 >nul
echo Offline Ubuntu install (when Microsoft Store/CDN unreachable)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%~dp0install-ubuntu-offline.ps1')"
pause
