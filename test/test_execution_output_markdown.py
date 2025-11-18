"""
Test execution output being included in generated markdown
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager
from project_manager import ProjectManager
from code_executor import CodeExecutor
from kernel_manager import KernelManager


class TestExecutionOutputMarkdown:
    """Test that execution output is included in markdown"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_execution_output_in_markdown(self):
        """
        Test: Execution output should be included in generated markdown

        Expected:
        1. Code with print statements executes
        2. Output is captured from kernel
        3. Markdown cell includes the output in code block
        4. Markdown shows "Execution Output" section
        """
        print("\n" + "="*70)
        print("TEST: Execution Output Included in Markdown")
        print("="*70)

        # Create notebook with code that has print statements
        notebook_path = self.project_path / "project.ipynb"
        nm = NotebookManager(str(notebook_path))

        code_with_output = """# Data processing node
import pandas as pd
import numpy as np

# Create sample data
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 75000]
}

df = pd.DataFrame(data)

# Print some information
print("Data Summary:")
print(f"  Total records: {len(df)}")
print(f"  Columns: {list(df.columns)}")
print(f"  Average age: {df['age'].mean():.1f}")
print()
print("DataFrame:")
print(df.to_string())

# Assign to node variable for result capture
data_1 = df"""

        nm.append_code_cell(
            code=code_with_output,
            node_type="data_source",
            node_id="data_1",
            name="Load Data"
        )
        nm.save()

        print("\n[STEP 1] Code cell created with print statements")
        print(f"  Code length: {len(code_with_output)}")
        print(f"  Contains prints: {'print(' in code_with_output}")

        # Create project.json directly
        project_json = self.project_path / "project.json"
        project_data = {
            "project_id": "test_project",
            "project_name": "Test Project",
            "nodes": [
                {
                    "node_id": "data_1",
                    "type": "data_source",
                    "name": "Load Data",
                    "depends_on": [],
                    "execution_status": "not_executed"
                }
            ]
        }
        with open(project_json, 'w') as f:
            import json
            json.dump(project_data, f, indent=2)

        pm = ProjectManager("test_project", str(self.project_path))

        print("\n[STEP 2] Project metadata created")

        # Execute the node
        ce = CodeExecutor(pm, KernelManager(), nm)
        result = ce.execute_node("data_1")

        print(f"\n[STEP 3] Node executed")
        print(f"  Status: {result['status']}")

        if result['status'] != 'success':
            print(f"  Error: {result.get('error_message')}")
            return False

        # Check if markdown cell was created
        print("\n[STEP 4] Check markdown cell")
        cells = nm.get_cells()
        markdown_cells = [c for c in cells if c.get('cell_type') == 'markdown']

        print(f"  Total cells: {len(cells)}")
        print(f"  Markdown cells: {len(markdown_cells)}")

        # Find markdown cell linked to data_1
        output_cell = None
        for cell in markdown_cells:
            metadata = cell.get('metadata', {})
            if metadata.get('linked_node_id') == 'data_1':
                output_cell = cell
                break

        if not output_cell:
            print("  ✗ No markdown cell found linked to data_1")
            return False

        print("  ✓ Markdown cell found")

        # Check markdown content
        md_source = output_cell.get('source', [])
        if isinstance(md_source, list):
            md_text = ''.join(md_source)
        else:
            md_text = md_source

        print(f"\n[STEP 5] Verify markdown content")
        print(f"  Markdown length: {len(md_text)}")

        checks = {
            "Contains 'Execution Complete'": "Execution Complete" in md_text,
            "Contains 'Execution Output'": "Execution Output" in md_text,
            "Contains 'Load Data' node name": "Load Data" in md_text,
            "Contains execution time": "Execution time:" in md_text,
            "Contains status check": "✅ Success" in md_text,
            "Contains code block (code fence)": "```" in md_text,
            "Contains print output": "Data Summary:" in md_text or "Total records:" in md_text,
        }

        all_passed = True
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}: {result}")
            if not result:
                all_passed = False

        if all_passed:
            print("\n[STEP 6] Show markdown content preview")
            print("\n" + "="*70)
            print("Generated Markdown:")
            print("="*70)
            print(md_text[:500] + "..." if len(md_text) > 500 else md_text)
            print("="*70)

        # Clean up
        ce.km.shutdown_kernel(ce.pm.project_id)

        return all_passed


if __name__ == "__main__":
    try:
        test = TestExecutionOutputMarkdown()
        test.setup_method()
        result = test.test_execution_output_in_markdown()
        test.teardown_method()

        if result:
            print("\n✅ TEST PASSED: Execution output included in markdown")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Execution output not properly included")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
