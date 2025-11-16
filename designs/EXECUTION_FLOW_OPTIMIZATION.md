# 执行流程优化设计

**日期**: 2025-11-17
**目标**: 完整的 6 步执行流程，从形式校验到数据读取单元生成

---

## 当前状态分析

### 已实现 ✅
- Pre-check: 检查同名变量（`_check_same_named_variable_in_code`）
- Auto-append: 自动追加保存代码（`_auto_append_save_code`）
- Execution: 基本的 Kernel 执行
- Post-check: 基本的执行后验证
- Metadata sync: 部分同步（仅 status，需要完善）

### 缺陷 ❌
- 形式校验不完整：只检查变量名，未检查类型
- 类型检查有 Bug：`get_variable()` 返回字符串而非对象
- 元数据同步不完整：仅同步 execution_status，未同步其他字段
- 缺少动态依赖生成：execution 后不生成新的 depends_on
- 缺少数据读取单元：execution 成功后不生成读取代码

---

## 优化后的 6 步执行流程

### Step 1: 形式校验（Form Validation）

**检查内容**:
```
✓ 同名变量或函数是否存在
✓ 类型是否正确
  - data_source: 必须是 DataFrame
  - compute: 必须是 DataFrame
  - chart: 必须是 plotly.graph_objects.Figure 或 dict
  - tool: 必须是 callable（函数）
✓ 如果校验失败：直接报错，不执行
```

**实现位置**: `CodeValidator.validate_node_output(code, node_id, node_type)`

**关键逻辑**:
```python
def validate_node_form(code: str, node_id: str, node_type: str):
    """
    Form validation: check if code assigns correct type

    Returns:
        (is_valid, error_message)
    """
    if not CodeValidator.has_same_named_variable(code, node_id):
        return False, f"Code must assign variable '{node_id}'"

    # Type-specific validation
    if node_type in ['data_source', 'compute']:
        if not CodeValidator.is_dataframe_result(code, node_id):
            return False, f"Node '{node_id}' must return DataFrame, got {detected_type}"
    elif node_type == 'chart':
        if not CodeValidator.is_chart_result(code, node_id):
            return False, f"Node '{node_id}' must return Figure or dict"
    elif node_type == 'tool':
        if not CodeValidator.is_function_definition(code, node_id):
            return False, f"Tool node '{node_id}' must define function"

    return True, "Form validation passed"
```

---

### Step 2: 追加保存代码（Append Save Code）

**当前实现**: ✅ 已正确实现
**改进**: 添加错误处理，确保保存失败时能抛出异常

```python
def _auto_append_save_code(self, code: str, node_id: str, result_format: str):
    # ... 现有逻辑 ...
    # 改进：确保 try-except 会抛出异常，不会静默失败
    if result_format == "parquet":
        save_code = f"""
try:
    {node_id}.to_parquet(...)
except Exception as save_error:
    raise RuntimeError(f"Failed to save: {{save_error}}")
"""
```

---

### Step 3: 执行（Execution）

**当前实现**: ✅ 已实现
**改进**: 捕获 Kernel 输出，用于后续调试

---

### Step 4: 更新元数据（Update Metadata）

**需要更新的内容**:

```
a. project.json:
   - execution_status: 'validated'
   - error_message: null
   - result_path: 'parquets/node_id.parquet' 或 'functions/node_id.pkl'
   - execution_time: datetime
   - output_type: 'dataframe' | 'chart' | 'dict'
   - output_format: 'parquet' | 'json' | 'pkl' | 'figure'

b. project.ipynb - cell metadata:
   - metadata.execution_status: 'validated'
   - metadata.error_message: null
   - metadata.result_path: '...'
   - metadata.execution_time: '...'

c. project.ipynb - cell 开头注释:
   # @execution_status: validated
   # @error_message: null
   # @result_path: parquets/node_id.parquet

d. project.ipynb - markdown cell (可选):
   创建或更新单元前的说明文档
```

**实现方法**:

```python
def _sync_execution_metadata(self, node_id: str, execution_result):
    """
    After successful execution, sync all metadata:
    1. project.json
    2. cell metadata
    3. cell comment
    4. markdown documentation
    """
    # Update project.json
    node = self.pm.get_node(node_id)
    node['execution_status'] = 'validated'
    node['error_message'] = None
    node['result_path'] = execution_result['result_path']
    node['execution_time'] = execution_result['execution_time']
    node['output_type'] = self._infer_output_type(node_id, execution_result)
    self.pm._save_metadata()

    # Update notebook cell
    self.nm.update_execution_status(node_id, 'validated')
    self.nm.update_cell_metadata(node_id, {
        'result_path': execution_result['result_path'],
        'execution_time': execution_result['execution_time']
    })
    self.nm.sync_metadata_comments()
    self.nm.save()
```

---

### Step 5: 生成动态依赖（Generate Dynamic Dependencies）

**目标**: 通过 AST 分析执行后的代码，自动生成新的 depends_on

**实现方式**:

