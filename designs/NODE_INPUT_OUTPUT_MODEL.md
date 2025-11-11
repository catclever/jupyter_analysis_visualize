# 节点输入/输出模型设计

## 🎯 核心改变

不仅要规范**输出**，还要规范**输入**！

```
现在的视角（只看输出）：
  节点执行 → 输出结果 → 前端展示
  ❌ 缺少对输入的考虑，节点之间的流转不清晰

新视角（输入+处理+输出）：
  输入数据 → 节点处理 → 输出结果
  ✅ 清晰的数据流，完整的节点定义
```

---

## 1. 节点的完整定义

每个节点都应该明确：

1. **输入是什么?** (Input Type)
   - 有多少个输入？
   - 每个输入的数据类型是什么？

2. **节点做什么?** (Processing Type)
   - 节点的功能是什么？
   - 处理的业务逻辑是什么？

3. **输出是什么?** (Output Type)
   - 输出什么类型的数据？
   - 输出在前端怎么展示？

---

## 2. 输入类型分类

### 2.1 输入来源分类

```
NodeInput
  ├─ SourceInput (数据源)
  │   ├─ FileSource: CSV, JSON, Excel, Parquet
  │   ├─ DatabaseSource: SQL Query, MongoDB, Redis
  │   ├─ APISource: REST API, GraphQL
  │   └─ StreamSource: Kafka, PubSub (未来)
  │
  ├─ DependencyInput (依赖的节点输出)
  │   ├─ SingleInput: 单个节点的输出
  │   ├─ MultipleInput: 多个节点的输出
  │   └─ ConditionalInput: 条件性依赖 (未来)
  │
  └─ ParameterInput (用户参数)
      ├─ StaticParameter: 固定值参数
      ├─ DynamicParameter: 运行时参数 (未来)
      └─ ConfigParameter: 配置参数
```

### 2.2 输入数据类型

```
InputDataType
  ├─ DataFrame: 结构化表格数据
  ├─ Dict/List: 非结构化数据
  ├─ Scalar: 标量值（数字、字符串）
  ├─ Model: 机器学习模型对象
  ├─ File: 文件路径或二进制数据
  ├─ Function: 函数对象（from Tool）
  └─ Stream: 数据流 (未来)
```

---

## 3. 节点类型完整定义

### 数据源节点 (Data Source)

```python
# 输入: 无
# 处理: 从外部源加载数据
# 输出: DataFrame | Dict | List

class DataSourceNode:
    input_count = 0
    input_types = []

    output_type = 'data'
    output_subtype = 'table' | 'record' | 'dict'

    # 节点属性
    source_type = 'csv' | 'database' | 'api' | 'stream'
    source_config = {...}  # 数据源配置

    # 在图上的表示
    icon = 'database' | 'file' | 'cloud'
    color = 'green'  # 标识数据源
```

**例子**:
```python
# @node_type: data_source
# @source_type: csv
# @source_config: {"path": "users.csv", "encoding": "utf-8"}

import pandas as pd

users = pd.read_csv('users.csv')
```

**图上显示**:
```
┌─────────────────┐
│ 📁 users.csv    │  ← 绿色框，特殊图标
│  (Data Source)  │
└────────┬────────┘
         │ DataFrame (10000 rows × 5 cols)
         ↓
```

---

### 处理节点 (Processing)

```python
# 输入: 1+ 个节点的输出 (必须是 DataFrame)
# 处理: 转换和处理数据
# 输出: DataFrame (用于后续计算/可视化)

class ProcessingNode:
    input_count = '1+'
    input_types = ['DataFrame']  # 严格约束

    depends_on = ['node_id1', 'node_id2', ...]  # 明确依赖

    output_type = 'data'
    output_subtype = 'table'  # 只能是表格，不能是统计结果！

    # 在图上的表示
    icon = 'gear'
    color = 'blue'
```

**例子**:
```python
# @node_type: processing
# @depends_on: [users, activities]

merged = users.merge(activities, on='user_id')
# ✅ 返回 DataFrame，可被其他节点依赖
```

**约束**:
- ❌ 不能返回 dict（即使是统计）
- ❌ 不能返回单个数值
- ✅ 必须返回 DataFrame

