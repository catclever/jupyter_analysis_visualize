# 智能递归依赖执行设计方案

**日期**: 2025-11-17
**目标**: 优化节点执行流程，实现智能依赖加载和递归执行

---

## 📋 需求分析

### 当前问题

1. **依赖在执行时才分析** - 执行节点时才确定需要哪些依赖，效率低
2. **无法智能加载** - 不区分已保存的数据和需要执行的代码
3. **缺少递归执行** - 前置节点的前置节点不会自动执行
4. **状态管理不完善** - 节点的执行状态未能在前端清晰展示
5. **错误处理粗糙** - 任何环节失败都会中断整个流程

### 优化目标

- ✅ 执行前智能分析依赖关系，不执行则不修改 depends_on
- ✅ 检查依赖变量在 Kernel 中是否存在
- ✅ 已验证节点从文件加载数据，未执行节点递归执行代码
- ✅ 递归判断前置节点的依赖
- ✅ 原子化执行：所有前置节点和当前节点都执行成功才标记完成
- ✅ 每个节点完成后立即更新状态和依赖
- ✅ 任何节点失败立即停止，标记为待验证
- ✅ 前端明显区分节点状态：未执行(灰色/无) → 待验证(红色叹号) → 已验证(绿色勾)

---

## 🔄 新的执行流程

```
执行节点 node_id
│
├─ Step 1: 形式校验 (Form Validation)
│  ├─ 检查代码是否定义了正确的变量/函数
│  ├─ 静态推断返回类型
│  └─ 如果失败 → 返回 validation_error
│
├─ Step 2: 分析依赖 (Analyze Dependencies)
│  ├─ 通过 AST 提取代码中引用的变量名
│  ├─ 交集匹配 (variables ∩ node_ids)
│  ├─ 识别前置节点列表
│  ├─ ⚠️  此时 NOT 写入 node['depends_on'] 字段
│  └─ 返回临时依赖列表 (pending_deps)
│
├─ Step 3: 检查 Kernel 中的变量 (Check Kernel Variables)
│  ├─ 对于每个 pending_dep:
│  │  ├─ 检查 Kernel 中是否存在 var_name
│  │  ├─ 如果存在 → 跳过 (已加载)
│  │  └─ 如果不存在 → 加入待执行列表
│  └─ 返回需要执行的节点列表 (nodes_to_execute)
│
├─ Step 4: 递归执行前置节点 (Recursive Pre-execution)
│  ├─ 对于每个 node in nodes_to_execute:
│  │  ├─ 获取该节点状态:
│  │  │  ├─ 如果 status == 'validated' && result_path 存在
│  │  │  │  └─ 从文件加载数据到 Kernel
│  │  │  └─ 如果 status != 'validated'
│  │  │     └─ 递归调用 execute_node(node_id)
│  │  ├─ 如果任何节点执行失败 → 停止,返回失败
│  │  └─ 如果执行成功 → 继续下一个
│  └─ 所有前置节点完成后,继续 Step 5
│
├─ Step 5: 执行当前节点代码 (Execute Current Node)
│  ├─ 追加保存代码
│  ├─ 执行到 Kernel
│  ├─ 检查执行结果
│  └─ 如果失败 → 标记为 pending_validation,返回
│
├─ Step 6: 验证执行结果 (Verify Execution)
│  ├─ 检查期望的变量在 Kernel 中是否存在
│  └─ 如果不存在 → 标记为 pending_validation,返回
│
├─ Step 7: 更新当前节点状态 (Update Current Node)
│  ├─ 设置 execution_status = 'validated'
│  ├─ 清空 error_message
│  ├─ 设置 result_path
│  ├─ 计算 execution_time
│  └─ 同步到 project.json, notebook metadata, cell comments
│
├─ Step 8: 更新依赖关系 (Update Dependencies)
│  ├─ ⚠️  只在所有前置节点都完成后才执行
│  ├─ 根据实际执行的节点列表更新 depends_on
│  ├─ 同步回 project.json 和 notebook
│  └─ 返回成功
│
└─ Step 9: 生成结果单元 (Generate Result Cell)
   └─ 创建读取和显示结果的代码单元
```

