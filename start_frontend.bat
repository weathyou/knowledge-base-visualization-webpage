@echo off
setlocal

cd /d "%~dp0frontend"

echo [消防预案系统] 正在启动前端服务...
echo.

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo 未找到 npm，请先安装 Node.js。
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo 检测到前端依赖未安装，正在执行 npm install ...
    call npm install
    if %errorlevel% neq 0 (
        echo 前端依赖安装失败，请检查 Node.js / npm 环境。
        pause
        exit /b 1
    )
)

call npm run dev

echo.
echo 前端服务已退出。
pause
