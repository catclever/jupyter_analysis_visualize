@echo off
REM Jupyter Analysis Visualize - 启动脚本

setlocal enabledelayedexpansion

echo ==========================================
echo Jupyter Analysis Visualize - 启动脚本
echo ==========================================
echo.

REM 检查虚拟环境
if not exist venv (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 无法创建虚拟环境，请确保 Python 已安装
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
    echo.
)

REM 激活虚拟环境
echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 无法激活虚拟环境
    pause
    exit /b 1
)
echo ✓ 虚拟环境已激活
echo.

REM 检查依赖是否已安装
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [3/3] 首次运行，安装依赖...
    python backend\whls\install.bat
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
    echo ✓ 依赖安装成功
) else (
    echo [3/3] 依赖已安装，跳过
)

echo.
echo ==========================================
echo 启动服务中...
echo ==========================================
echo.
echo 应用地址: http://localhost:8000/
echo 按 Ctrl+C 停止服务
echo.

python backend/app.py

pause
