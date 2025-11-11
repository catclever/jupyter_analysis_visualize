# 节点输出设计 - 简洁版

## 核心概念

每个节点类型都应该明确回答两个问题：

1. **这个节点的输出是什么？** (输出类型)
2. **这个输出在前端怎么展示？** (展示方式)

---

## 1. 节点类型与输出映射

### Data Source (数据源)

**输出是什么?**
- `pd.DataFrame` - 结构化表格数据

**前端怎么展示?**
- 表格组件 + 分页 + 列描述
- 自动推导: 检测到 DataFrame → 保存为 parquet → 前端渲染表格

**核心约束**:
- 必须返回 DataFrame
- 不允许返回其他类型

```python
# ✅ 正确
user_data = pd.read_csv('users.csv')

# ❌ 错误 - 不能返回字典
user_info = {'count': 1000}
```

---

### Compute (计算)

**输出是什么?**
- `pd.DataFrame` - 表格数据
- `dict` 或 `list` - 结构化数据（统计、聚合结果）

**前端怎么展示?**
- DataFrame → 表格组件 + 分页
- dict/list → JSON 查看器

**核心约束**:
- 要么返回 DataFrame（用于后续计算和可视化）
- 要么返回 dict/list（用于展示统计结果，不能被其他节点依赖）
- 不能混合（同一节点的不同分支）

```python
# ✅ 变体1：返回处理后的数据表
result = user_data.merge(activity_data, on='user_id')

# ✅ 变体2：返回统计结果
stats = {
    'total_records': 1000,
    'unique_users': 500,
    'avg_value': 123.45
}

# ❌ 错误：同一节点返回不同类型
if some_condition:
    return merged_df
else:
    return {'count': 100}
```

---

### Chart (图表)

**输出是什么?**
- `plotly.graph_objects.Figure` - Plotly 图表对象
- `dict` (ECharts 配置) - ECharts 图表配置

**前端怎么展示?**
- Plotly Figure → 自动转为 HTML → 前端嵌入 iframe 或用 Plotly.js 渲染
- ECharts dict → 前端用 echarts.js 库渲染

**核心约束**:
- 返回的对象必须能序列化为 HTML 或 JSON
- 不能返回其他类型（如 matplotlib 图片）

```python
# ✅ Plotly
import plotly.graph_objects as go
fig = go.Figure(data=[go.Bar(x=[1,2,3], y=[4,5,6])])

# ✅ ECharts
echarts_config = {
    'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', ...]},
    'yAxis': {'type': 'value'},
    'series': [{'data': [120, 200, ...], 'type': 'bar'}]
}

# ❌ 错误：Matplotlib
import matplotlib.pyplot as plt
plt.plot([1,2,3], [4,5,6])
plt.savefig('chart.png')
```

---

### Tool (工具库)

**输出是什么?**
- 函数对象（内存中存储）
- 不产生任何展示输出

**前端怎么展示?**
- 不展示（工具库只被其他节点调用）

**核心约束**:
- 入口函数名必须与 node_id 相同
- 不能有 depends_on（因为是工具库，应该无状态）
- 函数可以返回任何类型（DataFrame、dict、list 等）

```python
# ✅ 正确的工具定义
def data_processing(df, operation='normalize', **kwargs):
    if operation == 'normalize':
        return (df - df.mean()) / df.std()
    elif operation == 'fill_missing':
        return df.fillna(0)
    return df
```

---

## 2. 输出-展示对应关系

```
节点执行结果
    ↓
自动类型推导
    ↓
┌──────────────────────────────────┐
│                                  │
├─ DataFrame                       │
│  ↓                               │
│  保存为 parquet                  │
│  ↓                               │
│  前端: 表格 + 分页               │
│                                  │
├─ dict/list                       │
│  ↓                               │
│  保存为 json                     │
│  ↓                               │
│  前端: JSON 查看器               │
│                                  │
├─ Plotly Figure                   │
│  ↓                               │
│  保存为 html                     │
│  ↓                               │
│  前端: 嵌入内容或 Plotly.js      │
│                                  │
├─ dict (ECharts 配置)             │
│  ↓                               │
│  保存为 json                     │
│  ↓                               │
│  前端: echarts.js 库渲染         │
│                                  │
└─ 函数对象 (Tool)                 │
   ↓                               │
   内存中存储（不保存）            │
   ↓                               │
   前端: 不展示                    │
```

---

## 3. 元数据中的关键字段

### 原有字段（保持不变）

```json
{
  "node_id": "node_id",
  "node_type": "data_source|compute|chart|tool",
  "name": "Display Name",
  "depends_on": ["other_node_id"],
  "execution_status": "not_executed|pending_validation|validated"
}
```

### 新增字段（用于展示）

```json
{
  "output_type": "dataframe|dict_list|plotly|echarts|function",
  "display_type": "table|json_viewer|plotly_chart|echarts_chart|none"
}
```

