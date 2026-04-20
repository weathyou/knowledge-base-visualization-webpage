@echo off
setlocal

echo [消防预案系统] 正在同步预案目录...
echo.

where curl >nul 2>nul
if %errorlevel% equ 0 (
    curl -X POST http://127.0.0.1:8000/api/sync
    echo.
    echo 同步请求已发送。
    pause
    exit /b 0
)

where powershell >nul 2>nul
if %errorlevel% equ 0 (
    powershell -Command "try { Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8000/api/sync | Select-Object -ExpandProperty Content } catch { Write-Output $_.Exception.Message; exit 1 }"
    echo.
    echo 同步请求已发送。
    pause
    exit /b 0
)

echo 未找到 curl 或 powershell，无法发送同步请求。
pause
exit /b 1
