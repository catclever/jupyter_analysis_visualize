"""
模拟用户在编辑框中输入代码，然后保存。
检查前端是否正确跟踪了输入内容。
"""
import json

# 模拟编辑框的行为
class CodeEditorState:
    def __init__(self):
        self.editingCode = ""
        self.apiCode = ""
        self.isEditingCode = False
        self.changes_log = []
    
    def load_code(self, code):
        """模拟加载代码"""
        self.apiCode = code
        self.editingCode = code  # 现在会初始化
        self.changes_log.append(f"load_code: editingCode='{code[:50]}...'")
    
    def handle_code_change(self, new_content):
        """模拟 handleCodeChange 回调"""
        self.editingCode = new_content
        self.changes_log.append(f"handleCodeChange: editingCode='{new_content[:50] if new_content else 'EMPTY'}...'")
    
    def handle_code_save(self):
        """模拟 handleCodeSave"""
        self.changes_log.append(f"handleCodeSave: sending editingCode='{self.editingCode[:50] if self.editingCode else 'EMPTY'}...'")
        return self.editingCode

# 测试场景 1：正常流程（应该工作）
print("\n=== 测试 1：正常输入流程 ===\n")
state = CodeEditorState()
state.load_code("import pandas as pd\n# Original code")
state.isEditingCode = True
state.handle_code_change("import pandas as pd\n# Modified code by user")
saved_code = state.handle_code_save()
print("\n日志：")
for log in state.changes_log:
    print(f"  {log}")
print(f"\n保存的代码: {repr(saved_code[:50])}")
print(f"✓ 工作正常" if saved_code else "✗ 问题：保存了空代码")

# 测试场景 2：handleCodeChange 没有被触发
print("\n\n=== 测试 2：handleCodeChange 未被触发 ===\n")
state = CodeEditorState()
state.load_code("import pandas as pd\n# Original code")
state.isEditingCode = True
# 用户输入了内容，但 handleCodeChange 没有被触发（BUG!）
# state.handle_code_change("...")  # 不调用这个
saved_code = state.handle_code_save()
print("\n日志：")
for log in state.changes_log:
    print(f"  {log}")
print(f"\n保存的代码: {repr(saved_code[:50])}")
print(f"✗ 问题：保存了空代码" if not saved_code else "✓ 工作正常")

# 测试场景 3：编辑框的 value 没有正确绑定到 editingCode
print("\n\n=== 测试 3：编辑框 value 绑定问题 ===\n")
print("可能的情况：")
print("  <CodeEditor value={editingCode} onChange={handleCodeChange} />")
print("")
print("  editingCode = ''")
print("  apiCode = 'original code'")
print("")
print("编辑框显示什么？")
print("  - 如果绑定正确: 显示 editingCode（空字符串）")
print("  - 如果有渲染 bug: 可能显示 apiCode（用户看到代码）")
print("")
print("用户输入后会保存什么？")
print("  - 如果 onChange 正确触发: editingCode 被更新")
print("  - 如果 onChange 没有触发: editingCode 保持为空")
