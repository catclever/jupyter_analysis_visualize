"""
Simple test to verify tool node auto-append fix
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from code_executor import CodeExecutor


class MockProjectManager:
    def __init__(self):
        self.project_path = Path("/tmp/test")
        self.parquets_path = self.project_path / "parquets"


def test_auto_append_skips_tool_nodes():
    """
    Test: _auto_append_save_code should skip tool nodes

    Expected: Tool nodes return original code unchanged
    """
    print("\n" + "="*70)
    print("TEST: _auto_append_save_code skips tool nodes")
    print("="*70)

    ce = CodeExecutor("test_project", "/tmp/dummy")
    ce.pm = MockProjectManager()

    # Test code
    original_code = """def my_function(x):
    return x * 2"""

    # Test 1: Tool node should NOT get auto-append code
    result_tool = ce._auto_append_save_code(
        original_code,
        "tool_func",
        "pkl",
        node_type="tool"
    )

    print("\n[TEST 1] Tool node (node_type='tool')")
    print(f"  Original length: {len(original_code)}")
    print(f"  Result length: {len(result_tool)}")

    if result_tool == original_code:
        print("  ✓ PASS: Code unchanged (no auto-append)")
    else:
        print("  ✗ FAIL: Code was modified")
        print(f"  Expected: {original_code}")
        print(f"  Got: {result_tool}")
        return False

    # Test 2: Data node SHOULD get auto-append code
    result_data = ce._auto_append_save_code(
        original_code,
        "data_var",
        "parquet",
        node_type="data_source"
    )

    print("\n[TEST 2] Data node (node_type='data_source')")
    print(f"  Original length: {len(original_code)}")
    print(f"  Result length: {len(result_data)}")

    if result_data != original_code and "Auto-appended" in result_data:
        print("  ✓ PASS: Auto-append code added")
    else:
        print("  ✗ FAIL: Auto-append code not added")
        return False

    # Test 3: Compute node SHOULD get auto-append code
    result_compute = ce._auto_append_save_code(
        original_code,
        "compute_var",
        "parquet",
        node_type="compute"
    )

    print("\n[TEST 3] Compute node (node_type='compute')")
    print(f"  Original length: {len(original_code)}")
    print(f"  Result length: {len(result_compute)}")

    if result_compute != original_code and "Auto-appended" in result_compute:
        print("  ✓ PASS: Auto-append code added")
    else:
        print("  ✗ FAIL: Auto-append code not added")
        return False

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    return True


if __name__ == "__main__":
    try:
        result = test_auto_append_skips_tool_nodes()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
