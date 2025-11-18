# Code Save Functionality Tests

这个目录包含用于诊断和测试代码保存功能的脚本。

## 📋 测试脚本

### 1. `test_code_save_flow.py`

**目的**: 测试代码保存的完整流程

**运行方式**:
```bash
cd backend
uv run python test/test_code_save_flow.py
```

**测试内容**:
- ✅ 代码检索（GET）
- ✅ 代码保存（PUT）- 有效代码
- ✅ 代码保存（PUT）- 空代码
- ✅ 文件验证（检查 .ipynb 文件中是否正确保存）

**预期结果**:
```
=== Test 1: Code Retrieval ===
✓ Code retrieved successfully
  Code length: 645 chars
  Contains metadata: True

✅ Test PASSED: Code retrieved correctly

=== Test 2: Code Save (Valid Code) ===
✓ Code saved successfully
✓ Found code cell
  Contains 'EDITED': True

✅ Test PASSED: Code saved correctly

=== Test 3: Code Save (Empty Code) ===
✓ Response status: OK
  Empty code handled correctly (returned metadata only)

✅ Test PASSED: Empty code handled correctly
```

---

### 2. `test_code_save_debug.py`

**目的**: 诊断代码保存中的问题，提供详细的调试信息

**运行方式**:
```bash
cd backend
uv run python test/test_code_save_debug.py
```

**测试内容**:
- ✅ 检查保存前的笔记本状态
- ✅ 发送代码到 API
- ✅ 检查保存后的笔记本状态
- ✅ 验证代码是否真的被保存
- ✅ 记录 API 请求日志

**输出示例**:
```
================================================================================
  INITIAL STATE
================================================================================

[2025-11-18T...] Checking notebook state (initial)...
✓ Found code cell at index 0:
  Source length: 645 chars
  Has @node_type: True
  First 100 chars: '# ===== System-managed metadata...'

================================================================================
  SAVE CODE VIA API
================================================================================

✓ Save successful:
  Response code length: 750 chars
  Response dependencies: []
  Response execution_status: not_executed

================================================================================
  VERIFY IN NOTEBOOK
================================================================================

✓ Found code cell at index 0:
  Source length: 750 chars

✅ Code was saved correctly!
   Timestamp marker found in notebook
```

---

## 🔍 诊断流程

### 如果代码保存失败，按照以下步骤诊断：

#### 步骤 1：运行 API 级别的测试
```bash
cd backend
uv run python test/test_code_save_flow.py
```

**查看输出**:
- 如果 Test 1 (Code Retrieval) 失败 → 后端 API 有问题
- 如果 Test 2 (Code Save - Valid) 失败 → 代码没有被正确保存
- 如果 Test 3 (Code Save - Empty) 失败 → 错误处理有问题

#### 步骤 2：运行详细诊断脚本
```bash
cd backend
uv run python test/test_code_save_debug.py
```

**查看输出**:
- 检查 "VERIFY IN NOTEBOOK" 部分
- 如果显示 ❌ "Code was NOT saved correctly"，说明 API 接收到了代码，但没有保存到文件

#### 步骤 3：检查后端日志
在运行测试时，查看后端的日志输出：

```
DEBUG: update_node_code called with project_id=dict_result_test, node_id=create_summaries
DEBUG: Got project manager
DEBUG: code_content length=404, content preview: # Modified at 20251118_152030...
```

关键点：
- `code_content length=404` → 说明后端收到了代码
- 如果显示 `code_content length=0` → **问题在前端，没有发送代码**

#### 步骤 4：检查前端日志
在浏览器开发工具（F12）的 Console 标签中查看：

应该看到类似的输出：
```
[DEBUG:handleCodeChange] Input detected {
  newContentLength: 404,
  apiCodeLength: 200,
  isDifferent: true,
  preview: "# Modified at...",
  timestamp: "2025-11-18T..."
}
[DEBUG:handleCodeChange] Marked as changed

[DEBUG:handleCodeSave] Save triggered {
  displayedNodeId: "create_summaries",
  hasChanges: true,
  editingCodeLength: 404,
  editingCodePreview: "# Modified at...",
  timestamp: "2025-11-18T..."
}
[DEBUG:handleCodeSave] Sending to API...
```

---

## 🔧 常见问题诊断

### 问题 1：API 测试通过，但前端保存失败

**可能原因**:
- 前端的 `handleCodeChange` 没有被触发
- 编辑框的输入事件没有被正确处理

**诊断方法**:
1. 在前端进行手动测试
2. 在编辑框中修改代码
3. 打开浏览器 Console
4. 查看是否有 `[DEBUG:handleCodeChange]` 输出

**解决方案**:
- 更新 react-simple-code-editor 库
- 或切换到另一个编辑器库

### 问题 2：API 收到了代码，但没有保存到文件

**可能原因**:
- 笔记本文件权限问题
- 文件被锁定或无法写入
- 后端代码有 bug

**诊断方法**:
```bash
# 检查文件权限
ls -la projects/dict_result_test/project.ipynb

# 检查文件是否可写
touch projects/dict_result_test/project.ipynb
```

### 问题 3：前端根本没有发送代码

**可能原因**:
- `editingCode` 状态为空
- `hasChanges` 标志为 false
- 保存按钮事件没有绑定

**诊断方法**:
1. 查看前端 Console 日志
2. 如果没有 `[DEBUG:handleCodeSave]` 输出，说明保存函数没有被调用
3. 检查保存按钮是否有正确的 onClick 事件

---

## 📊 测试结果解释

### 成功的保存：
```
✅ Code was saved correctly!
   Timestamp marker found in notebook
   Original length: 645 → New length: 750
```

### 失败的保存：
```
❌ Code was NOT saved correctly!
   Timestamp marker NOT found in notebook
   Expected to find: 'Modified at 20251118_152030'
```

---

## 🚀 快速测试流程

### 快速检查：是否能通过 API 保存
```bash
cd backend
uv run python test/test_code_save_flow.py
```

### 完整诊断：找出具体问题在哪里
```bash
cd backend
uv run python test/test_code_save_debug.py
```

---

## 📝 日志输出说明

### 后端日志
看 `print()` 输出中的：
```
DEBUG: code_content length=XXX, content preview: YYY
```

- `length=0` → 前端没有发送代码
- `length>0` → 前端发送了代码，后端需要处理

### 前端日志
看浏览器 Console 中的：
```
[DEBUG:handleCodeChange] Input detected
[DEBUG:handleCodeSave] Save triggered
```

- 如果没有这些日志 → 事件没有被触发
- 如果有但长度为 0 → 编辑框的内容没有被正确捕获

---

## ✅ 验证修复

修复完成后，运行完整测试：

```bash
cd backend
uv run python test/test_code_save_flow.py
```

所有测试都应该通过 ✅

---

**最后更新**: 2025-11-18
**相关文档**:
- `reports/CODE_SAVE_BUG_FIX.md`
- `reports/CODE_SAVE_DIAGNOSIS_GUIDE.md`
