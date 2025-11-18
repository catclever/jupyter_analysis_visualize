"""
Detailed trace to find where code is being cleared during save
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


class TestCodeSaveTrace:
    """Detailed trace of code save process"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_code_trace(self):
        """
        Trace where code is lost during save
        """
        print("\n" + "="*80)
        print("TRACE: Code Save Process")
        print("="*80)

        # Create notebook
        notebook_path = self.project_path / "project.ipynb"
        nm = NotebookManager(str(notebook_path))

        original_code = """import pandas as pd

df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print("Data loaded")
data_1 = df"""

        print(f"\n[STEP 0] Original Code to Save")
        print(f"  Length: {len(original_code)}")
        print(f"  Content:\n{original_code}\n")

        # Add cell
        nm.append_code_cell(
            code=original_code,
            node_type="data_source",
            node_id="data_1"
        )
        nm.save()

        print(f"[STEP 1] After append_code_cell and save()")
        cells = nm.get_cells()
        cell = cells[0]
        source = cell.get('source', [])
        if isinstance(source, list):
            loaded_code = ''.join(source)
        else:
            loaded_code = source
        print(f"  Cell source length: {len(loaded_code)}")
        print(f"  Contains 'import pandas': {'import pandas' in loaded_code}")
        print(f"  Contains 'data_1 = df': {'data_1 = df' in loaded_code}")

        # Extract code part
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, loaded_code, re.DOTALL)
        just_code = match.group(1) if match else loaded_code
        print(f"  Just code length: {len(just_code)}")
        print(f"  Just code preview: {just_code[:100]}...")

        # Now simulate update_node_code
        print(f"\n[STEP 2] Simulate update_node_code - Send CODE TO BACKEND")
        code_from_frontend = just_code  # Frontend sends stripped code
        print(f"  Code from frontend length: {len(code_from_frontend)}")
        print(f"  Code from frontend content: {code_from_frontend[:50]}...")

        # Step 2a: Generate header (like app.py does)
        print(f"\n[STEP 3] Generate new header")
        header = NotebookManager._generate_header_from_metadata(
            node_type="data_source",
            node_id="data_1",
            execution_status='not_executed',
            depends_on=None,
            name=None
        )
        print(f"  Header length: {len(header)}")
        print(f"  Header preview: {header[:100]}...")

        # Step 2b: Combine header with code (like app.py line 861)
        print(f"\n[STEP 4] Combine header + code (line 861 in app.py)")
        full_code = header + '\n\n' + code_from_frontend
        print(f"  Full code length: {len(full_code)}")
        print(f"  Contains 'import pandas': {'import pandas' in full_code}")
        print(f"  Contains 'data_1 = df': {'data_1 = df' in full_code}")

        # Step 2c: Format source (like app.py lines 865-871)
        print(f"\n[STEP 5] Format source for Jupyter (like app.py lines 865-871)")
        lines = full_code.split('\n')
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + '\n')
            elif line:  # Only add last line if not empty
                source.append(line)
        formatted_code = ''.join(source)
        print(f"  Formatted source length: {len(formatted_code)}")
        print(f"  Contains 'import pandas': {'import pandas' in formatted_code}")
        print(f"  Contains 'data_1 = df': {'data_1 = df' in formatted_code}")

        # Now update the actual cell
        print(f"\n[STEP 6] Update cell source in notebook")
        cell['source'] = source
        nm.save()

        # Reload and check
        print(f"\n[STEP 7] Reload notebook and verify")
        nm_reload = NotebookManager(str(notebook_path))
        cells_reload = nm_reload.get_cells()
        cell_reload = cells_reload[0]
        source_reload = cell_reload.get('source', [])
        if isinstance(source_reload, list):
            loaded_code_reload = ''.join(source_reload)
        else:
            loaded_code_reload = source_reload
        print(f"  Reloaded cell source length: {len(loaded_code_reload)}")
        print(f"  Contains 'import pandas': {'import pandas' in loaded_code_reload}")
        print(f"  Contains 'data_1 = df': {'data_1 = df' in loaded_code_reload}")

        # Extract code part from reloaded
        match_reload = re.search(pattern, loaded_code_reload, re.DOTALL)
        just_code_reload = match_reload.group(1) if match_reload else loaded_code_reload
        print(f"  Extracted code length: {len(just_code_reload)}")
        print(f"  Extracted code preview: {just_code_reload[:100]}...")

        # Now test sync_metadata_comments (this might be the culprit!)
        print(f"\n[STEP 8] Call sync_metadata_comments (potential issue!)")
        result = nm_reload.sync_metadata_comments()
        print(f"  Sync result: {result}")

        # Check after sync
        print(f"\n[STEP 9] Check after sync_metadata_comments")
        cells_after_sync = nm_reload.get_cells()
        cell_after_sync = cells_after_sync[0]
        source_after_sync = cell_after_sync.get('source', [])
        if isinstance(source_after_sync, list):
            loaded_code_after_sync = ''.join(source_after_sync)
        else:
            loaded_code_after_sync = source_after_sync
        print(f"  Cell source length: {len(loaded_code_after_sync)}")
        print(f"  Contains 'import pandas': {'import pandas' in loaded_code_after_sync}")
        print(f"  Contains 'data_1 = df': {'data_1 = df' in loaded_code_after_sync}")

        match_after = re.search(pattern, loaded_code_after_sync, re.DOTALL)
        just_code_after = match_after.group(1) if match_after else loaded_code_after_sync
        print(f"  Extracted code length: {len(just_code_after)}")
        if len(just_code_after) < 10:
            print(f"  ❌ CODE WAS CLEARED!")
            print(f"  Just code content: '{just_code_after}'")
            return False
        else:
            print(f"  ✓ Code preserved: {just_code_after[:50]}...")
            return True


if __name__ == "__main__":
    try:
        test = TestCodeSaveTrace()
        test.setup_method()
        result = test.test_save_code_trace()
        test.teardown_method()

        if result:
            print("\n✅ TEST PASSED: Code is preserved during save")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Code was cleared somewhere")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
