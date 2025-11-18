"""
Test script for ProjectManager

Tests project creation, metadata management, and file operations
"""

import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_manager import ProjectManager, ProjectMetadata


def test_project_creation():
    """Test creating a new project"""
    print("=" * 60)
    print("Test 1: Project Creation")
    print("=" * 60)

    # Use temporary test directory
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    # Create project
    pm = ProjectManager(str(test_root), "test_analysis")
    pm.create(
        name="Test Analysis Project",
        description="A test project for feature analysis"
    )

    print(f"✓ Created project: {pm.project_id}")
    print(f"  Path: {pm.project_path}")
    print(f"  Directories created:")
    print(f"    - {pm.project_path}")
    print(f"    - {pm.parquets_path}")
    print(f"    - {pm.nodes_path}")

    # Verify structure
    assert pm.project_path.exists(), "Project path should exist"
    assert pm.notebook_path.exists(), "Notebook should exist"
    assert pm.metadata_path.exists(), "Metadata should exist"
    assert pm.parquets_path.exists(), "Parquets directory should exist"

    print("✓ Directory structure verified")

    # Verify metadata
    assert pm.metadata is not None, "Metadata should be loaded"
    assert pm.metadata.project_id == "test_analysis"
    assert pm.metadata.name == "Test Analysis Project"

    print("✓ Metadata verified")


def test_add_nodes():
    """Test adding nodes to project"""
    print("\n" + "=" * 60)
    print("Test 2: Adding Nodes")
    print("=" * 60)

    test_root = Path("test_projects")
    pm = ProjectManager(str(test_root), "test_analysis")
    pm.load()

    # Add data source node
    idx1 = pm.add_node(
        node_id="data_1",
        node_type="data_source",
        name="User Data",
        code="""def load_users():
    return pd.read_csv('users.csv')

data_1 = load_users()
print(f"Loaded {len(data_1)} users")""",
        node_description="## Loading User Data\n\nLoad user information from CSV"
    )
    print(f"✓ Added data_source node at cell index {idx1}")

    # Add compute node
    idx2 = pm.add_node(
        node_id="compute_1",
        node_type="compute",
        name="Feature Analysis",
        depends_on=["data_1"],
        code="""def analyze_features(data_1):
    return data_1.groupby('age').agg({'income': 'mean'})

compute_1 = analyze_features(data_1)
print(compute_1)""",
        node_description="## Feature Analysis\n\nAnalyze key features by age group"
    )
    print(f"✓ Added compute node at cell index {idx2}")

    # Add chart node
    idx3 = pm.add_node(
        node_id="chart_1",
        node_type="chart",
        name="Age Distribution Chart",
        depends_on=["compute_1"],
        code="""import plotly.graph_objects as go

def create_chart(data):
    fig = go.Figure(data=[go.Bar(x=data.index, y=data['income'])])
    return fig

chart_1 = create_chart(compute_1)""",
        node_description="## Visualization\n\nVisualize analysis results"
    )
    print(f"✓ Added chart node at cell index {idx3}")

    # Add tool node
    idx4 = pm.add_node(
        node_id="tool_preprocessing",
        node_type="tool",
        name="Data Preprocessing Tools",
        code="""from toolkits.data_analysis.feature_engineering import feature_engineering

# Tools now available in kernel
print("Feature engineering toolkit loaded")"""
    )
    print(f"✓ Added tool node at cell index {idx4}")

    # Verify nodes in metadata
    assert len(pm.list_nodes()) == 4, "Should have 4 nodes"
    assert len(pm.list_nodes_by_type("data_source")) == 1
    assert len(pm.list_nodes_by_type("compute")) == 1
    assert len(pm.list_nodes_by_type("chart")) == 1
    assert len(pm.list_nodes_by_type("tool")) == 1

    print(f"✓ All {len(pm.list_nodes())} nodes verified in metadata")