---

## 📊 关键改进点

### 1. Step 2 - 依赖分析 (不写入数据)

```python
def _analyze_dependencies_pre_execution(self, node_id: str) -> List[str]:
    """
    分析节点需要的依赖,返回待执行列表
    注意: 此时不修改 node['depends_on']

    Returns: 分析出的依赖列表 (临时,未验证)
    """
    code = self._get_node_code(node_id)
    extracted_vars = CodeValidator._extract_variable_names(code)
    all_node_ids = {node['node_id'] for node in self.pm.list_nodes()}
    analyzed_deps = list(extracted_vars & all_node_ids)
    return analyzed_deps
```

### 2. Step 3 - Kernel 变量检查

```python
def _check_kernel_variables(self, analyzed_deps: List[str]) -> tuple:
    """
    检查分析出的依赖中哪些变量在 Kernel 中不存在

    Returns: (existing_vars, missing_vars)
    """
    existing_vars = []
    missing_vars = []

    for var_name in analyzed_deps:
        var_exists = self.km.variable_exists(self.pm.project_id, var_name)
        if var_exists:
            existing_vars.append(var_name)
        else:
            missing_vars.append(var_name)

    return existing_vars, missing_vars

# 新增方法到 KernelManager
def variable_exists(self, project_id: str, var_name: str) -> bool:
    """
    检查变量在 Kernel 中是否存在,不用 get_variable() 方法
    """
    code = f"""
import json
__exists = '{var_name}' in dir()
print(json.dumps(__exists))
"""
    output = self.execute_code(project_id, code, timeout=5)
    try:
        return json.loads(output.get('output', 'false'))
    except:
        return False
```

### 3. Step 4 - 递归执行

```python
def _execute_missing_dependencies_recursively(
    self,
    missing_var_names: List[str],
    execution_stack: List[str] = None
) -> bool:
    """
    递归执行缺失的依赖节点

    Args:
        missing_var_names: 需要的变量名称列表
        execution_stack: 执行栈,用于检测循环依赖

    Returns:
        True 如果所有依赖执行成功,False 如果任何失败
    """
    if execution_stack is None:
        execution_stack = []

    for var_name in missing_var_names:
        # var_name 对应的节点 id
        node = self.pm.get_node(var_name)
        if not node:
            return False  # 找不到对应节点

        node_id = var_name

        # 检查循环依赖
        if node_id in execution_stack:
            return False  # 检测到循环

        # 获取该节点的执行状态
        status = node.get('execution_status', 'not_executed')
        result_path = node.get('result_path')

        if status == 'validated' and result_path:
            # 从文件加载数据
            success = self._load_variable_from_file(
                node_id,
                result_path,
                node.get('result_format', 'parquet')
            )
            if not success:
                return False
        else:
            # 需要执行该节点
            result = self.execute_node(node_id, execution_stack + [node_id])
            if result['status'] != 'success':
                return False

    return True

def _load_variable_from_file(
    self,
    var_name: str,
    result_path: str,
    result_format: str
) -> bool:
    """
    从文件加载变量到 Kernel
    """
    full_path = self.pm.project_path / result_path
    if not full_path.exists():
        return False

    if result_format == 'parquet':
        load_code = f"""
import pandas as pd
{var_name} = pd.read_parquet(r'{full_path}')
"""
    elif result_format == 'json':
        load_code = f"""
import json
with open(r'{full_path}', 'r', encoding='utf-8') as f:
    {var_name} = json.load(f)
"""
    elif result_format == 'pkl':
        load_code = f"""
import pickle
with open(r'{full_path}', 'rb') as f:
    {var_name} = pickle.load(f)
"""
    else:
        return False

    try:
        output = self.km.execute_code(self.pm.project_id, load_code, timeout=30)
        return output.get('status') == 'success'
    except:
        return False
```

### 4. Step 7-8 - 原子化状态更新

