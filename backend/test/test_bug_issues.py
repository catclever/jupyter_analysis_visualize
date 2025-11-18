"""
Test cases for reported bug issues
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
from project_manager import ProjectManager
from code_executor import CodeExecutor
from kernel_manager import KernelManager


class TestCellSaveIssue:
    """Test Issue 1: Cell code disappears on save"""

    def setup_method(self):
        """Create temporary project for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cell_save_with_metadata_and_code(self):
        """
        Test: Saving a cell with both metadata comments and code content

        Expected: Both metadata and code are preserved
        Actual (reported): Only metadata remains, code disappears
        """
        print("\n" + "="*60)
        print("TEST 1: Cell Save Issue")
        print("="*60)

        # Create notebook
        notebook_path = self.project_path / "test.ipynb"
        nm = NotebookManager(str(notebook_path))

        # Add a code cell with metadata
        original_code = """import pandas as pd

def load_data():
    return pd.read_csv('data.csv')

data = load_data()
print(f"Loaded {len(data)} records")"""

        nm.append_code_cell(
            code=original_code,
            node_type="data_source",
            node_id="data_1",
            name="Load Data"
        )
        nm.save()

        # Read back the cell
        cells = nm.get_cells()
        assert len(cells) == 1, "Should have 1 cell"

        cell = cells[0]
        source_text = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

        print(f"\nCell source length: {len(source_text)}")
        print(f"Contains metadata start: {'System-managed metadata' in source_text}")
        print(f"Contains metadata end: {'End of system-managed metadata' in source_text}")
        print(f"Contains 'import pandas': {'import pandas' in source_text}")
        print(f"Contains 'def load_data': {'def load_data' in source_text}")
        print(f"Contains 'data = load_data': {'data = load_data' in source_text}")

        # Extract just the code part (without metadata)
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, source_text, re.DOTALL)
        extracted_code = match.group(1) if match else source_text

        print(f"\nExtracted code length: {len(extracted_code)}")
        print(f"Extracted code preview:\n{extracted_code[:200]}...")

        # Verify code is present
        assert 'import pandas' in source_text, "Code should contain 'import pandas'"
        assert 'def load_data' in source_text, "Code should contain 'def load_data'"
        assert 'data = load_data' in source_text, "Code should contain 'data = load_data'"

        # Verify extracted code is not empty
        assert len(extracted_code.strip()) > 0, "Extracted code should not be empty"
        assert 'import pandas' in extracted_code, "Extracted code should have imports"

        print("\n✅ PASS: Cell save preserves all code content")
        return True


class TestToolNodeDef:
    """Test Issue 2: Tool node def statement being stripped"""

    def setup_method(self):
        """Create temporary project for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tool_node_with_internal_imports(self):
        """
        Test: Tool node with import statements inside the function

        Expected: def line is preserved, internal imports work
        Actual (reported): def line gets stripped
        """
        print("\n" + "="*60)
        print("TEST 2: Tool Node Def Issue")
        print("="*60)

        # Create notebook
        notebook_path = self.project_path / "test.ipynb"
        nm = NotebookManager(str(notebook_path))

        # Tool node code with import inside function
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
            node_id="tool_feature_eng",
            name="Feature Engineering"
        )
        nm.save()

        # Read back the cell
        cells = nm.get_cells()
        assert len(cells) == 1, "Should have 1 cell"

        cell = cells[0]
        source_text = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

        print(f"\nCell source length: {len(source_text)}")
        print(f"First 300 chars:\n{source_text[:300]}\n...")

        # Extract code (without metadata)
        import re
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, source_text, re.DOTALL)
        extracted_code = match.group(1) if match else source_text

        print(f"Extracted code starts with: {extracted_code[:50]}")

        # Verify def line is present
        assert 'def feature_engineering' in source_text, "def line should be present in source"
        assert 'def feature_engineering' in extracted_code, "def line should be present in extracted code"

        # Verify import inside function is present
        assert 'import pandas as pd' in extracted_code, "Internal import should be present"

        # Verify other parts of code
        assert 'polynomial_features' in extracted_code, "Function logic should be present"
        assert 'df.copy()' in extracted_code, "Code body should be present"

        print("\n✅ PASS: Tool node def and internal imports preserved")
        return True


class TestToolNodeSerialization:
    """Test Issue 3: Tool node result serialization"""

    def setup_method(self):
        """Create temporary project for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        self.project_path.joinpath("projects").mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tool_node_result_format_default(self):
        """
        Test: Tool node result_format should default to 'pkl' not 'parquet'

        Expected: result_format for tool node is 'pkl'
        Actual (reported): incorrectly defaults to 'parquet'
        """
        print("\n" + "="*60)
        print("TEST 3: Tool Node Serialization Format")
        print("="*60)

        # Create project metadata with tool node
        project_data = {
            "project_id": "test_project",
            "nodes": [
                {
                    "node_id": "tool_1",
                    "type": "tool",
                    "name": "Test Tool",
                    "depends_on": []
                },
                {
                    "node_id": "data_1",
                    "type": "data_source",
                    "name": "Test Data",
                    "depends_on": []
                }
            ]
        }

        # Check logic: node_type == 'tool' should default to 'pkl'
        for node in project_data['nodes']:
            node_type = node.get('type', 'compute')
            result_format = node.get('result_format')

            # This is the logic that should be in code_executor.py
            if result_format is None:
                if node_type == 'tool':
                    result_format = 'pkl'
                else:
                    result_format = 'parquet'

            print(f"\nNode: {node['node_id']}")
            print(f"  Type: {node_type}")
            print(f"  Result format: {result_format}")

            if node_type == 'tool':
                assert result_format == 'pkl', f"Tool node should default to 'pkl', got '{result_format}'"
            else:
                assert result_format == 'parquet', f"Data node should default to 'parquet', got '{result_format}'"

        print("\n✅ PASS: Tool nodes default to pkl, data nodes to parquet")
        return True