```python
def _update_dependencies(self, node_id: str, code: str):
    """
    After successful execution, analyze code and generate dependencies

    Process:
    1. Extract all variable references from code
    2. Map to node_ids (only node_ids that have result files)
    3. Update node['depends_on'] with new list
    4. Rebuild DAG
    5. Sync to project.json and notebook metadata
    """
    # Existing: self._extract_variable_names(code)
    referenced_vars = self._extract_variable_names(code)

    # New: Map vars to node_ids
    new_dependencies = []
    for var_name in referenced_vars:
        potential_node = self.pm.get_node(var_name)
        if potential_node and var_name != node_id:
            new_dependencies.append(var_name)

    # Update metadata
    node = self.pm.get_node(node_id)
    node['depends_on'] = new_dependencies
    self.pm._save_metadata()

    # Sync to notebook
    self.nm.update_cell_metadata(node_id, {'depends_on': new_dependencies})
    self.nm.sync_metadata_comments()
    self.nm.save()

    return new_dependencies
```

---

### Step 6: 生成数据读取单元（Generate Data Reading Cell）

**目标**: 为已验证的节点生成"读取结果数据"的 cell，下次执行时快速加载

**单元内容**:

```python
# ===== System-managed: Result loading cell =====
# @node_type: result_loader
# @node_id: load_<node_id>_result
# @depends_on: []
# ===== End of system-managed =====

import pandas as pd
import json

# Load previously computed result
node_id = '<node_id>'
result_path = '<relative_path_to_parquet>'

if result_path.endswith('.parquet'):
    <node_id> = pd.read_parquet(result_path)
elif result_path.endswith('.json'):
    with open(result_path, 'r') as f:
        <node_id> = json.load(f)
```

**实现方式**:

```python
def _generate_result_loader_cell(self, node_id: str, result_path: str, result_format: str):
    """
    After successful execution, generate a "data loader" cell

    Purpose:
    - Next time this node is executed, load result from file instead of recomputing
    - Speeds up subsequent executions
    - Makes results reproducible without recomputation
    """
    if result_format == 'parquet':
        loader_code = f"""
import pandas as pd
{node_id} = pd.read_parquet(r'{result_path}')
print(f"✓ Loaded {node_id} from cache")
"""
    elif result_format == 'json':
        loader_code = f"""
import json
with open(r'{result_path}', 'r') as f:
    {node_id} = json.load(f)
print(f"✓ Loaded {node_id} from cache")
"""

    # Add as result cell after the original code cell
    self.nm.append_code_cell(
        node_id=f'load_{node_id}_result',
        code=loader_code,
        node_type='result_loader',
        result_cell=True
    )
```

**调用时机**: Step 4 元数据同步之后，Step 5 依赖生成之前

---

## 完整的执行流程时序

```
execute_node(node_id)
    ↓
[Step 1] 形式校验 - validate_node_form()
    if 失败 → return error immediately
    ↓
[Step 2] 追加保存代码 - _auto_append_save_code()
    code = code + save_code
    ↓
[Step 3] 执行 - km.execute_code()
    if 失败 → update status to 'pending_validation', return error
    ↓
[Step 4] 更新元数据 - _sync_execution_metadata()
    a. project.json: status, result_path, execution_time
    b. cell metadata
    c. cell comments
    d. markdown documentation
    ↓
[Step 5] 生成依赖 - _update_dependencies()
    Analyze code → extract variables → map to nodes
    Update project.json and cell metadata with new depends_on
    ↓
[Step 6] 生成读取单元 - _generate_result_loader_cell()
    Create new cell to load result from file
    ↓
return success result with all metadata updated
```

---

## 错误处理策略

| 阶段 | 失败情况 | 处理方式 |
|-----|--------|--------|
| Step 1 | 形式校验失败 | 报错，status='validation_error'，不执行 |
| Step 2 | 追加保存代码失败 | 应不会发生，代码生成内部逻辑 |
| Step 3 | Kernel 执行失败 | 报错，status='pending_validation'，停止 |
| Step 4 | 元数据同步失败 | 继续（有 try-catch），但记录警告 |
| Step 5 | 依赖生成失败 | 继续（有 try-catch），使用旧的 depends_on |
| Step 6 | 读取单元生成失败 | 继续（有 try-catch），不影响核心执行 |

---

## 关键改进点

1. **形式校验强化**: 从"是否有变量"升级到"是否是正确类型"
2. **元数据同步完整化**: 从仅更新 status 升级到完整的 4 项内容
3. **动态依赖生成**: 执行后自动分析代码生成新的依赖关系
4. **缓存读取优化**: 生成读取单元，下次可以快速加载而不重新计算
5. **错误处理分层**: 不同阶段的错误用不同的状态码表示

---

## 实现优先级

```
高优先级 (核心功能):
  1. Step 1: 形式校验强化
  2. Step 3-4: 元数据同步完整化
  3. Step 5: 动态依赖生成

中优先级 (优化功能):
  4. Step 6: 读取单元生成
  5. 错误处理分层

低优先级 (扩展功能):
  6. 性能优化
  7. 可观测性增强
```

---

## 验证方式

执行后检查:
```
1. project.json: 所有字段已更新
2. project.ipynb:
   - cell metadata 完整
   - cell comments 完整
   - 生成了读取单元
3. parquets/: 结果文件存在且有效
4. depends_on: 正确反映代码依赖
```
