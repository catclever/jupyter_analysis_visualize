# 节点规范化 - 实现步骤

## 实现总览

```
Phase 1 (后端推导)          Phase 2 (前端渲染)         Phase 3 (验证优化)
├─ 添加推导函数             ├─ 创建通用渲染器         ├─ 全面测试
├─ 更新元数据保存           ├─ 更新 API 响应         ├─ 性能优化
├─ 测试现有节点             ├─ 整合到 UI              └─ 文档完善
└─ 收集现有项目信息         └─ 验证各节点显示
```

---

## Phase 1: 后端改动 (2-3天)

### 1.1 添加输出推导函数

**文件**: `backend/execution_manager.py`

**在 `execute_node()` 方法中添加**:

```python
def execute_node(self, project_id: str, node_id: str, skip_existing: bool = True):
    """Execute a single node and save results"""

    # ... 现有的执行代码 ...

    result = node_result  # 节点执行的结果

    # ✨ NEW: 自动推导输出类型
    output_info = self._infer_output_type(result, node_type)

    # 保存结果
    self.pm.save_node_result(project_id, node_id, result)

    # ✨ NEW: 更新元数据
    node = self.pm.metadata.nodes[node_id]
    node['output_type'] = output_info['output_type']
    node['display_type'] = output_info['display_type']

    return {
        'status': 'success',
        'output_type': output_info['output_type'],
        'display_type': output_info['display_type']
    }


def _infer_output_type(self, result, node_type: str) -> Dict[str, str]:
    """
    Infer output type and display type from result.

    Returns:
        Dict with keys: 'output_type', 'display_type'
    """
    import pandas as pd
    import plotly.graph_objects as go

    # Tool 节点：函数对象
    if node_type == 'tool':
        return {
            'output_type': 'function',
            'display_type': 'none'
        }

    # DataFrame
    if isinstance(result, pd.DataFrame):
        return {
            'output_type': 'dataframe',
            'display_type': 'table'
        }

    # dict 或 list（统计数据）
    if isinstance(result, (dict, list)):
        return {
            'output_type': 'dict_list',
            'display_type': 'json_viewer'
        }

    # Plotly Figure
    if isinstance(result, go.Figure):
        return {
            'output_type': 'plotly',
            'display_type': 'plotly_chart'
        }

    # ECharts 配置 (dict with specific structure)
    if isinstance(result, dict) and ('xAxis' in result or 'series' in result):
        return {
            'output_type': 'echarts',
            'display_type': 'echarts_chart'
        }

    # 默认为 JSON
    return {
        'output_type': 'dict_list',
        'display_type': 'json_viewer'
    }
```

### 1.2 更新 API 响应

**文件**: `backend/app.py`

**修改 `get_node_data()` 端点**:

```python
@app.get("/api/projects/{project_id}/nodes/{node_id}/data")
async def get_node_data(
    project_id: str,
    node_id: str,
    page: int = 1,
    page_size: int = 50
):
    """Get node result data with output type information"""

    pm = ProjectManager('projects', project_id)
    pm.load()

    node_info = pm.metadata.nodes[node_id]
    data = pm.load_node_result(node_id)

    # ✨ NEW: 构建响应对象
    response = {
        'node_id': node_id,
        'node_type': node_info['type'],
        'output_type': node_info.get('output_type', 'unknown'),
        'display_type': node_info.get('display_type', 'none'),
        'data': data
    }

    # 添加分页信息（仅表格类型）
    if node_info.get('display_type') == 'table' and isinstance(data, pd.DataFrame):
        total_records = len(data)
        total_pages = (total_records + page_size - 1) // page_size

        if page < 1 or page > total_pages:
            raise HTTPException(status_code=400, detail="Invalid page number")

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        response['pagination'] = {
            'current_page': page,
            'total_pages': total_pages,
            'page_size': page_size,
            'total_records': total_records
        }

        response['data'] = data.iloc[start_idx:end_idx].to_dict('records')

    return response
```

**也需要更新 `get_project()` 端点**:

```python
@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project metadata with node output information"""

    pm = ProjectManager('projects', project_id)
    pm.load()

    project_info = pm.get_project_info()

    # ✨ NEW: 为每个节点添加展示信息
    project_info['nodes'] = []
    for node_id, node_meta in pm.metadata.nodes.items():
        project_info['nodes'].append({
            'id': node_id,
            'name': node_meta['name'],
            'type': node_meta['type'],
            'output_type': node_meta.get('output_type', 'unknown'),
            'display_type': node_meta.get('display_type', 'none'),
            'depends_on': node_meta['depends_on'],
            'execution_status': node_meta['execution_status']
        })

    # ... DAG 信息保持不变 ...

    return project_info
```

### 1.3 验证改动

**测试脚本**: `backend/test_output_inference.py` (新建)