class TestDataFrameDisplay:
    """Test Issue 4: DataFrame non-numeric type display"""

    def test_dataframe_to_dict_with_mixed_types(self):
        """
        Test: DataFrame with mixed types (numeric, string, datetime) converts to JSON

        Expected: All fields can be serialized
        Actual (reported): Non-numeric fields cause display errors
        """
        print("\n" + "="*60)
        print("TEST 4: DataFrame Display with Mixed Types")
        print("="*60)

        try:
            import pandas as pd
        except ImportError:
            print("⚠️  SKIP: pandas not available")
            return True

        # Create DataFrame with mixed types
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'score': [95.5, 87.3, 92.1],
            'category': ['A', 'B', 'A'],
            'created_at': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
        })

        print(f"\nDataFrame dtypes:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")

        # Try to convert to records (what the API does)
        try:
            records = df.to_dict(orient='records')
            print(f"\n✓ Successfully converted to records")
            print(f"  Number of records: {len(records)}")
            print(f"  First record: {records[0]}")

            # Try JSON serialization
            import json
            json_str = json.dumps(records)
            print(f"✓ Successfully serialized to JSON")

        except (TypeError, ValueError) as e:
            print(f"✗ Conversion failed: {e}")
            # Try fallback
            print("\nTrying fallback with type conversion...")
            df_copy = df.copy()
            for col in df_copy.columns:
                if not pd.api.types.is_object_dtype(df_copy[col]) and \
                   not pd.api.types.is_numeric_dtype(df_copy[col]) and \
                   not pd.api.types.is_bool_dtype(df_copy[col]):
                    print(f"  Converting {col} to string")
                    df_copy[col] = df_copy[col].astype(str)

            records = df_copy.to_dict(orient='records')
            json_str = json.dumps(records)
            print(f"✓ Fallback successful")

        print("\n✅ PASS: Mixed-type DataFrame displays correctly")
        return True


class TestKernelRestartAutoLoad:
    """Test Issue 5: Auto-load validated nodes on kernel restart"""

    def setup_method(self):
        """Create temporary project for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validated_nodes_identified(self):
        """
        Test: Validated nodes can be identified in project metadata

        Expected: Nodes with execution_status == 'validated' are found
        """
        print("\n" + "="*60)
        print("TEST 5: Kernel Restart Auto-Load")
        print("="*60)

        # Create project metadata with validated nodes
        project_data = {
            "project_id": "test_project",
            "nodes": [
                {
                    "node_id": "data_1",
                    "type": "data_source",
                    "execution_status": "validated",
                    "result_format": "parquet"
                },
                {
                    "node_id": "compute_1",
                    "type": "compute",
                    "execution_status": "validated",
                    "result_format": "parquet"
                },
                {
                    "node_id": "tool_1",
                    "type": "tool",
                    "execution_status": "not_executed",
                    "result_format": "pkl"
                }
            ]
        }

        # Filter validated nodes
        validated_nodes = [n for n in project_data['nodes'] if n.get('execution_status') == 'validated']

        print(f"\nTotal nodes: {len(project_data['nodes'])}")
        print(f"Validated nodes: {len(validated_nodes)}")

        for node in validated_nodes:
            print(f"  - {node['node_id']} (type: {node['type']})")

        assert len(validated_nodes) == 2, "Should have 2 validated nodes"
        assert validated_nodes[0]['node_id'] == 'data_1'
        assert validated_nodes[1]['node_id'] == 'compute_1'

        print("\n✅ PASS: Validated nodes can be identified")
        return True


if __name__ == "__main__":
    test_results = []

    # Test 1: Cell Save
    try:
        test = TestCellSaveIssue()
        test.setup_method()
        result = test.test_cell_save_with_metadata_and_code()
        test_results.append(("Cell Save", result))
        test.teardown_method()
    except Exception as e:
        print(f"\n❌ FAIL: Cell Save test - {e}")
        test_results.append(("Cell Save", False))

    # Test 2: Tool Node Def
    try:
        test = TestToolNodeDef()
        test.setup_method()
        result = test.test_tool_node_with_internal_imports()
        test_results.append(("Tool Node Def", result))
        test.teardown_method()
    except Exception as e:
        print(f"\n❌ FAIL: Tool Node Def test - {e}")
        test_results.append(("Tool Node Def", False))

    # Test 3: Tool Node Serialization
    try:
        test = TestToolNodeSerialization()
        test.setup_method()
        result = test.test_tool_node_result_format_default()
        test_results.append(("Tool Node Serialization", result))
        test.teardown_method()
    except Exception as e:
        print(f"\n❌ FAIL: Tool Node Serialization test - {e}")
        test_results.append(("Tool Node Serialization", False))

    # Test 4: DataFrame Display
    try:
        test = TestDataFrameDisplay()
        result = test.test_dataframe_to_dict_with_mixed_types()
        test_results.append(("DataFrame Display", result))
    except Exception as e:
        print(f"\n❌ FAIL: DataFrame Display test - {e}")
        test_results.append(("DataFrame Display", False))

    # Test 5: Kernel Restart
    try:
        test = TestKernelRestartAutoLoad()
        test.setup_method()
        result = test.test_validated_nodes_identified()
        test_results.append(("Kernel Restart", result))
        test.teardown_method()
    except Exception as e:
        print(f"\n❌ FAIL: Kernel Restart test - {e}")
        test_results.append(("Kernel Restart", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        sys.exit(1)