def test_save_and_load_results():
    """Test saving and loading node results"""
    print("\n" + "=" * 60)
    print("Test 3: Save and Load Results")
    print("=" * 60)

    test_root = Path("test_projects")
    pm = ProjectManager(str(test_root), "test_analysis")
    pm.load()

    # Create sample DataFrame
    df = pd.DataFrame({
        'age': [25, 30, 35, 40],
        'income': [50000, 60000, 70000, 80000],
        'score': [0.8, 0.85, 0.9, 0.95]
    })

    # Save as parquet
    path1 = pm.save_node_result("compute_1", df)
    print(f"✓ Saved DataFrame to: {path1}")
    assert Path(path1).exists(), "Parquet file should exist"

    # Save as JSON
    json_data = {"result": "success", "count": 100}
    path2 = pm.save_node_result("chart_1", json_data)
    print(f"✓ Saved dict to: {path2}")
    assert Path(path2).exists(), "JSON file should exist"

    # Load results back
    loaded_df = pm.load_node_result("compute_1")
    print(f"✓ Loaded DataFrame: shape={loaded_df.shape}")
    assert isinstance(loaded_df, pd.DataFrame)
    assert len(loaded_df) == 4

    loaded_json = pm.load_node_result("chart_1")
    print(f"✓ Loaded dict: {loaded_json}")
    assert isinstance(loaded_json, dict)
    assert loaded_json["result"] == "success"

    # List all results
    results = pm.list_results()
    print(f"✓ Listed {len(results)} results:")
    for result in results:
        print(f"  - {result['node_id']}.{result['format']} ({result['size_bytes']} bytes)")


def test_project_info():
    """Test getting project information"""
    print("\n" + "=" * 60)
    print("Test 4: Project Information")
    print("=" * 60)

    test_root = Path("test_projects")
    pm = ProjectManager(str(test_root), "test_analysis")
    pm.load()

    info = pm.get_project_info()
    print(f"Project: {info['project_id']}")
    print(f"Path: {info['path']}")
    print(f"Metadata:")
    print(f"  - Name: {info['metadata']['name']}")
    print(f"  - Version: {info['metadata']['version']}")
    print(f"  - Nodes: {len(info['metadata']['nodes'])}")
    print(f"Notebook: {info['notebook_cells']} total cells, {info['node_cells']} node cells")
    print(f"Results: {len(info['results'])} files")

    assert info['project_id'] == "test_analysis"
    assert len(info['metadata']['nodes']) == 4
    assert info['notebook_cells'] > 0

    print("✓ Project info verified")


def test_metadata_export():
    """Test exporting metadata"""
    print("\n" + "=" * 60)
    print("Test 5: Metadata Export")
    print("=" * 60)

    test_root = Path("test_projects")
    pm = ProjectManager(str(test_root), "test_analysis")
    pm.load()

    export_path = test_root / "exported_metadata.json"
    pm.export_metadata_json(str(export_path))

    print(f"✓ Exported metadata to: {export_path}")
    assert export_path.exists()

    # Verify exported content
    with open(export_path, 'r') as f:
        exported = json.load(f)

    assert exported['project_id'] == "test_analysis"
    assert len(exported['nodes']) == 4
    print("✓ Exported metadata verified")


def test_load_existing_project():
    """Test loading an existing project"""
    print("\n" + "=" * 60)
    print("Test 6: Load Existing Project")
    print("=" * 60)

    test_root = Path("test_projects")
    pm = ProjectManager(str(test_root), "test_analysis")

    # Project should exist from previous tests
    assert pm.exists(), "Project should exist"
    print(f"✓ Project exists: {pm.project_id}")

    # Load it
    pm.load()
    print(f"✓ Loaded project")

    # Verify content
    assert pm.metadata is not None
    assert len(pm.list_nodes()) == 4
    assert pm.notebook_manager is not None

    print(f"✓ Project loaded successfully")
    print(f"  - Nodes: {len(pm.list_nodes())}")
    print(f"  - Notebook cells: {len(pm.notebook_manager.get_cells())}")


def cleanup():
    """Clean up test artifacts"""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)

    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)
        print(f"✓ Removed test directory: {test_root}")


if __name__ == "__main__":
    try:
        test_project_creation()
        test_add_nodes()
        test_save_and_load_results()
        test_project_info()
        test_metadata_export()
        test_load_existing_project()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    finally:
        cleanup()
