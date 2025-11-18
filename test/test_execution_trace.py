"""
Test to trace exact code being executed and find where def is stripped
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager
from project_manager import ProjectManager
from kernel_manager import KernelManager


class TestDefStrippingDuringExecution:
    """Test if def is stripped during execution"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        (self.project_path / "parquets").mkdir()
        (self.project_path / "functions").mkdir()
        (self.project_path / "visualizations").mkdir()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tool_code_through_full_flow(self):
        """
        Test: Track tool node code through entire flow:
        1. Create notebook with tool code
        2. Load code from notebook
        3. Execute in kernel
        4. Check if def is still there
        """
        print("\n" + "="*70)
        print("EXECUTION TRACE TEST: Tool Node Code Through Full Flow")
        print("="*70)

        # STEP 1: Create notebook with tool code
        print("\n[STEP 1] Create notebook with tool node code...")

        notebook_path = self.project_path / "project.ipynb"
        nm = NotebookManager(str(notebook_path))

        original_code = """def feature_engineering(df, operation='polynomial_features'):
    import pandas as pd

    if operation == 'polynomial_features':
        df_copy = df.copy()
        df_copy['age_squared'] = df_copy['age'] ** 2
        return df_copy
    elif operation == 'create_bins':
        df_copy = df.copy()
        df_copy['age_group'] = pd.cut(df_copy['age'], bins=[0, 30, 50, 100])
        return df_copy
    else:
        raise ValueError(f"Unknown operation: {operation}")"""

        nm.append_code_cell(
            code=original_code,
            node_type="tool",
            node_id="tool_feature_eng"
        )
        nm.save()

        print(f"  Original code length: {len(original_code)}")
        print(f"  Original code starts with: {original_code[:50]}")

        # STEP 2: Load code from notebook (simulating what execute_node does)
        print("\n[STEP 2] Load code from notebook...")

        cells = nm.get_cells()
        assert len(cells) == 1, "Should have 1 cell"

        cell = cells[0]
        source = cell.get('source', '')
        if isinstance(source, list):
            loaded_code = ''.join(source)
        else:
            loaded_code = source

        print(f"  Loaded code length: {len(loaded_code)}")
        print(f"  Loaded code starts with: {loaded_code[:50]}")

        # Extract the actual code (without metadata)
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, loaded_code, re.DOTALL)
        just_code = match.group(1) if match else loaded_code

        print(f"  Code after metadata removed length: {len(just_code)}")
        print(f"  Code after metadata removed starts with: {just_code[:50]}")

        # STEP 3: Prepare code for execution (simulate what _auto_append_save_code does)
        print("\n[STEP 3] Prepare code for execution (add save code)...")

        functions_dir = str(self.project_path / "functions")
        save_code = f"""
# Auto-appended: Save result to pickle
import pickle
from pathlib import Path
functions_dir = Path(r'{functions_dir}')
functions_dir.mkdir(parents=True, exist_ok=True)
save_path = functions_dir / 'tool_feature_eng.pkl'
with open(str(save_path), 'wb') as f:
    pickle.dump(tool_feature_eng, f)
print(f"✓ Saved pickle to {{save_path}}")"""

        code_to_execute = just_code + save_code

        print(f"  Total code to execute length: {len(code_to_execute)}")
        print(f"  Code to execute starts with: {code_to_execute[:50]}")
        print(f"  Code to execute contains 'def feature_engineering': {'def feature_engineering' in code_to_execute}")

        # STEP 4: Try to compile the code (this would catch syntax errors)
        print("\n[STEP 4] Validate code syntax...")

        try:
            compile(code_to_execute, filename='<tool_node>', mode='exec')
            print("  ✓ Code compiles successfully")
        except SyntaxError as e:
            print(f"  ✗ Syntax error in code: {e}")
            print(f"  Error location: line {e.lineno}")
            raise

        # STEP 5: Try executing in kernel (if available)
        print("\n[STEP 5] Execute in Jupyter kernel...")

        try:
            km = KernelManager()
            kernel = km.get_or_create_kernel("test_project", str(self.project_path))

            # Execute the code
            result = km.execute_code("test_project", code_to_execute, timeout=10)

            print(f"  Execution status: {result.get('status')}")
            if result.get('status') == 'error':
                print(f"  Error: {result.get('error')}")
            else:
                print(f"  Output: {result.get('output')[:100] if result.get('output') else 'None'}")

            # Check if function definition exists
            try:
                func_value = km.get_variable("test_project", "feature_engineering")
                print(f"  ✓ Function 'feature_engineering' exists in kernel")
                print(f"    Type: {type(func_value)}")
                print(f"    Callable: {callable(func_value)}")
            except Exception as e:
                print(f"  ✗ Cannot access 'feature_engineering' in kernel: {e}")

            # Check if tool_feature_eng exists (from auto-append code)
            try:
                var_value = km.get_variable("test_project", "tool_feature_eng")
                print(f"  ✓ Variable 'tool_feature_eng' exists in kernel")
                print(f"    Type: {type(var_value)}")
                print(f"    Value: {var_value}")
            except Exception as e:
                print(f"  ✗ Cannot access 'tool_feature_eng' in kernel: {e}")

            # Clean up kernel
            kernel.cleanup()

        except Exception as e:
            print(f"  Note: Kernel execution skipped - {e}")

        # STEP 6: Verify all steps preserved the code
        print("\n[STEP 6] Verification...")

        checks = {
            "original_code contains 'def'": 'def feature_engineering' in original_code,
            "loaded_code contains 'def'": 'def feature_engineering' in loaded_code,
            "just_code contains 'def'": 'def feature_engineering' in just_code,
            "code_to_execute contains 'def'": 'def feature_engineering' in code_to_execute,
            "original_code contains 'import pandas'": 'import pandas as pd' in original_code,
            "just_code contains 'import pandas'": 'import pandas as pd' in just_code,
        }

        all_passed = True
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")
            if not result:
                all_passed = False

        if all_passed:
            print("\n✅ All checks passed - code is preserved through execution flow")
            return True
        else:
            print("\n❌ Some checks failed - code is being stripped somewhere")
            return False


