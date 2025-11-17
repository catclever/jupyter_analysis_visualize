# project.json 格式验证指南

## ✅ 正确的 project.json 格式

### 最小化示例（必需字段）

```json
{
  "project_id": "my_project",
  "name": "My Project",
  "description": "Project description",
  "version": "1.0.0",
  "created_at": "2025-11-17T10:30:00.000000",
  "updated_at": "2025-11-17T10:30:00.000000",
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source",
      "name": "Data Source",
      "depends_on": [],
      "execution_status": "not_executed",
      "result_format": null,
      "result_path": null,
      "error_message": null,
      "last_execution_time": null
    }
  ]
}
```

### 完整示例（带执行结果）

```json
{
  "project_id": "sales_analysis",
  "name": "Sales Data Analysis",
  "description": "Analyze sales performance metrics",
  "version": "1.0.0",
  "created_at": "2025-11-17T10:00:00.000000",
  "updated_at": "2025-11-17T14:30:00.000000",
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source",
      "name": "Load Sales Data",
      "depends_on": [],
      "execution_status": "validated",
      "result_format": "parquet",
      "result_path": "parquets/data_1.parquet",
      "error_message": null,
      "last_execution_time": "2025-11-17T14:00:00.000000"
    },
    {
      "node_id": "compute_1",
      "type": "compute",
      "name": "Calculate Metrics",
      "depends_on": ["data_1"],
      "execution_status": "validated",
      "result_format": "parquet",
      "result_path": "parquets/compute_1.parquet",
      "error_message": null,
      "last_execution_time": "2025-11-17T14:10:00.000000"
    },
    {
      "node_id": "chart_1",
      "type": "chart",
      "name": "Sales Trend Chart",
      "depends_on": ["compute_1"],
      "execution_status": "not_executed",
      "result_format": null,
      "result_path": null,
      "error_message": null,
      "last_execution_time": null
    }
  ]
}
```

## 🔍 字段详解

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `project_id` | string | ✅ | 项目唯一标识符（必须与目录名一致） | `"my_project"` |
| `name` | string | ✅ | 项目显示名称 | `"My Project"` |
| `description` | string | ❌ | 项目描述 | `"Project description"` |
| `version` | string | ✅ | 项目版本 | `"1.0.0"` |
| `created_at` | string | ✅ | 创建时间（ISO 8601 格式） | `"2025-11-17T10:30:00"` |
| `updated_at` | string | ✅ | 最后更新时间（ISO 8601 格式） | `"2025-11-17T10:30:00"` |
| `nodes` | array | ✅ | 节点列表 | `[{...}, {...}]` |

### nodes 数组中的字段

| 字段 | 类型 | 必需 | 说明 | 有效值 |
|------|------|------|------|--------|
| `node_id` | string | ✅ | 节点唯一标识符 | `"data_1"` |
| `type` | string | ✅ | 节点类型 | `data_source`, `compute`, `chart`, `image`, `tool` |
| `name` | string | ✅ | 节点显示名称 | `"Load Data"` |
| `depends_on` | array | ✅ | 依赖的节点 ID 列表 | `["data_1", "data_2"]` 或 `[]` |
| `execution_status` | string | ✅ | 执行状态 | `not_executed`, `pending_validation`, `validated` |
| `result_format` | string/null | ✅ | 结果格式 | `"parquet"`, `"json"`, `"image"`, `null` |
| `result_path` | string/null | ✅ | 结果文件路径 | `"parquets/data_1.parquet"`, `null` |
| `error_message` | string/null | ✅ | 错误信息 | `"Error details"`, `null` |
| `last_execution_time` | string/null | ✅ | 最后执行时间 | `"2025-11-17T14:00:00"`, `null` |

## ❌ 常见错误

### 错误 1：nodes 是字典而不是数组

```json
{
  "nodes": {
    "data_1": { ... },
    "compute_1": { ... }
  }
}
```

**问题**：代码期望 `nodes` 是数组 `[{...}, {...}]`，不是字典
**修复**：改为数组格式：
```json
{
  "nodes": [
    { "node_id": "data_1", ... },
    { "node_id": "compute_1", ... }
  ]
}
```

### 错误 2：缺少必需字段

