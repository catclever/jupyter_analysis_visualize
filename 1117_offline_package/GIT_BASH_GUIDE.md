# Git Bash 启动指南

如果你在 **Git Bash** 中进行操作（而不是 Windows `cmd.exe`），请按照本指南进行。

## 关键区别

| 特性 | Windows cmd | Git Bash |
|------|-----------|----------|
| Shell 类型 | Windows 命令行 | Unix/Linux 模拟 |
| 激活命令 | `call venv\Scripts\activate.bat` | `source venv/Scripts/activate` |
| 路径分隔符 | `\` (反斜杠) | `/` (正斜杠) |
| 环境变量 | `%VAR%` | `$VAR` |
| 脚本文件 | `.bat` | `.sh` |

## 方式 1：使用 Git Bash 启动脚本（推荐）

**运行以下命令**（在包目录中）：

```bash
bash start.sh
```

该脚本会自动：
1. ✅ 创建虚拟环境（如果不存在）
2. ✅ 配置虚拟环境路径
3. ✅ 安装所有依赖（仅首次需要）
4. ✅ 启动 FastAPI 服务

## 方式 2：手动启动（分步操作）

### 步骤 1：进入包目录

```bash
cd /path/to/1117_offline_package
```

### 步骤 2：创建虚拟环境

```bash
python -m venv venv
```

### 步骤 3：激活虚拟环境

```bash
source venv/Scripts/activate
```

> **重要**：在 Git Bash 中必须用 `source` 命令，不能用 `call` 命令

激活后，你应该看到：
```
(venv) user@computer:/path/to/1117_offline_package$
```

### 步骤 4：安装依赖

```bash
pip install --no-index --find-links backend/whls/whls aiohappyeyeballs aiohttp aiosignal annotated_doc annotated_types anyio appnope argon2_cffi argon2_cffi_bindings arrow asttokens async_lru async_timeout attrs babel beautifulsoup4 bidict bleach blinker certifi cffi charset_normalizer click colorama comm contourpy cryptography cycler debugpy decorator defusedxml exceptiongroup executing fastapi fastjsonschema flask Flask_SocketIO fonttools fqdn frozenlist grpcio h11 httpcore httpx idna ipykernel ipython ipywidgets isoduration itsdangerous jedi jinja2 json5 jsonpointer jsonschema jsonschema_specifications jupyter jupyter_client jupyter_console jupyter_core jupyter_events jupyter_lsp jupyter_server jupyter_server_terminals jupyterlab jupyterlab_pygments jupyterlab_server jupyterlab_widgets kiwisolver lark loguru markupsafe matplotlib matplotlib_inline mistune multidict nbclient nbconvert nbformat nest_asyncio notebook notebook_shim numpy overrides packaging pandas pandocfilters parso pexpect pillow platformdirs prometheus_client prompt_toolkit propcache protobuf psutil ptyprocess pure_eval pyarrow pycparser pydantic pydantic_core pydantic_settings pygments pyparsing python_dateutil python_dotenv python_engineio python_json_logger python_socketio pytz pywinpty pyyaml pyzmq referencing requests rfc3339_validator rfc3986_validator rfc3987_syntax rpds_py Send2Trash setuptools simple_websocket six sniffio soupsieve stack_data starlette terminado tinycss2 tomli tornado traitlets typing_extensions typing_inspection tzdata uri_template urllib3 uvicorn wcwidth webcolors webencodings websocket_client websockets werkzeug widgetsnbextension win32_setctime wsproto yarl
```

或者更简洁的方式：

```bash
pip install --no-index --find-links backend/whls/whls -r backend/requirements.txt
```

### 步骤 5：启动服务

```bash
python backend/app.py
```

### 步骤 6：访问应用

打开浏览器访问：`http://localhost:8000/`

### 步骤 7：停止服务

在 Git Bash 窗口中按 `Ctrl+C` 停止服务

### 步骤 8：后续启动

如果要再次启动：

```bash
# 进入包目录
cd /path/to/1117_offline_package

# 激活虚拟环境
source venv/Scripts/activate

# 启动服务
python backend/app.py
```

## 故障排除

### 问题 1：`source: not found` 或类似错误

这说明你可能在使用 Windows `cmd.exe` 而不是 Git Bash。

**检查方法**：看命令提示符的标题，是否显示"Git Bash"或"bash"。

**解决方案**：
- 右键点击文件夹
- 选择"Open Git Bash here"
- 或者手动打开 Git Bash：通常在开始菜单中搜索"Git Bash"

### 问题 2：权限错误 `Permission denied`

这通常是由于：
1. 文件没有可执行权限
2. 防火墙或杀毒软件阻止

**解决方案**：

```bash
# 给脚本添加执行权限
chmod +x start.sh

# 再次运行
bash start.sh
```

### 问题 3：虚拟环境激活后路径不对

如果你在 Git Bash 中：

**错误做法**：
```bash
call venv\Scripts\activate.bat    # ❌ call 命令在 Git Bash 中不存在
```

**正确做法**：
```bash
source venv/Scripts/activate      # ✅ 使用 source 命令
```

### 问题 4：找不到 Python

**检查 Python 是否安装**：

```bash
python --version
```

如果显示 `command not found`，说明 Python 没有加入 PATH。

**解决方案**：
1. 确保 Python 已安装（版本 3.10.x）
2. 在 Python 安装目录中找到 `python.exe`
3. 将其目录加入 Windows PATH 环境变量
4. 重启 Git Bash

## 总结

| 任务 | Git Bash 命令 |
|------|--------------|
| 创建虚拟环境 | `python -m venv venv` |
| 激活虚拟环境 | `source venv/Scripts/activate` |
| 安装依赖 | `pip install --no-index --find-links backend/whls/whls -r backend/requirements.txt` |
| 启动服务 | `python backend/app.py` |
| 停止服务 | `Ctrl+C` |

> **建议**：使用 `bash start.sh` 最简单，省去手动逐步执行的麻烦。