**图上显示**:
```
users (DataFrame)  activities (DataFrame)
   │                    │
   └────────┬───────────┘
            ↓
    ┌──────────────────┐
    │ ⚙️ merge_data    │
    │ (Processing)     │
    └────────┬─────────┘
             │ DataFrame (5000 rows × 8 cols)
             ↓
```

---

### 分析节点 (Analysis)

```python
# 输入: 1+ 个节点的输出 (可以是任何类型)
# 处理: 计算统计指标和分析结果
# 输出: Dict | Scalar (仅用于展示，不能被其他节点依赖)

class AnalysisNode:
    input_count = '1+'
    input_types = ['DataFrame', 'Dict', 'List', 'Scalar']  # 灵活

    depends_on = ['node_id1', ...]

    output_type = 'metric' | 'analysis'
    output_subtype = 'dict' | 'scalar' | 'list'

    # 在图上的表示
    icon = 'chart-bar'
    color = 'orange'

    # 标记：这个节点的输出不能被依赖
    is_leaf_node = True  # 不能被其他节点依赖
```

**例子**:
```python
# @node_type: analysis
# @depends_on: [merged_data]

stats = {
    'total_records': len(merged_data),
    'unique_users': merged_data['user_id'].nunique(),
    'avg_value': merged_data['value'].mean()
}
# ✅ 返回 dict，仅用于展示
```

**约束**:
- ✅ 可以返回 dict、scalar、list
- ❌ 输出不能被其他节点的 depends_on 引用
- ✅ 但可以被可视化节点使用

**图上显示** (用虚线表示是叶子节点):
```
merged_data (DataFrame)
    │
    ↓
┌──────────────────┐
│ 📊 statistics    │ ← 虚线框，标记为分析节点
│ (Analysis)       │
└──────────────────┘
     (不能被依赖)
```

---

### 可视化节点 (Visualization)

```python
# 输入: 1+ 个节点的输出 (任何类型)
# 处理: 生成图表和可视化
# 输出: Plotly Figure | ECharts Dict | Custom

class VisualizationNode:
    input_count = '1+'
    input_types = ['DataFrame', 'Dict', 'Scalar', 'List']

    depends_on = ['node_id1', ...]

    output_type = 'visualization'
    output_subtype = 'plotly' | 'echarts' | 'custom'

    # 在图上的表示
    icon = 'image'
    color = 'purple'

    # 标记：这个节点通常是叶子节点
    is_leaf_node = True
```

**例子**:
```python
# @node_type: visualization
# @depends_on: [statistics, merged_data]

import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(x=merged_data['date'], y=merged_data['value'])
])
```

**约束**:
- ✅ 可以依赖任何节点
- ❌ 输出通常不被其他节点依赖
- ✅ 但在理论上可以被未来的"导出节点"依赖

**图上显示**:
```
statistics (Dict)  merged_data (DataFrame)
   │                    │
   └────────┬───────────┘
            ↓
    ┌──────────────────┐
    │ 🖼️ sales_chart   │
    │ (Visualization)  │
    └──────────────────┘
         (叶子节点)
```

---

### 工具节点 (Tool)

```python
# 输入: 无（或配置参数）
# 处理: 定义可复用函数
# 输出: Function Object (内存中存储)

class ToolNode:
    input_count = 0
    input_types = []

    depends_on = []  # Tool 不能依赖其他节点（无状态）

    output_type = 'function'
    output_subtype = 'function'

    # 在图上的表示
    icon = 'wrench'
    color = 'gray'

    # 标记：这是一个工具库，特殊处理
    is_tool = True
    is_leaf_node = False  # 可以被其他节点调用
```

**例子**:
```python
# @node_type: tool

def _normalize(df):
    return (df - df.mean()) / df.std()

def data_processing(df, operation='normalize', **kwargs):
    if operation == 'normalize':
        return _normalize(df)
    # ...
```

**约束**:
- ❌ 不能有 depends_on
- ✅ 函数名必须与 node_id 相同
- ✅ 可以被其他节点调用

