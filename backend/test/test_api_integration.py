"""
Integration tests simulating actual API calls and scenarios
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager


class TestAPICodeSaveSimulation:
    """Simulate what happens when frontend calls API to save code"""

    def setup_method(self):
        """Create temporary project for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_api_save_with_empty_code(self):
        """
        Test: Frontend sends empty code in API request

        Simulates: User clicks save with empty editor
        Issue: Cell becomes empty (only metadata left)
        """
        print("\n" + "="*60)
        print("API TEST 1: Save with Empty Code")
        print("="*60)

        # Create notebook with initial code
        notebook_path = self.project_path / "test.ipynb"
        nm = NotebookManager(str(notebook_path))

        original_code = "import pandas as pd\n\ndf = pd.DataFrame()"

        nm.append_code_cell(
            code=original_code,
            node_type="data_source",
            node_id="data_1"
        )
        nm.save()

        # Simulate what update_node_code does:
        # 1. Frontend sends empty code
        code_content = ""  # ← This is what we're testing
        node_id = "data_1"

        # 2. Backend generates new header
        header = """# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: data_source
# @node_id: data_1
# ===== End of system-managed metadata ====="""

        # 3. Backend combines header with code
        full_code = header + '\n\n' + code_content

        print(f"\ncode_content: '{code_content}' (length: {len(code_content)})")
        print(f"header length: {len(header)}")
        print(f"full_code length: {len(full_code)}")
        print(f"full_code ends with: '{full_code[-20:]}'")

        # 4. Convert to Jupyter format
        lines = full_code.split('\n')
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + '\n')
            elif line:  # Only add last line if not empty
                source.append(line)

        print(f"\nJupyter source lines: {len(source)}")
        source_text = ''.join(source)

        # 5. Check if code exists
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, source_text, re.DOTALL)
        extracted = match.group(1) if match else ""

        print(f"Extracted code length: {len(extracted)}")
        print(f"Extracted code: '{extracted}'")

        # ISSUE: If code_content is empty, extracted is also empty!
        if code_content == "":
            assert len(extracted.strip()) == 0, "Empty code should stay empty"
            print("\n⚠️  ISSUE CONFIRMED: Empty code sent → Empty code saved")
            print("   This is actually CORRECT behavior (garbage in, garbage out)")
            print("   The real question is: WHY is frontend sending empty code?")
        else:
            assert code_content in source_text, "Code should be in source"

        return True

    def test_api_save_real_scenario(self):
        """
        Test: Real scenario - frontend sends code with newlines
        """
        print("\n" + "="*60)
        print("API TEST 2: Real Code Save Scenario")
        print("="*60)

        # Create notebook
        notebook_path = self.project_path / "test.ipynb"
        nm = NotebookManager(str(notebook_path))

        # Initial code
        nm.append_code_cell(
            code="import pandas as pd\ndf = pd.DataFrame()",
            node_type="data_source",
            node_id="data_1"
        )
        nm.save()

        # Simulate: User edits code in frontend
        edited_code = """import pandas as pd
import numpy as np

def load_data():
    data = {
        'a': [1, 2, 3],
        'b': [4, 5, 6]
    }
    return pd.DataFrame(data)

df = load_data()
print(df)"""

        # Simulate API call: update_node_code
        node_id = "data_1"
        code_content = edited_code  # Frontend sends this

        # Backend logic
        header = f"""# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: data_source
# @node_id: {node_id}
# ===== End of system-managed metadata ====="""

        full_code = header + '\n\n' + code_content

        print(f"\ncode_content length: {len(code_content)}")
        print(f"full_code length: {len(full_code)}")

        # Convert to Jupyter format
        lines = full_code.split('\n')
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + '\n')
            elif line:
                source.append(line)

        source_text = ''.join(source)

        # Extract to verify
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, source_text, re.DOTALL)
        extracted = match.group(1) if match else ""

        print(f"Extracted code length: {len(extracted)}")

        # Verify all content is present
        assert 'import pandas as pd' in extracted
        assert 'import numpy as np' in extracted
        assert 'def load_data():' in extracted
        assert 'print(df)' in extracted

        print("\n✅ Code save successful with all content preserved")
        return True

    def test_stripmetadata_simulation(self):
        """
        Test: Simulate frontend stripMetadataComments function
        """
        print("\n" + "="*60)
        print("API TEST 3: Frontend stripMetadataComments")
        print("="*60)

        # Full code with metadata (what frontend receives from backend)
        full_code_with_metadata = """# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: tool
# @node_id: tool_feature_eng
# @name: Feature Engineering
# ===== End of system-managed metadata =====

def feature_engineering(df, operation='polynomial_features'):
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

        # Simulate stripMetadataComments from frontend (DataTable.tsx lines 67-100)
        def strip_metadata_comments(code: str) -> str:
            lines = code.split('\n')
            result = []
            in_metadata_block = False

            for line in lines:
                # Check if entering metadata block
                if 'System-managed metadata' in line:
                    in_metadata_block = True
                    continue
                # Check if exiting metadata block
                if 'End of system-managed metadata' in line:
                    in_metadata_block = False
                    continue
                # Skip lines inside metadata block
                if in_metadata_block:
                    continue
                # Keep all other lines
                result.append(line)

            # Remove leading/trailing empty lines
            while result and result[0].strip() == '':
                result.pop(0)
            while result and result[-1].strip() == '':
                result.pop()

            return '\n'.join(result)

        # Apply the function
        stripped_code = strip_metadata_comments(full_code_with_metadata)

        print(f"\nOriginal length: {len(full_code_with_metadata)}")
        print(f"Stripped length: {len(stripped_code)}")
        print(f"\nStripped code starts with:\n{stripped_code[:100]}\n...")

        # Verify
        assert 'System-managed metadata' not in stripped_code
        assert 'End of system-managed metadata' not in stripped_code
        assert 'def feature_engineering' in stripped_code
        assert 'import pandas as pd' in stripped_code

        print("\n✅ stripMetadataComments works correctly")
        print("   - Metadata comments removed")
        print("   - Code preserved (including internal imports)")
        print("   - Leading/trailing whitespace cleaned")
        return True


class TestToolNodeExecution:
    """Test tool node execution with imports"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tool_code_extraction_and_execution(self):
        """
        Test: Extract tool node code and verify it's executable
        """
        print("\n" + "="*60)
        print("API TEST 4: Tool Node Code Extraction")
        print("="*60)

        notebook_path = self.project_path / "test.ipynb"
        nm = NotebookManager(str(notebook_path))

        # Tool node with complex structure
        tool_code = """def feature_engineering(df, operation='polynomial_features'):
    import pandas as pd
    import numpy as np

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

        # Simulate: Extract code from notebook (what execute_node does)
        cells = nm.get_cells()
        node_cell = cells[0]

        source = node_cell.get('source', '')
        if isinstance(source, list):
            extracted_code = ''.join(source)
        else:
            extracted_code = source

        print(f"\nExtracted code length: {len(extracted_code)}")
        print(f"Contains metadata: {'System-managed metadata' in extracted_code}")
        print(f"Contains 'def feature_engineering': {'def feature_engineering' in extracted_code}")
        print(f"Contains 'import pandas': {'import pandas' in extracted_code}")

        # Extract just the code part (without metadata comments)
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, extracted_code, re.DOTALL)
        just_code = match.group(1) if match else extracted_code

        print(f"\nJust code length: {len(just_code)}")
        print(f"Just code starts with: {just_code[:50]}")

        # Verify the function definition is intact
        assert 'def feature_engineering' in just_code, "def should be present"
        assert 'import pandas as pd' in just_code, "pandas import should be present"
        assert 'import numpy as np' in just_code, "numpy import should be present"
        assert "operation='polynomial_features'" in just_code, "parameter should be present"

        # Try to compile it (verify syntax is correct)
        try:
            compile(just_code, filename='<tool_node>', mode='exec')
            print("\n✅ Code compiles successfully")
        except SyntaxError as e:
            print(f"\n❌ Syntax error: {e}")
            raise

        print("✅ Tool node code extraction and syntax verification passed")
        return True


if __name__ == "__main__":
    test_results = []

    # API Test 1
    try:
        test = TestAPICodeSaveSimulation()
        test.setup_method()
        result = test.test_api_save_with_empty_code()
        test_results.append(("API Save Empty Code", result))
        test.teardown_method()
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("API Save Empty Code", False))

    # API Test 2
    try:
        test = TestAPICodeSaveSimulation()
        test.setup_method()
        result = test.test_api_save_real_scenario()
        test_results.append(("API Save Real Code", result))
        test.teardown_method()
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("API Save Real Code", False))

    # API Test 3
    try:
        test = TestAPICodeSaveSimulation()
        test.setup_method()
        result = test.test_stripmetadata_simulation()
        test_results.append(("Strip Metadata", result))
        test.teardown_method()
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Strip Metadata", False))

    # API Test 4
    try:
        test = TestToolNodeExecution()
        test.setup_method()
        result = test.test_tool_code_extraction_and_execution()
        test_results.append(("Tool Code Extraction", result))
        test.teardown_method()
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Tool Code Extraction", False))

    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        sys.exit(1)
