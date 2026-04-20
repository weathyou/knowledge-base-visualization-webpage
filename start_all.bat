@echo off
setlocal

cd /d "%~dp0"

echo [消防预案系统] 正在同时启动后端和前端...
echo.

start "消防预案系统 - Backend" cmd /k call "%~dp0start_backend.bat"
start "消防预案系统 - Frontend" cmd /k call "%~dp0start_frontend.bat"

echo 已打开前后端启动窗口。
echo 浏览器访问: http://localhost:5173
echo.
pause