**图上显示** (虚线框表示是工具库):
```
┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐
│ 🔧 data_processing │  ← 虚线框，表示工具库
│    (Tool)           │     不在主流中
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘
     (被其他节点调用)
```

---

## 4. 节点在图上的表示

### 4.1 节点类型的视觉区分

```
数据源节点 (Data Source)        处理节点 (Processing)
┌─────────────────┐             ┌─────────────────┐
│ 📁 data_source  │             │ ⚙️  processing  │
│   Data Source   │             │  Processing     │
└────────┬────────┘             └────────┬────────┘
         │                               │
     绿色框                           蓝色框
  特殊数据库图标                    齿轮图标


分析节点 (Analysis)              可视化节点 (Visualization)
┌─ ─ ─ ─ ─ ─ ─ ─┐               ┌─────────────────┐
│ 📊 analysis   │               │ 🖼️ visualization│
│   Analysis    │               │ Visualization   │
└─ ─ ─ ─ ─ ─ ─ ─┘               └─────────────────┘
   虚线框+橙色                      紫色框
   标记为分析                       可视化图标


工具节点 (Tool)
┌─ ─ ─ ─ ─ ─ ─ ─┐
│ 🔧 tool       │
│    Tool       │
└─ ─ ─ ─ ─ ─ ─ ─┘
   虚线框+灰色
   工具库图标
```

### 4.2 图的流向示例

```
完整的数据分析流程：

┌─────────────────┐
│ 📁 users        │  ← 数据源节点（绿色）
│  Data Source    │
└────────┬────────┘
         │ DataFrame
         ↓
    ┌──────────────┐
    │ ⚙️ merged    │  ← 处理节点（蓝色）
    │ Processing   │
    └────────┬─────┘
             │ DataFrame
             ↓
    ┌─ ─ ─ ─ ─ ─ ─┐
    │ 📊 stats    │  ← 分析节点（虚线）
    │ Analysis    │
    └─ ─ ─ ─ ─ ─ ─┘
             │ Dict
             ↓
    ┌──────────────────┐
    │ 🖼️ chart        │  ← 可视化节点（紫色）
    │ Visualization    │
    └──────────────────┘

依赖关系清晰：
- 数据源 → 可被任何节点依赖
- 处理 → 可被处理/分析/可视化依赖
- 分析 → 只能被可视化依赖（虚线箭头）
- 可视化 → 通常是叶子节点
- 工具 → 被其他节点调用（特殊处理）
```

---

## 5. 元数据中的输入/输出定义

### 5.1 完整的节点元数据

```json
{
  "node_id": "merged_data",
  "node_type": "processing",
  "name": "Merge Datasets",

  "input": {
    "count": 2,
    "items": [
      {
        "source": "node",
        "node_id": "users",
        "data_type": "dataframe"
      },
      {
        "source": "node",
        "node_id": "activities",
        "data_type": "dataframe"
      }
    ]
  },

  "output": {
    "type": "data",
    "subtype": "table",
    "data_type": "dataframe",
    "shape": [5000, 8],
    "description": "Merged user and activity data"
  },

  "depends_on": ["users", "activities"],
  "execution_status": "validated",

  "display_config": {
    "icon": "gear",
    "color": "blue",
    "is_leaf_node": false
  }
}
```

### 5.2 数据源节点特殊定义

```json
{
  "node_id": "user_data",
  "node_type": "data_source",
  "name": "Load Users",

  "input": {
    "source": "file",
    "source_type": "csv",
    "path": "data/users.csv",
    "config": {
      "encoding": "utf-8",
      "sep": ",",
      "index_col": 0
    }
  },

  "output": {
    "type": "data",
    "subtype": "table",
    "data_type": "dataframe",
    "shape": [10000, 5],
    "columns": ["user_id", "name", "email", "age", "created_at"]
  },

  "depends_on": [],  // 数据源不依赖任何节点

  "display_config": {
    "icon": "database",
    "color": "green",
    "is_leaf_node": false
  }
}
```

---

## 6. 前端渲染中的输入/输出表示

### 6.1 节点卡片设计

