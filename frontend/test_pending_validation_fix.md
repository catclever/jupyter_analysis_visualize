# Test Plan: Fix Code Reload on pending_validation

## 问题描述
当节点执行失败（status = 'pending_validation'）时，前端会触发 `nodeRefreshKey` 增加，导致 DataTable 重新加载代码，用户的编辑会被覆盖。

## 修复内容
移除 `pending_validation` 和其他错误情况下的 `nodeRefreshKey` 增加，只保留流程图刷新。

## 测试场景

### 场景1：基本修复验证
**步骤：**
1. 打开一个已执行过的节点（execution_status = 'validated'）
2. 编辑代码，修改逻辑使其出现错误
3. 点击执行按钮
4. 等待执行失败，状态变为 'pending_validation'

**预期结果：**
- ✅ 错误消息显示在错误面板
- ✅ 编辑器中的代码保留用户修改（不被覆盖）
- ✅ 编辑器保持在编辑模式（isEditingCode = true）
- ✅ 流程图中节点显示红色边框（pending_validation 状态）
- ✅ 可以立即修改代码并重试

**检验方法：**
```javascript
// 打开浏览器开发者工具，在执行失败后检查：
console.log('editingCode:', editingCode);
console.log('isEditingCode:', isEditingCode);
console.log('nodeExecutionStatus:', nodeExecutionStatus);
console.log('nodeErrors[displayedNodeId]:', nodeErrors[displayedNodeId]);
```

### 场景2：成功执行仍然正确工作
**步骤：**
1. 打开一个未执行的节点
2. 编写代码
3. 执行代码成功

**预期结果：**
- ✅ 代码被正确保存
- ✅ 节点状态变为 'validated'（绿色边框）
- ✅ DataTable 刷新显示结果
- ✅ 自动切换到结果视图（如果有结果）

### 场景3：多次重试
**步骤：**
1. 执行失败（pending_validation）
2. 修改代码
3. 再次执行
4. 如果继续失败，重复修改和执行

**预期结果：**
- ✅ 每次失败后，用户的新代码都被保留
- ✅ 可以进行多次重试而不丢失编辑
- ✅ 最终成功后，节点状态正确更新为 'validated'

### 场景4：验证流程图状态同步
**步骤：**
1. 执行失败，节点进入 'pending_validation'
2. 观察流程图

**预期结果：**
- ✅ 节点显示红色边框（pending_validation）
- ✅ 可以看到错误消息提示（tooltip）
- ✅ 流程图和数据表状态一致

### 场景5：验证其他错误类型
**步骤：**
1. 造成其他类型的错误（如网络错误、超时等）
2. 检查代码是否被保留

**预期结果：**
- ✅ 代码被保留
- ✅ 用户可以继续编辑

## 代码变更验证

### 变更1：pending_validation 情况
```typescript
// 修改前：
} else if (result.status === 'pending_validation') {
  setNodeExecutionStatus('pending_validation');
  setNodeRefreshKey(prev => prev + 1);  // ❌ 导致代码重新加载
}

// 修改后：
} else if (result.status === 'pending_validation') {
  setNodeExecutionStatus('pending_validation');
  // ✅ 移除 setNodeRefreshKey，代码保留
}
```

### 变更2：其他错误情况
```typescript
// 修改前：
} else {
  onProjectUpdate?.();
  setNodeRefreshKey(prev => prev + 1);  // ❌ 导致代码重新加载
}

// 修改后：
} else {
  onProjectUpdate?.();
  // ✅ 只刷新流程图，不刷新代码
}
```

## 预期行为对比

| 执行结果 | 流程图刷新 | DataTable 刷新 | 代码保留 | 自动视图切换 |
|---------|----------|--------------|---------|-----------|
| **success** | ✅ 是 | ✅ 是 | 否（重新加载） | ✅ 是（到结果） |
| **pending_validation** | ✅ 是 | ❌ 否 | ✅ 是 | ❌ 否（保持编辑） |
| **其他错误** | ✅ 是 | ❌ 否 | ✅ 是 | ❌ 否（保持编辑） |

## 验证命令

### 查看提交信息
```bash
git log -1 --format=fuller
```

### 验证修改内容
```bash
git show HEAD
```

### 运行开发服务器进行手动测试
```bash
cd frontend
npm run dev
```

## 边界情况

### 边界1：快速重试
- **描述：** 用户快速连续执行多次
- **预期：** 每次都正确处理，代码保留

### 边界2：切换节点
- **描述：** 执行失败后切换到其他节点
- **预期：** 新节点数据正确加载，失败节点的代码在回来时仍然保留

### 边界3：页面刷新
- **描述：** 执行失败后刷新页面
- **预期：** 重新加载项目数据，节点状态为 'pending_validation'，代码为后端保存的版本

## 监控指标

成功修复的表现：
- ✅ pending_validation 时不调用 setNodeRefreshKey
- ✅ 错误状态下流程图正确更新
- ✅ 用户编辑的代码在失败时被保留
- ✅ 可以多次重试而不丢失编辑
