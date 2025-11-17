@echo off
REM 离线pip安装脚本 - Windows
setlocal enabledelayedexpansion

echo 开始安装离线轮子包...
echo 当前目录: %cd%

REM 安装所有轮子包
pip install --no-index --find-links=whls aiohappyeyeballs aiohttp aiosignal annotated_doc annotated_types anyio appnope argon2_cffi argon2_cffi_bindings arrow asttokens async_lru async_timeout attrs babel beautifulsoup4 bidict bleach blinker certifi cffi charset_normalizer click colorama comm contourpy cryptography cycler debugpy decorator defusedxml exceptiongroup executing fastapi fastjsonschema flask Flask_SocketIO fonttools fqdn frozenlist grpcio h11 httpcore httpx idna ipykernel ipython ipywidgets isoduration itsdangerous jedi jinja2 json5 jsonpointer jsonschema jsonschema_specifications jupyter jupyter_client jupyter_console jupyter_core jupyter_events jupyter_lsp jupyter_server jupyter_server_terminals jupyterlab jupyterlab_pygments jupyterlab_server jupyterlab_widgets kiwisolver lark loguru markupsafe matplotlib matplotlib_inline mistune multidict nbclient nbconvert nbformat nest_asyncio notebook notebook_shim numpy overrides packaging pandas pandocfilters parso pexpect pillow platformdirs prometheus_client prompt_toolkit propcache protobuf psutil ptyprocess pure_eval pyarrow pycparser pydantic pydantic_core pydantic_settings pygments pyparsing python_dateutil python_dotenv python_engineio python_json_logger python_socketio pytz pywinpty pyyaml pyzmq referencing requests rfc3339_validator rfc3986_validator rfc3987_syntax rpds_py Send2Trash setuptools simple_websocket six sniffio soupsieve stack_data starlette terminado tinycss2 tomli tornado traitlets typing_extensions typing_inspection tzdata uri_template urllib3 uvicorn wcwidth webcolors webencodings websocket_client websockets werkzeug widgetsnbextension wsproto yarl

if %errorlevel% equ 0 (
    echo.
    echo ✓ 安装完成！
) else (
    echo.
    echo ✗ 安装失败，请检查上面的错误信息
    pause
    exit /b 1
)

pause