```python
def _finalize_execution(
    self,
    node_id: str,
    analyzed_deps: List[str],
    execution_time: float
) -> None:
    """
    执行成功后,更新节点状态和依赖关系
    """
    node = self.pm.get_node(node_id)
    result_format = node.get('result_format', 'parquet')

    # Step 7: 更新执行状态
    node['execution_status'] = 'validated'
    node['error_message'] = None
    node['execution_time'] = execution_time
    node['last_execution_time'] = datetime.now().isoformat()

    # 计算结果路径
    if result_format == 'parquet':
        result_path = f"parquets/{node_id}.parquet"
    elif result_format == 'json':
        result_path = f"parquets/{node_id}.json"
    elif result_format == 'pkl':
        result_path = f"functions/{node_id}.pkl"
    else:
        result_path = f"results/{node_id}"

    node['result_path'] = result_path

    # Step 8: 更新依赖关系 (只在全部成功后)
    node['depends_on'] = sorted(list(set(analyzed_deps)))

    # 保存到 project.json 和 notebook
    self.pm._save_metadata()
    self.nm.update_execution_status(node_id, 'validated')
    self.nm.sync_metadata_comments()
    self.nm.save()
```

---

## 🎯 前端状态指示器设计

### 节点状态定义

| 状态 | 说明 | 图标 | 颜色 | 交互 |
|------|------|------|------|------|
| `not_executed` | 未执行 | 无/灰圈 | 灰色 (#999) | 可点击执行 |
| `pending_validation` | 待验证 | ❌ 叹号 | 红色 (#ef4444) | 可点击重新执行 |
| `validated` | 已验证 | ✓ 勾 | 绿色 (#22c55e) | 禁用执行 |

### 前端实现

```tsx
// FlowDiagram.tsx 中的节点样式

const getNodeStatusIcon = (status: string) => {
  switch (status) {
    case 'validated':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'pending_validation':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    case 'not_executed':
    default:
      return <Circle className="w-4 h-4 text-gray-400" />;
  }
};

const getNodeBorderColor = (status: string) => {
  switch (status) {
    case 'validated':
      return '2px solid #22c55e';  // 绿色
    case 'pending_validation':
      return '2px solid #ef4444';  // 红色
    case 'not_executed':
    default:
      return '2px solid #999';     // 灰色
  }
};

// 节点组件
const CustomNode = ({ data, selected }: NodeProps<FlowNodeData>) => {
  const status = data.executionStatus || 'not_executed';

  return (
    <div
      style={{
        padding: '10px',
        borderRadius: '8px',
        border: getNodeBorderColor(status),
        backgroundColor: selected ? '#f0f0f0' : 'white',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        cursor: status === 'validated' ? 'default' : 'pointer'
      }}
    >
      {getNodeStatusIcon(status)}
      <span>{data.label}</span>
    </div>
  );
};
```

### API 返回数据更新

```json
{
  "node_id": "compute_1",
  "name": "Path 1: Daily Sales Trend",
  "type": "compute",
  "execution_status": "validated",  // 新增
  "error_message": null,             // 新增
  "result_path": "parquets/compute_1.parquet",
  "execution_time": 2.34,           // 新增
  "last_execution_time": "2025-11-17T10:30:45.123456"  // 新增
}
```

---

## 🚀 实现步骤

### Phase 1: 后端核心逻辑 (3-4天)

- [ ] 新增 `variable_exists()` 方法到 KernelManager
- [ ] 新增 `_analyze_dependencies_pre_execution()` 方法
- [ ] 新增 `_check_kernel_variables()` 方法
- [ ] 新增 `_execute_missing_dependencies_recursively()` 方法
- [ ] 新增 `_load_variable_from_file()` 方法
- [ ] 修改 `execute_node()` 集成新流程
- [ ] 修改 `_finalize_execution()` 实现原子化更新

### Phase 2: 错误处理和验证 (2天)

- [ ] 添加循环依赖检测
- [ ] 添加超时处理
- [ ] 添加部分失败恢复机制
- [ ] 单元测试

### Phase 3: 前端集成 (2-3天)

- [ ] 更新节点状态图标和颜色
- [ ] 更新 API 返回数据结构
- [ ] 更新前端显示逻辑
- [ ] 集成测试

---

## 📝 关键设计决策

### 1. 为什么分离 "分析依赖" 和 "写入依赖"?

**理由**:
- 如果只是提交不执行,不应该修改 depends_on
- 避免虚假的依赖关系污染 project.json
- 只在真正执行成功后才锁定依赖

**例子**:
```python
# 用户提交代码 load_A = load_raw_data() + compute_result
# 但用户只点了 "预览" 不真正执行

# 旧流程: depends_on 已被修改为 ['compute_result']
# 新流程: depends_on 保持不变,等到真正执行后再更新
```

### 2. 为什么先检查 Kernel 中的变量?

**理由**:
- 避免重复执行已加载的数据
- 加快执行速度
- 支持交互式工作流 (先执行 A,再执行 B,B 可以使用 A 的结果)

**例子**:
```
用户已执行了 load_orders 和 load_customers
现在想执行 merge_data (depends_on: load_orders, load_customers)

Kernel 中已有这两个变量
→ 直接使用,无需重新加载或执行
```

### 3. 为什么需要递归?

**理由**:
- 用户只需点一个节点
- 系统自动计算并执行所有必要的前置节点
- 类似 Make/Gradle 的增量构建

**例子**:
```
DAG:
  raw_data → clean_data → analyze_1
                      ↘ analyze_2

用户执行 analyze_2
→ 系统递归执行: raw_data → clean_data → analyze_2
→ 只有这 3 个节点被执行,analyze_1 不受影响
```

### 4. 为什么状态是原子操作?

**理由**:
- 防止部分执行成功导致的不一致状态
- 所有前置节点+当前节点都成功 = 整体成功
- 任何一个失败 = 整体失败

**例子**:
```
执行 analyze 时:
  load_data: ✓ (执行成功)
  analyze:   ✗ (执行失败)

结果:
  load_data: validated (因为它独立成功)
  analyze:   pending_validation (失败)

不会出现: analyze = validated (虽然依赖都满足)
```

---

## 🔍 错误处理

### 失败场景 1: 前置节点执行失败

```python
执行流: load_A → load_B → compute

load_A: ✓ (success)
load_B: ✗ (failure → pending_validation)

结果:
  - load_A: validated
  - load_B: pending_validation
  - compute: 不执行 (因为 load_B 失败)
  - 返回错误: "Dependency load_B failed with error: ..."
```

### 失败场景 2: 循环依赖

```python
执行栈检测:
  A depends_on B
  B depends_on A

检测: 执行 A → 需要 B → 需要 A (在栈中!)
返回错误: "Circular dependency detected: A → B → A"
```

### 失败场景 3: 超时

```python
执行 load_big_data (超时 30s)

返回错误: "Node execution timeout (30s)"
状态: pending_validation
用户可重新执行
```

---

## ✅ 验收标准

### 后端

- [ ] 所有 8 步都在 execute_node() 中正确实现
- [ ] 递归执行通过单元测试
- [ ] 循环依赖检测通过测试
- [ ] 错误恢复机制验证通过
- [ ] 性能: 依赖分析 <10ms,文件加载 <1s

### 前端

- [ ] 节点显示正确的状态图标
- [ ] 状态颜色符合设计 (绿/红/灰)
- [ ] 点击节点时正确显示编辑或执行选项
- [ ] 执行过程中实时更新状态显示
- [ ] 错误信息清晰显示在数据面板

### 集成

- [ ] 手动测试: 执行单个节点,验证依赖递归执行
- [ ] 手动测试: 执行已验证节点,验证从文件加载
- [ ] 手动测试: 前置节点失败,验证停止执行
- [ ] 手动测试: 循环依赖,验证错误检测
- [ ] 端到端: 完整的项目执行流程

---

## 时间估算

| 阶段 | 任务 | 时间 |
|------|------|------|
| Phase 1 | 后端核心逻辑 | 3-4 天 |
| Phase 2 | 错误处理和验证 | 2 天 |
| Phase 3 | 前端集成 | 2-3 天 |
| 测试 | 集成测试 | 1-2 天 |
| **总计** | | **8-11 天** |

---

**下一步**: 等待确认后,开始 Phase 1 实现。

