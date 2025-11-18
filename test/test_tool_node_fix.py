"""
Test to verify tool node execution fix
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager
from project_manager import ProjectManager
from code_executor import CodeExecutor
from kernel_manager import KernelManager


class TestToolNodeExecution:
    """Test tool node execution with proper auto-append logic"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tool_node_with_function_definition(self):
        """
        Test: Execute tool node with function definition

        Expected: Function should be defined in kernel without trying
                 to pickle a non-existent variable
        """
        print("\n" + "="*70)
        print("TEST: Tool Node with Function Definition")
        print("="*70)

        # Create notebook with tool node
        notebook_path = self.project_path / "project.ipynb"
        nm = NotebookManager(str(notebook_path))

        tool_code = """def feature_engineering(df, operation='polynomial_features'):
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
            code=tool_code,
            node_type="tool",
            node_id="tool_feature_eng"
        )
        nm.save()

        print("\n[STEP 1] Tool node code saved to notebook")
        print(f"  Code length: {len(tool_code)}")
        print(f"  Contains 'def feature_engineering': {'def feature_engineering' in tool_code}")

        # Create project metadata
        pm = ProjectManager("test_project", str(self.project_path))
        # Create project.json directly
        pm.project_data = {
            "project_id": "test_project",
            "project_name": "Test Project",
            "nodes": []
        }
        pm.add_node("tool_feature_eng", "tool", [])
        pm._save_metadata()

        print("\n[STEP 2] Project metadata created")

        # Execute the tool node
        ce = CodeExecutor("test_project", str(self.project_path))
        result = ce.execute_node("tool_feature_eng")

        print(f"\n[STEP 3] Tool node executed")
        print(f"  Execution status: {result['status']}")

        if result['status'] == 'error':
            print(f"  Error: {result.get('error_message')}")
            return False
        else:
            print(f"  ✓ Execution successful")

        # Check if function exists in kernel
        km = ce.km
        try:
            func_value = km.get_variable(ce.pm.project_id, "feature_engineering")
            print(f"\n[STEP 4] Function verification")
            print(f"  ✓ Function 'feature_engineering' exists in kernel")
            print(f"    Type: {type(func_value)}")
            print(f"    Callable: {callable(func_value)}")

            if callable(func_value):
                print(f"    ✓ Function is callable - SUCCESS!")
                return True
            else:
                print(f"    ✗ Function is NOT callable - FAILED!")
                return False
        except Exception as e:
            print(f"  ✗ Cannot access 'feature_engineering': {e}")
            return False
        finally:
            ce.km.shutdown_kernel(ce.pm.project_id)


if __name__ == "__main__":
    try:
        test = TestToolNodeExecution()
        test.setup_method()
        result = test.test_tool_node_with_function_definition()
        test.teardown_method()

        if result:
            print("\n✅ TEST PASSED: Tool node functions are preserved and callable")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Tool node function issue")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
