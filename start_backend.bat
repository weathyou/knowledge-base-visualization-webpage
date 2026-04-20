@echo off
setlocal

cd /d "%~dp0backend"

echo [消防预案系统] 正在启动后端服务...
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 未找到 python，请先安装 Python 并加入 PATH。
    pause
    exit /b 1
)

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo 后端服务已退出。
pause