```
┌──────────────────────────────────────────────┐
│ 📁 users                                     │  ← 节点类型图标
│ Data Source                                  │
├──────────────────────────────────────────────┤
│ Input:                                       │
│  • CSV file: users.csv (10000 rows × 5 cols)│
├──────────────────────────────────────────────┤
│ Output:                                      │
│  • DataFrame: 10000 rows × 5 columns         │
│    - user_id, name, email, age, created_at  │
├──────────────────────────────────────────────┤
│ [🔄 Refresh] [📊 Preview] [💾 Download]    │
└──────────────────────────────────────────────┘


┌──────────────────────────────────────────────┐
│ ⚙️ merged_data                               │
│ Processing                                   │
├──────────────────────────────────────────────┤
│ Input:                                       │
│  • users (DataFrame)                         │
│  • activities (DataFrame)                    │
├──────────────────────────────────────────────┤
│ Output:                                      │
│  • DataFrame: 5000 rows × 8 columns          │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ Depends on: [users, activities]              │
├──────────────────────────────────────────────┤
│ [🔄 Execute] [📊 View Data] [🔗 Dependencies]│
└──────────────────────────────────────────────┘
```

### 6.2 DAG 图中的输入输出流

```typescript
// 前端显示完整的数据流

节点间的箭头应该标注数据类型：

users ──────(DataFrame 10000×5)────→ merged_data

activities ──(DataFrame 8000×4)─┘

merged_data ─────(DataFrame 5000×8)───→ chart
                    ↓
              statistics (Dict)
                    │
                    └────────→ chart
```

---

## 7. 约束总结表

| 节点类型 | 输入来源 | 输入数据类型 | 输出类型 | 输出子类型 | 依赖其他节点? | 能被依赖? | 叶子节点? |
|---------|--------|----------|-------|---------|-----------|---------|---------|
| data_source | 文件/DB/API | N/A | data | table | ❌ | ✅ | ❌ |
| processing | 节点输出 | DataFrame | data | table | ✅ | ✅ | ❌ |
| analysis | 节点输出 | Any | metric | dict/scalar | ✅ | ⚠️(虚线) | ✅ |
| visualization | 节点输出 | Any | visualization | plotly/echarts | ✅ | ❌ | ✅ |
| tool | 无 | N/A | function | function | ❌ | ⚠️(调用) | N/A |

---

## 8. 实现建议

### 立即改进（基础设计）

在现有系统中添加：

1. **节点类型细分**
   ```json
   {
     "node_type": "compute",  // 保持兼容
     "node_purpose": "processing" | "analysis",  // 新字段
     "output_subtype": "table" | "dict"
   }
   ```

2. **输入元数据**
   ```json
   {
     "input": {
       "source": "file" | "node" | "parameter",
       "node_id": "...",  // 如果是节点输入
       "data_type": "dataframe" | "dict" | "scalar"
     }
   }
   ```

3. **前端显示优化**
   - 数据源节点显示绿色 + 特殊图标
   - 分析节点显示虚线框 + 警告标记
   - 箭头上标注数据类型

### 中期完善（架构升级）

1. 创建完整的输入/输出类型系统
2. 实现节点验证（输入输出类型匹配）
3. 增强图可视化（显示数据流信息）

### 长期演进（生态发展）

1. 支持新的节点类型（ML/导出/评估等）
2. 参数化输入支持
3. 条件依赖支持

---

## 总结

### 关键改变

```
现在（只看输出）：
  节点1 → 输出 → 展示
  节点2 → 输出 → 展示
  问题：不知道节点间的关系，数据流不清晰

之后（输入+处理+输出）：
  数据源 ──(DataFrame)──→ 处理 ──(DataFrame)──→ 分析 ──(Dict)──→ 可视化
                                                                    ↑
  输入明确 → 处理清晰 → 输出规范 → 依赖清晰 → 图清晰 ───────────────┘
```

### 收益

✅ 清晰的数据流
✅ 清晰的节点定义
✅ 清晰的节点间关系
✅ 清晰的依赖约束
✅ 易于可视化和调试
✅ 易于扩展新节点类型

---

> 💡 完整的节点模型 = 清晰的输入 + 明确的处理 + 规范的输出
