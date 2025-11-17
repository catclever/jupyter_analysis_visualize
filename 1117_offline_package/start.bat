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
        echo 错误: 无法创建虚拟环境，请确保 Python 3.10 已安装
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
    echo.
)

REM 设置虚拟环境的 Python 和 pip 路径
echo [2/3] 配置虚拟环境...
set VENV_PYTHON=venv\Scripts\python.exe
set VENV_PIP=venv\Scripts\pip.exe
echo ✓ 虚拟环境配置完成
echo.

REM 检查依赖是否已安装
%VENV_PIP% show fastapi >nul 2>&1
if errorlevel 1 (
    echo [3/3] 首次运行，安装依赖...
    echo.
    echo 这可能需要几分钟...
    echo.

    REM 直接用虚拟环境的 pip 安装轮子
    %VENV_PIP% install --no-index --find-links backend\whls\whls aiohappyeyeballs aiohttp aiosignal annotated_doc annotated_types anyio appnope argon2_cffi argon2_cffi_bindings arrow asttokens async_lru async_timeout attrs babel beautifulsoup4 bidict bleach blinker certifi cffi charset_normalizer click colorama comm contourpy cryptography cycler debugpy decorator defusedxml exceptiongroup executing fastapi fastjsonschema flask Flask_SocketIO fonttools fqdn frozenlist grpcio h11 httpcore httpx idna ipykernel ipython ipywidgets isoduration itsdangerous jedi jinja2 json5 jsonpointer jsonschema jsonschema_specifications jupyter jupyter_client jupyter_console jupyter_core jupyter_events jupyter_lsp jupyter_server jupyter_server_terminals jupyterlab jupyterlab_pygments jupyterlab_server jupyterlab_widgets kiwisolver lark loguru markupsafe matplotlib matplotlib_inline mistune multidict nbclient nbconvert nbformat nest_asyncio notebook notebook_shim numpy overrides packaging pandas pandocfilters parso pexpect pillow platformdirs prometheus_client prompt_toolkit propcache protobuf psutil ptyprocess pure_eval pyarrow pycparser pydantic pydantic_core pydantic_settings pygments pyparsing python_dateutil python_dotenv python_engineio python_json_logger python_socketio pytz pywinpty pyyaml pyzmq referencing requests rfc3339_validator rfc3986_validator rfc3987_syntax rpds_py Send2Trash setuptools simple_websocket six sniffio soupsieve stack_data starlette terminado tinycss2 tomli tornado traitlets typing_extensions typing_inspection tzdata uri_template urllib3 uvicorn wcwidth webcolors webencodings websocket_client websockets werkzeug widgetsnbextension win32_setctime wsproto yarl

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

REM 从根目录启动，确保路径解析正确
cd /d "%~dp0"

REM 清理 Python 缓存
if exist backend\__pycache__ (
    echo 清理 Python 缓存...
    rmdir /s /q backend\__pycache__
)

%VENV_PYTHON% backend/app.py

pause