```json
{
  "project_id": "test",
  "name": "Test"
  // 缺少 description, version, created_at, updated_at, nodes
}
```

**问题**：后端在加载时会出错
**修复**：添加所有必需字段

### 错误 3：节点缺少字段

```json
{
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source"
      // 缺少 name, depends_on, execution_status 等
    }
  ]
}
```

**问题**：前端显示不正确或崩溃
**修复**：添加所有必需的节点字段

### 错误 4：type 字段值错误

```json
{
  "nodes": [
    {
      "node_id": "data_1",
      "type": "datasource"  // ❌ 应该是 data_source
    }
  ]
}
```

**有效的 type 值**：
- `data_source` （数据源）
- `compute` （计算）
- `chart` （图表）
- `image` （图像）
- `tool` （工具）

### 错误 5：dependencies 循环

```json
{
  "nodes": [
    { "node_id": "a", "depends_on": ["b"] },
    { "node_id": "b", "depends_on": ["a"] }  // 循环依赖！
  ]
}
```

**问题**：无法执行，会导致死循环
**修复**：检查依赖关系树，确保无循环

### 错误 6：project_id 与目录名不一致

```
projects/
└── my_project/
    └── project.json  (内容：project_id: "different_name")
```

**问题**：项目加载失败
**修复**：确保 project.json 中的 `project_id` 与目录名一致

### 错误 7：depends_on 引用不存在的节点

```json
{
  "nodes": [
    {
      "node_id": "compute_1",
      "depends_on": ["nonexistent_node"]  // 该节点不存在！
    }
  ]
}
```

**问题**：前端可能加载失败或显示错误
**修复**：确保 `depends_on` 中的所有节点都在 `nodes` 数组中存在

### 错误 8：result_path 指向不存在的文件

```json
{
  "nodes": [
    {
      "execution_status": "validated",
      "result_path": "parquets/nonexistent.parquet"  // 文件不存在！
    }
  ]
}
```

**问题**：查看结果时会失败
**修复**：确保：
- 如果 `execution_status` 是 `validated`，`result_path` 必须指向存在的文件
- 文件确实存在于 `projects/{project_id}/` 目录下

## ✅ 验证检查清单

运行以下检查确保 project.json 正确：

### 手动检查

```bash
# 1. 检查 JSON 格式是否有效
cd projects/your_project
cat project.json | python -m json.tool > /dev/null && echo "JSON 有效" || echo "JSON 无效"

# 2. 检查 project_id 是否与目录名一致
python << 'PYTHON'
import json
from pathlib import Path

# 获取目录名
dir_name = Path.cwd().name

# 读取 project.json
with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

if data['project_id'] == dir_name:
    print("✓ project_id 与目录名一致")
else:
    print(f"✗ project_id 不匹配：dir={dir_name}, json={data['project_id']}")
PYTHON

# 3. 检查必需字段
python << 'PYTHON'
import json

required_fields = ['project_id', 'name', 'version', 'created_at', 'updated_at', 'nodes']
with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for field in required_fields:
    if field in data:
        print(f"✓ {field} 存在")
    else:
        print(f"✗ {field} 缺失")
PYTHON

# 4. 验证节点字段
python << 'PYTHON'
import json

required_node_fields = ['node_id', 'type', 'name', 'depends_on', 'execution_status',
                        'result_format', 'result_path', 'error_message', 'last_execution_time']

with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, node in enumerate(data.get('nodes', [])):
    print(f"\n节点 {i+1} ({node.get('node_id', '??')}):")
    for field in required_node_fields:
        if field in node:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} 缺失")
PYTHON

# 5. 检查节点类型是否有效
python << 'PYTHON'
import json

valid_types = {'data_source', 'compute', 'chart', 'image', 'tool'}
with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for node in data.get('nodes', []):
    node_type = node.get('type')
    if node_type in valid_types:
        print(f"✓ {node['node_id']}: type={node_type}")
    else:
        print(f"✗ {node['node_id']}: 无效的 type={node_type}（有效值：{valid_types}）")
PYTHON

# 6. 检查依赖关系
python << 'PYTHON'
import json

with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

node_ids = {node['node_id'] for node in data.get('nodes', [])}

for node in data.get('nodes', []):
    for dep in node.get('depends_on', []):
        if dep in node_ids:
            print(f"✓ {node['node_id']} → {dep}")
        else:
            print(f"✗ {node['node_id']} 依赖不存在的节点: {dep}")
PYTHON

# 7. 检查结果文件是否存在
python << 'PYTHON'
import json
from pathlib import Path

with open('project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for node in data.get('nodes', []):
    if node.get('execution_status') == 'validated' and node.get('result_path'):
        result_file = Path(node['result_path'])
        if result_file.exists():
            print(f"✓ {node['node_id']}: 结果文件存在")
        else:
            print(f"✗ {node['node_id']}: 结果文件不存在 ({result_file})")
PYTHON
```

