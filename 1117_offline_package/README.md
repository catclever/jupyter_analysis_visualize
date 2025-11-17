# Jupyter Analysis Visualize - 离线部署包

## 📦 包内容

```
offline_package/
├── backend/                 # Python 后端服务
│   ├── app.py              # FastAPI 主应用（已配置静态文件托管）
│   ├── *.py                # 后端模块（notebook_manager, project_manager 等）
│   ├── requirements.txt     # 依赖列表（参考）
│   ├── whls/               # 离线轮子包（149 个，135MB）
│   │   ├── whls/           # 编译好的 .whl 文件
│   │   ├── install.bat     # Windows 一键安装脚本
│   │   └── requirements.txt # 副本
│   ├── toolkits/           # 工具库（可选）
│   ├── node_types/         # 节点类型定义
│   └── [其他模块]
├── frontend/               # 前端应用
│   └── dist/               # 预编译的前端静态文件
│       ├── index.html      # 入口页面
│       ├── favicon.ico
│       ├── robots.txt
│       └── assets/         # CSS/JS 资源
├── projects/               # 用户项目目录（初始为空）
└── README.md               # 本文件
```

## 🚀 启动步骤（Windows）

### 选择你的环境

选择下面**其中一种**方式启动：

#### 方式 A：Windows cmd（命令提示符）

**直接双击运行 `start.bat`**（推荐）

```batch
双击 start.bat
```

该脚本会自动：
1. ✅ 创建虚拟环境（如果不存在）
2. ✅ 配置虚拟环境路径
3. ✅ 安装所有依赖（仅首次需要）
4. ✅ 启动 FastAPI 服务

> **⚠️ 重要**：如果遇到权限错误，请**以管理员身份运行命令提示符**后再执行 `start.bat`

#### 方式 B：Git Bash

在 Git Bash 中运行：

```bash
bash start.sh
```

> **详细说明**：请参考 `GIT_BASH_GUIDE.md` 获取完整的 Git Bash 使用说明

### 手动启动（如果不想用脚本）

#### 在 Windows cmd 中：

**1. 打开命令提示符并进入本目录**
```batch
cd 到本目录
```

**2. 创建虚拟环境**
```batch
python -m venv venv
```

**3. 配置虚拟环境路径**
```batch
set VENV_PYTHON=venv\Scripts\python.exe
set VENV_PIP=venv\Scripts\pip.exe
```

**4. 安装依赖**
```batch
%VENV_PIP% install --no-index --find-links backend\whls\whls -r backend\requirements.txt
```

**5. 启动服务**
```batch
%VENV_PYTHON% backend/app.py
```

**6. 访问应用**
- 打开浏览器访问：`http://localhost:8000/`

#### 在 Git Bash 中：

**1. 进入包目录**
```bash
cd /path/to/1117_offline_package
```

**2. 创建虚拟环境**
```bash
python -m venv venv
```

**3. 激活虚拟环境**
```bash
source venv/Scripts/activate
```

**4. 安装依赖**
```bash
pip install --no-index --find-links backend/whls/whls -r backend/requirements.txt
```

**5. 启动服务**
```bash
python backend/app.py
```

**6. 访问应用**
- 打开浏览器访问：`http://localhost:8000/`

## 📋 系统要求

- **操作系统**：Windows 10 或更高
- **处理器**：AMD64（x86-64）
- **Python 版本**：3.10
- **磁盘空间**：至少 500MB（包含虚拟环境）
- **内存**：最小 2GB（建议 4GB+）
- **网络**：离线环境，无需网络连接

## 📊 包大小

- 轮子包（whls）：135 MB
- 前端文件：2.2 MB  
- 后端代码：约 5 MB
- **总计**：约 142 MB（不含虚拟环境）
- 虚拟环境大小：约 400-500 MB

## ⚙️ 配置

### 修改端口

编辑 `backend/app.py` 的最后几行，修改 `port` 参数：

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,  # 改为你想要的端口
    )
```

### 前端 API 地址

前端自动连接 `http://localhost:8000/api`，如果改了端口需要同时检查前端配置。

## 🔧 故障排除

### 问题 1：`python not found`
- 确保 Python 3.10 已安装且添加到 PATH
- 打开命令提示符，运行 `python --version` 确认版本为 3.10.x

### 问题 2：权限错误 `[WinError 5] 拒绝访问`
- **解决方案**：以管理员身份运行命令提示符
  1. 右键单击"命令提示符"或"PowerShell"
  2. 选择"以管理员身份运行"
  3. 进入包目录后再运行 `start.bat`

### 问题 3：安装失败（缺少依赖）
- 确保 `backend\whls\whls\` 目录中有 149 个轮子文件（.whl）
- 检查磁盘空间是否充足（至少 500MB 可用）
- 试试运行 `backend\whls\install.bat` 查看详细错误信息

### 问题 4：虚拟环境未被正确使用
- **确保使用了正确的方法**：
  - ❌ **错误**：`call activate.bat` 然后运行 `pip install`
  - ✅ **正确**：使用 `set VENV_PIP=venv\Scripts\pip.exe`，然后 `%VENV_PIP% install`
  - ✅ **推荐**：直接使用 `start.bat` 脚本（已正确配置）

### 问题 5：无法访问应用
- 检查 `http://localhost:8000/` 是否可访问
- 查看命令提示符窗口的输出是否有错误信息
- 试试改端口看是否是端口 8000 被占用：编辑 `backend/app.py` 最后几行

### 问题 6：项目无法加载
- 检查 `projects/` 目录是否存在且有写入权限
- 查看应用日志了解具体错误信息

## 📝 说明

- **后端**: FastAPI + Jupyter 内核，支持代码执行和项目管理
- **前端**: React + ReactFlow，用于 DAG 可视化和交互
- **静态托管**: 前端已预编译，由后端直接托管，无需单独部署
- **离线运行**: 所有依赖已包含，无需网络连接

## 🆘 支持

问题反馈请查看原项目仓库