#### 字段说明

| node_type | output_type | display_type | 说明 |
|-----------|------------|------------|------|
| data_source | dataframe | table | DataFrame 作为表格展示 |
| compute | dataframe | table | 处理后的数据表 |
| compute | dict_list | json_viewer | 统计结果作为 JSON 展示 |
| chart | plotly | plotly_chart | Plotly 图表 |
| chart | echarts | echarts_chart | ECharts 图表 |
| tool | function | none | 工具库，不展示 |

---

## 4. 前端展示逻辑（简化版）

```typescript
// 根据 output_type 和 display_type 选择展示组件

if (displayType === 'table') {
  return <DataTable data={data} columns={metadata.columns_info} />;
}

if (displayType === 'json_viewer') {
  return <JSONViewer data={data} />;
}

if (displayType === 'plotly_chart') {
  return <PlotlyChart htmlContent={data} />;
}

if (displayType === 'echarts_chart') {
  return <EChartsChart config={data} />;
}

if (displayType === 'none') {
  return <div>Tool library - not displayed</div>;
}
```

---

## 5. 实现方式

### 后端改动最小化

**不需要**:
- 创建新的 NodeOutput 类
- 复杂的包装逻辑
- 大量的 display_config

**需要**:
- 在执行结果后，自动推导 `output_type` 和 `display_type`
- 更新元数据保存这两个字段

```python
def execute_node(self, project_id, node_id):
    # ... 执行代码 ...
    result = node_result

    # 自动推导输出类型和展示类型
    output_info = self._infer_output_info(result, node_info)

    # 保存结果
    self.pm.save_node_result(project_id, node_id, result)

    # 更新元数据
    node_info['output_type'] = output_info['output_type']
    node_info['display_type'] = output_info['display_type']

def _infer_output_info(self, result, node_info):
    """自动推导输出类型和展示类型"""

    if isinstance(result, pd.DataFrame):
        return {
            'output_type': 'dataframe',
            'display_type': 'table'
        }

    elif isinstance(result, (dict, list)):
        return {
            'output_type': 'dict_list',
            'display_type': 'json_viewer'
        }

    elif isinstance(result, go.Figure):  # Plotly
        return {
            'output_type': 'plotly',
            'display_type': 'plotly_chart'
        }

    elif isinstance(result, dict) and 'xAxis' in result:  # ECharts
        return {
            'output_type': 'echarts',
            'display_type': 'echarts_chart'
        }

    elif callable(result):  # Tool
        return {
            'output_type': 'function',
            'display_type': 'none'
        }
```

### 前端改动最小化

**不需要**:
- 复杂的配置解析
- 自定义展示配置

**需要**:
- 根据 `display_type` 选择组件（简单的 switch/if 语句）

```typescript
// 在获取节点数据后
const response = await getNodeData(projectId, nodeId);

// 直接根据 display_type 渲染
const renderer = {
  'table': <DataTable />,
  'json_viewer': <JSONViewer />,
  'plotly_chart': <PlotlyChart />,
  'echarts_chart': <EChartsChart />,
  'none': null
}[response.display_type];
```

---

## 6. 节点编写规范

### Data Source - 清晰

```python
# ===== System-managed metadata =====
# @node_type: data_source
# @node_id: users
# @name: Load Users
# ===== End of system-managed metadata =====

import pandas as pd

# 必须返回 DataFrame
users = pd.read_csv('users.csv')
```

**约束**:
- ✅ 返回 DataFrame
- ❌ 不能返回 dict/list/其他类型

---

### Compute - 清晰

```python
# ===== System-managed metadata =====
# @node_type: compute
# @node_id: merged_data
# @depends_on: [users, activities]
# @name: Merge Data
# ===== End of system-managed metadata =====

import pandas as pd

# 选项1：返回 DataFrame（用于后续计算）
merged = users.merge(activities, on='user_id')

# 选项2：返回 dict/list（用于展示统计）
# stats = {
#     'total': 1000,
#     'unique_users': 500
# }
```

**约束**:
- ✅ 返回 DataFrame 或 dict/list，二选一
- ❌ 不能在同一节点内混合返回不同类型

---

### Chart - 清晰

```python
# ===== System-managed metadata =====
# @node_type: chart
# @node_id: sales_chart
# @depends_on: [merged_data]
# @name: Sales Chart
# ===== End of system-managed metadata =====

import plotly.graph_objects as go

# 选项1：Plotly
fig = go.Figure(data=[go.Bar(x=[1,2,3], y=[4,5,6])])

# 选项2：ECharts
# fig = {
#     'xAxis': {'type': 'category', 'data': [...]}
#     'yAxis': {'type': 'value'},
#     'series': [{'data': [...], 'type': 'bar'}]
# }
```