## 🔧 自动验证工具

创建 `validate_project.py` 脚本进行自动验证：

```python
#!/usr/bin/env python
"""Validate project.json format"""

import json
import sys
from pathlib import Path

def validate_project_json(project_dir):
    """Validate project.json in a project directory"""
    project_json_path = Path(project_dir) / 'project.json'

    if not project_json_path.exists():
        print(f"❌ project.json 不存在: {project_json_path}")
        return False

    try:
        with open(project_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        return False

    # 检查必需字段
    required_fields = ['project_id', 'name', 'version', 'created_at', 'updated_at', 'nodes']
    for field in required_fields:
        if field not in data:
            print(f"❌ 缺少必需字段: {field}")
            return False

    # 检查 project_id 与目录名
    if data['project_id'] != Path(project_dir).name:
        print(f"❌ project_id 与目录名不匹配: {data['project_id']} != {Path(project_dir).name}")
        return False

    # 检查 nodes
    if not isinstance(data['nodes'], list):
        print(f"❌ nodes 必须是数组，而不是 {type(data['nodes']).__name__}")
        return False

    if len(data['nodes']) == 0:
        print("⚠️  nodes 数组为空")

    # 检查节点
    node_ids = set()
    valid_types = {'data_source', 'compute', 'chart', 'image', 'tool'}

    for i, node in enumerate(data['nodes']):
        # 检查必需字段
        required_node_fields = ['node_id', 'type', 'name', 'depends_on', 'execution_status']
        for field in required_node_fields:
            if field not in node:
                print(f"❌ 节点 {i} 缺少字段: {field}")
                return False

        # 检查 node_id 唯一性
        if node['node_id'] in node_ids:
            print(f"❌ 节点 ID 重复: {node['node_id']}")
            return False
        node_ids.add(node['node_id'])

        # 检查 type
        if node['type'] not in valid_types:
            print(f"❌ 节点 {node['node_id']} 的 type 无效: {node['type']}")
            return False

        # 检查 depends_on
        for dep in node.get('depends_on', []):
            if dep not in node_ids and dep not in {n['node_id'] for n in data['nodes']}:
                print(f"❌ 节点 {node['node_id']} 依赖不存在的节点: {dep}")
                return False

    print("✅ project.json 验证通过！")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <project_dir>")
        sys.exit(1)

    project_dir = sys.argv[1]
    if validate_project_json(project_dir):
        sys.exit(0)
    else:
        sys.exit(1)
```

使用：
```bash
python validate_project.py projects/my_project
```

## 📊 对比：错误 vs 正确

### ❌ 错误格式

```json
{
  "project_id": "test",
  "name": "Test",
  "nodes": {
    "data_1": {
      "type": "datasource",
      "depends_on": ["nonexistent"]
    }
  }
}
```

**问题**：
1. `nodes` 是字典而不是数组
2. `type` 值拼写错误（`datasource` 应该 `data_source`）
3. 缺少必需字段
4. 依赖非法

### ✅ 正确格式

```json
{
  "project_id": "test",
  "name": "Test",
  "description": "",
  "version": "1.0.0",
  "created_at": "2025-11-17T10:00:00",
  "updated_at": "2025-11-17T10:00:00",
  "nodes": [
    {
      "node_id": "data_1",
      "type": "data_source",
      "name": "Data",
      "depends_on": [],
      "execution_status": "not_executed",
      "result_format": null,
      "result_path": null,
      "error_message": null,
      "last_execution_time": null
    }
  ]
}
```

## 需要帮助？

将你的 project.json 内容发出来，我可以帮你检查具体的问题！
