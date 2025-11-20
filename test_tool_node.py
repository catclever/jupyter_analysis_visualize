
import sys
import ast
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from projects.project_builder import _infer_node_id, _infer_node_type

def test_tool_node():
    cases = {
        "Pure Function": """
def my_tool(x):
    return x + 1
""",
        "Pure Class": """
class MyProcessor:
    pass
""",
        "Function with Assignment (Should be Assign)": """
def helper(): return 1
x = helper()
""",
        "Loop then Function (Should be Function)": """
for i in range(10):
    pass
def final_tool():
    pass
"""
    }

    print(f"{'Case Name':<40} | {'Inferred ID':<15} | {'Inferred Type':<15}")
    print("-" * 75)
    
    for name, code in cases.items():
        node_id = _infer_node_id(code)
        node_type = _infer_node_type(code)
        print(f"{name:<40} | {str(node_id):<15} | {str(node_type):<15}")

if __name__ == "__main__":
    test_tool_node()