class TestCodeExtractionLogic:
    """Test the specific code extraction logic"""

    def test_metadata_extraction_edge_cases(self):
        """
        Test edge cases in metadata extraction that might strip code
        """
        print("\n" + "="*70)
        print("CODE EXTRACTION EDGE CASES TEST")
        print("="*70)

        test_cases = [
            {
                "name": "Tool with def and internal import",
                "code": """# ===== System-managed metadata =====
# @node_type: tool
# @node_id: tool_1
# ===== End of system-managed metadata =====

def my_tool(df):
    import pandas as pd
    return df.copy()""",
                "should_contain": ["def my_tool", "import pandas as pd"]
            },
            {
                "name": "Tool with blank line after metadata",
                "code": """# ===== System-managed metadata =====
# @node_type: tool
# @node_id: tool_2
# ===== End of system-managed metadata =====

def my_tool(df):
    return df""",
                "should_contain": ["def my_tool", "return df"]
            },
            {
                "name": "Tool without blank line",
                "code": """# ===== System-managed metadata =====
# @node_type: tool
# @node_id: tool_3
# ===== End of system-managed metadata =====
def my_tool(df):
    return df""",
                "should_contain": ["def my_tool", "return df"]
            },
        ]

        results = []

        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            code = test_case['code']

            # Extract using the same logic as the code
            import re
            pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
            match = re.search(pattern, code, re.DOTALL)
            extracted = match.group(1) if match else ""

            print(f"    Extracted length: {len(extracted)}")
            print(f"    Extracted preview: {extracted[:80]}...")

            # Check if required content is present
            all_present = True
            for should_have in test_case['should_contain']:
                is_present = should_have in extracted
                status = "✓" if is_present else "✗"
                print(f"    {status} Contains '{should_have}': {is_present}")
                if not is_present:
                    all_present = False

            if all_present:
                print(f"    ✅ PASS")
                results.append(True)
            else:
                print(f"    ❌ FAIL")
                results.append(False)

        passed = sum(results)
        total = len(results)
        print(f"\n  Total: {passed}/{total} edge cases passed")

        return all(results)


if __name__ == "__main__":
    test_results = []

    # Test 1: Full flow
    try:
        test = TestDefStrippingDuringExecution()
        test.setup_method()
        result = test.test_tool_code_through_full_flow()
        test_results.append(("Execution Trace - Full Flow", result))
        test.teardown_method()
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Execution Trace - Full Flow", False))

    # Test 2: Edge cases
    try:
        test = TestCodeExtractionLogic()
        result = test.test_metadata_extraction_edge_cases()
        test_results.append(("Code Extraction Edge Cases", result))
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Code Extraction Edge Cases", False))

    # Summary
    print("\n" + "="*70)
    print("EXECUTION TRACE TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    sys.exit(0 if passed == total else 1)
