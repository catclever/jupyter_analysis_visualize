# API 端点文档

## 概述

Jupyter Analysis Visualize 后端 API 使用 FastAPI 框架，提供以下功能：
- 项目列表查询
- 项目元数据和 DAG 获取
- 节点结果数据分页查询
- 可视化文件流式传输

## 基础配置

**API 基础 URL**: `http://localhost:8000`

## 端点

### 1. 健康检查
```
GET /api/health
```

**响应**:
```json
{
  "status": "ok"
}
```

---

### 2. 列表所有项目
```
GET /api/projects
```

**响应示例**:
```json
{
  "projects": [
    {
      "id": "test_user_behavior_analysis",
      "name": "User Behavior Analysis",
      "description": "Analyze user behavior patterns from activity logs",
      "version": "1.0.0",
      "created_at": "2025-11-07T13:17:39.193531",
      "updated_at": "2025-11-07T13:17:39.214519"
    }
  ]
}
```

---

### 3. 获取项目详情（包含 DAG）
```
GET /api/projects/{project_id}
```

**参数**:
- `project_id` (path): 项目 ID，例如 `test_user_behavior_analysis`

**响应示例**:
```json
{
  "id": "test_user_behavior_analysis",
  "name": "User Behavior Analysis",
  "description": "Analyze user behavior patterns from activity logs",
  "version": "1.0.0",
  "created_at": "2025-11-07T13:17:39.193531",
  "updated_at": "2025-11-07T13:17:39.214519",
  "nodes": [
    {
      "id": "load_user_data",
      "label": "Load User Data",
      "type": "data",
      "execution_status": "validated",
      "result_format": "parquet",
      "result_path": "parquets/load_user_data.parquet"
    }
  ],
  "edges": [
    {
      "id": "e_load_user_data_merge_datasets",
      "source": "load_user_data",
      "target": "merge_datasets",
      "animated": true
    }
  ]
}
```

**节点类型**:
- `data`: 数据源节点
- `compute`: 计算/分析节点
- `chart`: 图表/可视化节点

---

### 4. 获取节点数据（带分页）
```
GET /api/projects/{project_id}/nodes/{node_id}/data
```

**参数**:
- `project_id` (path): 项目 ID
- `node_id` (path): 节点 ID
- `page` (query): 页码，默认为 1（1-indexed）
- `page_size` (query): 每页记录数，默认为 10，最大 1000

**响应示例 (Parquet)**:
```json
{
  "node_id": "load_user_data",
  "format": "parquet",
  "total_records": 100,
  "page": 1,
  "page_size": 5,
  "total_pages": 20,
  "columns": ["user_id", "age", "signup_date", "country", "premium"],
  "data": [
    {
      "user_id": 1,
      "age": 56,
      "signup_date": "2023-01-01T00:00:00",
      "country": "DE",
      "premium": true
    }
  ]
}
```

**响应示例 (JSON)**:
```json
{
  "node_id": "calculate_metrics",
  "format": "json",
  "total_records": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "data": {
    "total_sales": 4988695.0,
    "total_units": 52667.0,
    "average_deal_size": 55429.944444444445
  }
}
```

**响应示例 (Image/Visualization)**:
```json
{
  "node_id": "visualize_results",
  "format": "image",
  "file_path": "visualizations/visualize_results.png",
  "url": "/api/projects/{project_id}/nodes/{node_id}/image"
}
```

---

### 5. 获取图片文件
```
GET /api/projects/{project_id}/nodes/{node_id}/image
```

**参数**:
- `project_id` (path): 项目 ID
- `node_id` (path): 节点 ID

**响应**: PNG 图片文件（MIME type: `image/png`）

---

### 6. 获取可视化文件
```
GET /api/projects/{project_id}/nodes/{node_id}/visualization
```

**参数**:
- `project_id` (path): 项目 ID
- `node_id` (path): 节点 ID

**响应**: PNG 图表文件（MIME type: `image/png`）

---

## 错误处理

所有错误响应使用标准 HTTP 状态码：

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误或节点未执行 |
| 404 | 项目/节点/文件不存在 |
| 500 | 服务器错误 |

**错误响应示例**:
```json
{
  "detail": "Project test_invalid not found"
}
```

---

## 数据格式说明

### Parquet 格式
- 用于存储 DataFrame 结果
- API 自动分页返回
- 返回 `columns` 和 `data` 两个字段

### JSON 格式
- 用于存储字典、列表、统计数据
- 如果是列表，自动分页返回
- 如果是单个对象，作为单条记录返回

### Image/Visualization 格式
- 用于存储生成的图表（PNG）
- 返回文件元数据和下载 URL
- 前端可通过 URL 直接加载图片

---

## 使用示例

### 前端获取项目列表
```typescript
const projects = await fetch('http://localhost:8000/api/projects').then(r => r.json());
```

### 前端获取项目 DAG
```typescript
const project = await fetch(
  'http://localhost:8000/api/projects/test_user_behavior_analysis'
).then(r => r.json());

// 用于 FlowDiagram 组件
const nodes = project.nodes;
const edges = project.edges;
```

### 前端分页获取节点数据
```typescript
const data = await fetch(
  'http://localhost:8000/api/projects/test_user_behavior_analysis/nodes/load_user_data/data?page=1&page_size=10'
).then(r => r.json());

// 显示分页信息
console.log(`第 ${data.page}/${data.total_pages} 页，共 ${data.total_records} 条记录`);

// 填充数据表格
displayTableData(data.columns, data.data);
```

---

## 启动 API 服务器

```bash
cd jupyter_analysis_visualize/backend

# 使用 uv 运行
uv run python app.py

# 或者直接使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000
```

API 将在 http://localhost:8000 启动，文档可在 http://localhost:8000/docs 查看。