```python
"""Test output type inference"""

import pandas as pd
import plotly.graph_objects as go
from execution_manager import ExecutionManager

def test_inference():
    em = ExecutionManager('projects')

    # Test 1: DataFrame
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    result = em._infer_output_type(df, 'data_source')
    assert result['output_type'] == 'dataframe'
    assert result['display_type'] == 'table'

    # Test 2: dict
    data = {'count': 100, 'mean': 50.5}
    result = em._infer_output_type(data, 'compute')
    assert result['output_type'] == 'dict_list'
    assert result['display_type'] == 'json_viewer'

    # Test 3: Plotly
    fig = go.Figure(data=[go.Bar(x=[1, 2], y=[3, 4])])
    result = em._infer_output_type(fig, 'chart')
    assert result['output_type'] == 'plotly'
    assert result['display_type'] == 'plotly_chart'

    # Test 4: ECharts
    echarts = {
        'xAxis': {'type': 'category'},
        'yAxis': {'type': 'value'},
        'series': [{'data': [1, 2, 3], 'type': 'bar'}]
    }
    result = em._infer_output_type(echarts, 'chart')
    assert result['output_type'] == 'echarts'
    assert result['display_type'] == 'echarts_chart'

    print("✓ All inference tests passed")

if __name__ == '__main__':
    test_inference()
```

**运行测试**:
```bash
cd backend
python test_output_inference.py
```

---

## Phase 2: 前端改动 (2-3天)

### 2.1 创建通用渲染器

**文件**: `frontend/src/components/NodeResultViewer.tsx` (新建)

```typescript
import React from 'react';
import { DataTable } from './DataTable';
import { JSONViewer } from './JSONViewer';
import { PlotlyViewer } from './PlotlyViewer';
import { EChartsViewer } from './EChartsViewer';

interface NodeDataResponse {
  node_id: string;
  node_type: string;
  output_type: 'dataframe' | 'dict_list' | 'plotly' | 'echarts' | 'function';
  display_type: 'table' | 'json_viewer' | 'plotly_chart' | 'echarts_chart' | 'none';
  data: any;
  pagination?: {
    current_page: number;
    total_pages: number;
    page_size: number;
    total_records: number;
  };
}

interface NodeResultViewerProps {
  response: NodeDataResponse;
}

export const NodeResultViewer: React.FC<NodeResultViewerProps> = ({ response }) => {
  const { display_type, data, pagination } = response;

  // 根据 display_type 选择展示组件
  switch (display_type) {
    case 'table':
      return (
        <DataTable
          data={data}
          pagination={pagination}
        />
      );

    case 'json_viewer':
      return <JSONViewer data={data} />;

    case 'plotly_chart':
      return <PlotlyViewer data={data} />;

    case 'echarts_chart':
      return <EChartsViewer config={data} />;

    case 'none':
      return (
        <div className="text-gray-500 text-center py-8">
          Tool library - no output to display
        </div>
      );

    default:
      return (
        <div className="text-red-500">
          Unknown display type: {display_type}
        </div>
      );
  }
};
```

### 2.2 实现具体的 Viewer 组件

**文件**: `frontend/src/components/viewers/PlotlyViewer.tsx` (新建)

```typescript
import React, { useEffect } from 'react';

interface PlotlyViewerProps {
  data: any;  // Plotly HTML string or config
}

export const PlotlyViewer: React.FC<PlotlyViewerProps> = ({ data }) => {
  // 如果是 HTML 字符串，使用 iframe
  if (typeof data === 'string') {
    return (
      <div className="w-full h-96">
        <iframe
          srcDoc={data}
          className="w-full h-full border-0"
          title="Plotly Chart"
        />
      </div>
    );
  }

  // 否则假设是 JSON 配置，使用 Plotly.js
  return (
    <div id="plotly-chart" className="w-full h-96" />
  );
};
```

**文件**: `frontend/src/components/viewers/EChartsViewer.tsx` (新建)

```typescript
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface EChartsViewerProps {
  config: any;  // ECharts configuration
}

export const EChartsViewer: React.FC<EChartsViewerProps> = ({ config }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const myChart = echarts.init(chartRef.current);
    myChart.setOption(config);

    // 处理窗口resize
    const handleResize = () => myChart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      myChart.dispose();
    };
  }, [config]);

  return <div ref={chartRef} className="w-full h-96" />;
};
```

### 2.3 更新 API 服务

**文件**: `frontend/src/services/api.ts`

```typescript
// 添加新的类型定义
export interface NodeDataResponse {
  node_id: string;
  node_type: string;
  output_type: string;
  display_type: string;
  data: any;
  pagination?: {
    current_page: number;
    total_pages: number;
    page_size: number;
    total_records: number;
  };
}

// 修改 getNodeData 函数
export const getNodeData = async (
  projectId: string,
  nodeId: string,
  page: number = 1,
  pageSize: number = 50
): Promise<NodeDataResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/nodes/${nodeId}/data?page=${page}&page_size=${pageSize}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch node data: ${response.statusText}`);
  }

  return response.json();
};
```

### 2.4 整合到现有 UI

**文件**: `frontend/src/pages/Index.tsx` (修改)

```typescript
// 在节点详情面板中使用新的渲染器
import { NodeResultViewer } from '@/components/NodeResultViewer';

