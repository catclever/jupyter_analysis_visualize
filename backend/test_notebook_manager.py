"""
Test script for NotebookManager
Run this to verify the notebook generation works correctly
"""

from notebook_manager import NotebookManager
import json


def test_basic_notebook_creation():
    """Test creating a new notebook with various cell types"""
    print("=" * 60)
    print("Test 1: Basic Notebook Creation")
    print("=" * 60)

    manager = NotebookManager("test_notebook.ipynb")

    # Add title
    manager.append_markdown_cell("# Data Analysis Project\n\nRisk assessment and feature analysis")

    # Add imports
    manager.append_code_cell(
        code="import pandas as pd\nimport numpy as np",
        name="Imports"
    )

    # Add data source
    idx = manager.append_code_cell(
        code="""def load_users():
    return pd.read_csv('data/users.csv')

data_1 = load_users()
print(f"Loaded {len(data_1)} records")""",
        node_type="data_source",
        node_id="data_1",
        name="User Data"
    )
    print(f"✓ Added data_source node at index {idx}")

    # Add compute
    idx = manager.append_code_cell(
        code="""def feature_analysis(data_1, data_2):
    merged = data_1.merge(data_2)
    return merged.groupby('age').mean()

compute_1 = feature_analysis(data_1, data_2)""",
        node_type="compute",
        node_id="compute_1",
        depends_on=["data_1", "data_2"],
        name="Feature Analysis"
    )
    print(f"✓ Added compute node at index {idx}")

    # Add chart
    idx = manager.append_code_cell(
        code="""import plotly.graph_objects as go

def create_chart(data):
    fig = go.Figure(data=[go.Bar(x=data.index, y=data.values)])
    return fig

chart_1 = create_chart(compute_1)""",
        node_type="chart",
        node_id="chart_1",
        depends_on=["compute_1"],
        name="Result Chart"
    )
    print(f"✓ Added chart node at index {idx}")

    # Add tool
    idx = manager.append_code_cell(
        code="""def normalize(x):
    return (x - x.mean()) / x.std()

def tool_preprocessing(df, operation='normalize'):
    if operation == 'normalize':
        return normalize(df)

print("Preprocessing toolkit ready")""",
        node_type="tool",
        node_id="tool_preprocessing",
        name="Preprocessing Tools"
    )
    print(f"✓ Added tool node at index {idx}")

    # Save
    manager.save()
    print(f"\n✓ Notebook saved to {manager.notebook_path}")
    print(f"  Total cells: {manager.get_cell_count()}")


def test_append_cells():
    """Test appending to existing notebook"""
    print("\n" + "=" * 60)
    print("Test 2: Appending to Existing Notebook")
    print("=" * 60)

    manager = NotebookManager("test_notebook.ipynb")
    print(f"Loaded notebook with {manager.get_cell_count()} cells")

    # Append new section
    manager.append_markdown_cell("## Additional Analysis")
    idx = manager.append_code_cell(
        code="# Additional analysis code\nresult = compute_1.sum()",
        node_type="compute",
        node_id="compute_2",
        depends_on=["compute_1"],
        name="Summary Statistics"
    )
    print(f"✓ Appended new compute node at index {idx}")

    manager.save()
    print(f"✓ Notebook now has {manager.get_cell_count()} cells")


def test_node_parsing():
    """Test parsing node metadata"""
    print("\n" + "=" * 60)
    print("Test 3: Parsing Node Metadata")
    print("=" * 60)

    manager = NotebookManager("test_notebook.ipynb")
    node_cells = manager.list_node_cells()

    print(f"Found {len(node_cells)} node cells:")
    for i, cell in enumerate(node_cells, 1):
        meta = cell["metadata"]
        print(f"\n  {i}. Node: {meta.get('node_id', 'unknown')}")
        print(f"     Type: {meta.get('node_type', 'unknown')}")
        print(f"     Name: {meta.get('name', 'N/A')}")
        if meta.get('depends_on'):
            print(f"     Depends on: {meta.get('depends_on')}")


def test_insert_cells():
    """Test inserting cells at specific positions"""
    print("\n" + "=" * 60)
    print("Test 4: Inserting Cells at Specific Positions")
    print("=" * 60)

    manager = NotebookManager("test_notebook_insert.ipynb")

    # Build notebook with specific structure
    manager.append_markdown_cell("# Section 1")
    manager.append_code_cell("print('Cell 1')")
    manager.append_markdown_cell("# Section 2")

    print(f"Initial structure: {manager.get_cell_count()} cells")

    # Insert in middle
    manager.insert_markdown_cell(2, "## Inserted Section")
    manager.insert_code_cell(
        3,
        "print('Inserted cell')",
        node_type="compute",
        node_id="inserted_node",
        name="Inserted Node"
    )

    manager.save()
    print(f"✓ After insertion: {manager.get_cell_count()} cells")
    print(f"✓ Saved to {manager.notebook_path}")


def inspect_notebook_format():
    """Inspect the actual notebook JSON format"""
    print("\n" + "=" * 60)
    print("Test 5: Notebook JSON Format Inspection")
    print("=" * 60)

    manager = NotebookManager("test_notebook.ipynb")
    cells = manager.get_cells()

    # Show first node cell in detail
    node_cells = manager.list_node_cells()
    if node_cells:
        print(f"\nExample node cell structure:")
        print(json.dumps(node_cells[0], indent=2, ensure_ascii=False)[:500])
        print("...")

    # Show header comment format
    code_cells = manager.list_code_cells()
    if code_cells:
        first_code = code_cells[0]
        if first_code["cell_type"] == "code":
            print(f"\nExample code cell source (first 300 chars):")
            source = ''.join(first_code["source"])
            print(repr(source[:300]))


if __name__ == "__main__":
    # Run all tests
    test_basic_notebook_creation()
    test_append_cells()
    test_node_parsing()
    test_insert_cells()
    inspect_notebook_format()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nGenerated notebooks:")
    print("  - test_notebook.ipynb (main test)")
    print("  - test_notebook_insert.ipynb (insertion test)")
    print("\nYou can now open these in Jupyter to verify the format!")
