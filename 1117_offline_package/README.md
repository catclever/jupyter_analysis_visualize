# Jupyter Analysis Visualize - 离线部署包

## 📦 包内容

```
offline_package/
├── backend/                 # Python 后端服务
│   ├── app.py              # FastAPI 主应用（已配置静态文件托管）
│   ├── *.py                # 后端模块（notebook_manager, project_manager 等）
│   ├── requirements.txt     # 依赖列表（参考）
│   ├── whls/               # 离线轮子包（148 个，135MB）
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

### 第一次启动

**1. 创建虚拟环境**
```batch
cd 到本目录
python -m venv venv
call venv\Scripts\activate.bat
```

**2. 安装依赖**
```batch
python backend\whls\install.bat
```

或者手动安装：
```batch
pip install --no-index --find-links backend\whls -r backend\requirements.txt
```

**3. 启动服务**
```batch
python backend/app.py
```

**4. 访问应用**
- 打开浏览器访问：`http://localhost:8000/`

### 后续启动

**激活虚拟环境并启动**
```batch
call venv\Scripts\activate.bat
python backend/app.py
```

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
- 确保 Python 已安装且添加到 PATH
- 查看 `python --version` 确认版本为 3.10+

### 问题 2：安装失败（缺少依赖）
- 检查 `backend\whls\whls\` 目录中是否有轮子文件
- 确保运行了 `install.bat` 或完整的 pip install 命令

### 问题 3：无法访问应用
- 检查 `http://localhost:8000/` 是否可访问
- 查看终端输出是否有错误信息
- 试试改端口看是否是端口被占用

### 问题 4：项目无法加载
- 检查 `projects/` 目录是否存在且有写入权限
- 查看应用日志了解具体错误

## 📝 说明

- **后端**: FastAPI + Jupyter 内核，支持代码执行和项目管理
- **前端**: React + ReactFlow，用于 DAG 可视化和交互
- **静态托管**: 前端已预编译，由后端直接托管，无需单独部署
- **离线运行**: 所有依赖已包含，无需网络连接

## 🆘 支持

问题反馈请查看原项目仓库