**约束**:
- ✅ 返回 Plotly Figure 或 ECharts dict
- ❌ 不能返回其他图表库（matplotlib 等）

---

### Tool - 清晰

```python
# ===== System-managed metadata =====
# @node_type: tool
# @node_id: data_processing
# @name: Data Processing Utils
# ===== End of system-managed metadata =====

def _normalize(df):
    return (df - df.mean()) / df.std()

def _fill_missing(df):
    return df.fillna(0)

# 入口函数 - 必须与 node_id 相同
def data_processing(df, operation='normalize', **kwargs):
    if operation == 'normalize':
        return _normalize(df)
    elif operation == 'fill_missing':
        return _fill_missing(df)
    return df
```

**约束**:
- ✅ 定义入口函数，名称与 node_id 相同
- ✅ 函数可以返回任何类型
- ❌ 不能有 depends_on
- ❌ 不能在 node_id 外定义全局变量

---

## 7. 迁移步骤

### Step 1: 收集现有节点的输出信息

```python
# 遍历所有项目和节点
from backend.project_manager import ProjectManager

for project_id in os.listdir('projects'):
    pm = ProjectManager('projects', project_id)
    pm.load()

    for node_id, node_info in pm.metadata.nodes.items():
        print(f"{project_id}/{node_id}: {node_info['type']}")
        # 手动检查或运行节点查看输出类型
```

### Step 2: 为每个节点添加输出类型注解

修改 metadata_parser.py，在解析时就记录输出类型：

```python
# 或通过执行后自动推导
output_info = infer_output_info(node_result, node_info)
node_info['output_type'] = output_info['output_type']
node_info['display_type'] = output_info['display_type']
```

### Step 3: 更新 API 返回格式

添加 `output_type` 和 `display_type` 字段到 API 响应：

```python
@app.get("/api/projects/{project_id}/nodes/{node_id}/data")
async def get_node_data(project_id, node_id):
    pm = ProjectManager('projects', project_id)
    pm.load()

    node_info = pm.metadata.nodes[node_id]
    data = pm.load_node_result(node_id)

    return {
        'node_id': node_id,
        'output_type': node_info['output_type'],
        'display_type': node_info['display_type'],
        'data': data,
        'pagination': {...}  # 仅 table 类型有
    }
```

### Step 4: 更新前端渲染

```typescript
// components/NodeResultViewer.tsx
export const NodeResultViewer = ({ response }) => {
  const { displayType, data } = response;

  switch (displayType) {
    case 'table':
      return <DataTable data={data} pagination={response.pagination} />;
    case 'json_viewer':
      return <JSONViewer data={data} />;
    case 'plotly_chart':
      return <PlotlyChart html={data} />;
    case 'echarts_chart':
      return <EChartsChart config={data} />;
    case 'none':
      return <div>Tool library (no output to display)</div>;
    default:
      return <div>Unknown display type: {displayType}</div>;
  }
};
```

---

## 8. 验证清单

### 对每个节点检查

- [ ] 节点类型明确 (data_source/compute/chart/tool)
- [ ] 输出类型确定 (dataframe/dict_list/plotly/echarts/function)
- [ ] 展示方式对应 (table/json_viewer/plotly_chart/echarts_chart/none)

### 对后端检查

- [ ] 结果保存格式正确 (parquet/json/html)
- [ ] 元数据包含 output_type 和 display_type
- [ ] API 返回包含这两个字段

### 对前端检查

- [ ] NodeResultViewer 支持所有 display_type
- [ ] 各类型组件工作正常
- [ ] 分页、搜索等功能正常

---

## 9. 对比：之前 vs 现在

### 之前的问题

```python
# 不清楚输出什么
result = some_function()

# 前端不知道怎么展示
if node['type'] == 'data_source':
    # 假设是 DataFrame？但不确定
    render_table(result)
```

### 现在的方案

```python
# 清楚地知道输出什么
result = pd.read_csv(...)  # DataFrame

# 后端自动推导
node['output_type'] = 'dataframe'
node['display_type'] = 'table'

# 前端明确知道怎么展示
if node['display_type'] == 'table':
    render_table(result)
```

---

## 10. 总结

### 核心改进

1. **清晰的输出约束** - 每个节点类型明确输出什么
2. **自动推导机制** - 后端自动判断 output_type 和 display_type
3. **前端智能渲染** - 根据 display_type 选择组件
4. **最小改动** - 不需要复杂的类和配置系统

### 实现成本

| 组件 | 改动量 | 复杂度 |
|------|--------|--------|
| 后端 | 中等 | 低 |
| 前端 | 小 | 低 |
| 文档 | 中等 | 低 |

### 收益

- ✅ 开发者：清晰的约束，更少错误
- ✅ 用户：更好的展示，自适应渲染
- ✅ 维护者：容易理解和扩展