export const AnalysisSidebar = ({ selectedNode }) => {
  const [nodeData, setNodeData] = useState<NodeDataResponse | null>(null);

  useEffect(() => {
    if (!selectedNode) return;

    getNodeData(projectId, selectedNode.id)
      .then(setNodeData)
      .catch(console.error);
  }, [selectedNode, projectId]);

  return (
    <div className="sidebar">
      {/* 节点信息头 */}
      <div className="node-header">
        <h3>{selectedNode?.name}</h3>
        <p className="text-sm text-gray-500">Type: {selectedNode?.type}</p>
      </div>

      {/* ✨ 使用新的通用渲染器 */}
      {nodeData && <NodeResultViewer response={nodeData} />}

      {/* 节点代码、文档等其他标签页 */}
      <div className="node-tabs">
        {/* ... 保持原有内容 ... */}
      </div>
    </div>
  );
};
```

### 2.5 验证改动

**检查清单**:
- [ ] DataTable 组件显示正常
- [ ] JSONViewer 显示正常
- [ ] PlotlyViewer 显示正常
- [ ] EChartsViewer 显示正常
- [ ] 分页功能正常
- [ ] 响应式布局正常

---

## Phase 3: 验证优化 (1-2天)

### 3.1 全面测试

**手动测试流程**:

1. **测试 Data Source 节点**
   ```bash
   # 访问 http://localhost:5173
   # 选择 test_user_behavior_analysis 项目
   # 点击 user_data 节点
   # 验证：显示表格，有分页
   ```

2. **测试 Compute 节点（返回 DataFrame）**
   ```bash
   # 点击 merged_data 节点
   # 验证：显示表格，可分页，有列描述
   ```

3. **测试 Compute 节点（返回 dict）**
   ```bash
   # 点击 statistics 节点
   # 验证：显示 JSON 查看器，格式化的数据
   ```

4. **测试 Chart 节点**
   ```bash
   # 如果有 chart 节点，点击它
   # 验证：显示图表，可交互
   ```

5. **测试 Tool 节点**
   ```bash
   # 如果有 tool 节点，点击它
   # 验证：显示"Tool library - no output to display"
   ```

### 3.2 性能优化

**如果数据很大**:

```python
# 后端：限制单次返回的记录数
MAX_PREVIEW_RECORDS = 1000

if len(data) > MAX_PREVIEW_RECORDS:
    response['data'] = data.iloc[:MAX_PREVIEW_RECORDS].to_dict('records')
    response['note'] = f'Showing first {MAX_PREVIEW_RECORDS} of {len(data)} records'
```

**前端**:
```typescript
// 虚拟滚动优化大列表
import { FixedSizeList } from 'react-window';

// 在 DataTable 中使用虚拟滚动
<FixedSizeList
  height={400}
  itemCount={data.length}
  itemSize={35}
>
  {({ index, style }) => (
    <div style={style}>{/* row content */}</div>
  )}
</FixedSizeList>
```

### 3.3 文档更新

更新以下文档：
- `README.md` - 添加"节点输出展示"章节
- `backend/API_DESIGN.md` - 更新 API 响应格式说明
- `designs/NODE_OUTPUT_DESIGN.md` - 保留作为参考

---

## 实施检查清单

### 后端完成

- [ ] 添加 `_infer_output_type()` 方法
- [ ] 修改 `execute_node()` 调用推导函数
- [ ] 更新 `get_node_data()` API 端点
- [ ] 更新 `get_project()` API 端点
- [ ] 创建并运行推导测试
- [ ] 测试现有项目是否兼容
- [ ] 更新 Swagger/API 文档

### 前端完成

- [ ] 创建 `NodeResultViewer` 组件
- [ ] 创建 `PlotlyViewer` 组件
- [ ] 创建 `EChartsViewer` 组件
- [ ] 更新 API 服务类型定义
- [ ] 整合到现有 UI
- [ ] 测试各类型展示
- [ ] 验证响应式设计

### 优化完成

- [ ] 性能优化（大数据）
- [ ] 错误处理完善
- [ ] 文档更新
- [ ] 全面回归测试

---

## 时间估算

| 任务 | 时间 | 难度 |
|------|------|------|
| 后端推导函数 | 4h | ⭐ |
| 后端 API 更新 | 2h | ⭐ |
| 后端测试 | 2h | ⭐ |
| 前端组件 | 4h | ⭐⭐ |
| 前端整合 | 2h | ⭐ |
| 前端测试 | 3h | ⭐ |
| 性能优化 | 2h | ⭐⭐ |
| 文档更新 | 2h | ⭐ |
| **总计** | **21h** | - |

**建议分工**: 2 人 × 10-11 天，或 1 人 × 3-4 周

---

## 常见问题

**Q: 需要修改现有的节点代码吗?**
A: 不需要。现有节点无需修改，系统会自动推导输出类型。

**Q: 如果节点返回非预期类型会怎样?**
A: 系统会尽量推导为最接近的类型，defaulting to `json_viewer`。可在日志中查看警告。

**Q: 如何测试新功能不会破坏现有功能?**
A: 运行现有项目，检查每个节点的展示是否正常。API 响应格式向后兼容。

**Q: 前端包体积会增加吗?**
A: Plotly 和 ECharts 是可选的，可以按需加载。建议使用 dynamic import。
