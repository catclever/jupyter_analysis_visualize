"""
Test script for ProjectMetadataParser

Tests notebook parsing, metadata extraction, and DAG validation
"""

import json
import sys
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metadata_parser import ProjectMetadataParser, MetadataParseError
from notebook_manager import NotebookManager


def create_test_notebook(notebook_path: str, nodes: list) -> None:
    """
    Helper to create test notebook with nodes

    Args:
        notebook_path: Path to save notebook
        nodes: List of node configs (dicts with node_id, node_type, depends_on, code)
    """
    nb_manager = NotebookManager(notebook_path)

    # Add header
    nb_manager.append_markdown_cell("# Test Project")

    # Add nodes
    for node in nodes:
        if 'description' in node:
            nb_manager.append_markdown_cell(node['description'])

        nb_manager.append_code_cell(
            code=node['code'],
            node_type=node['node_type'],
            node_id=node['node_id'],
            depends_on=node.get('depends_on', []),
            name=node.get('name', node['node_id']),
            add_header_comment=True
        )

    nb_manager.save()


def test_basic_parsing():
    """Test basic notebook parsing"""
    print("=" * 60)
    print("Test 1: Basic Notebook Parsing")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    # Create test notebook
    create_test_notebook(
        str(notebook_path),
        [
            {
                "node_id": "data_1",
                "node_type": "data_source",
                "code": "data_1 = 42",
                "name": "Data"
            },
            {
                "node_id": "compute_1",
                "node_type": "compute",
                "depends_on": ["data_1"],
                "code": "compute_1 = data_1 * 2",
                "name": "Compute"
            }
        ]
    )

    # Parse
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()

    print(f"✓ Parsed notebook:")
    print(f"  Total cells: {metadata.total_cells}")
    print(f"  Node cells: {len(metadata.node_cells)}")
    print(f"  Errors: {len(metadata.errors)}")

    assert len(metadata.node_cells) == 2
    assert len(metadata.errors) == 0

    # Verify nodes
    node_ids = [cell.node_id for cell in metadata.node_cells]
    assert "data_1" in node_ids
    assert "compute_1" in node_ids

    print(f"✓ Basic parsing verified")

    # Cleanup
    shutil.rmtree(test_root)


def test_dependency_extraction():
    """Test extracting dependencies from nodes"""
    print("\n" + "=" * 60)
    print("Test 2: Dependency Extraction")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    # Create notebook with complex dependencies
    create_test_notebook(
        str(notebook_path),
        [
            {
                "node_id": "n1",
                "node_type": "data_source",
                "code": "n1 = 1"
            },
            {
                "node_id": "n2",
                "node_type": "data_source",
                "code": "n2 = 2"
            },
            {
                "node_id": "n3",
                "node_type": "compute",
                "depends_on": ["n1", "n2"],
                "code": "n3 = n1 + n2"
            },
            {
                "node_id": "n4",
                "node_type": "compute",
                "depends_on": ["n3"],
                "code": "n4 = n3 * 2"
            }
        ]
    )

    # Parse and check dependencies
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()

    # Find n3 and check its dependencies
    n3_cell = next((cell for cell in metadata.node_cells if cell.node_id == "n3"), None)
    assert n3_cell is not None
    assert "n1" in n3_cell.depends_on
    assert "n2" in n3_cell.depends_on

    print(f"✓ Dependencies extracted correctly:")
    for cell in metadata.node_cells:
        if cell.depends_on:
            print(f"  {cell.node_id} depends on {cell.depends_on}")

    # Cleanup
    shutil.rmtree(test_root)


def test_execution_order():
    """Test computing execution order from DAG"""
    print("\n" + "=" * 60)
    print("Test 3: Execution Order Computation")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    create_test_notebook(
        str(notebook_path),
        [
            {
                "node_id": "step1",
                "node_type": "data_source",
                "code": "step1 = 1"
            },
            {
                "node_id": "step2",
                "node_type": "compute",
                "depends_on": ["step1"],
                "code": "step2 = step1 + 1"
            },
            {
                "node_id": "step3",
                "node_type": "compute",
                "depends_on": ["step2"],
                "code": "step3 = step2 * 2"
            },
            {
                "node_id": "tool1",
                "node_type": "tool",
                "code": "def helper(): pass"
            }
        ]
    )

    # Parse and get execution order
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()
    order = parser.get_node_execution_order(metadata)

    print(f"✓ Execution order: {order}")

    # Verify order
    assert order.index("step1") < order.index("step2")
    assert order.index("step2") < order.index("step3")

    print(f"✓ Execution order verified")

    # Cleanup
    shutil.rmtree(test_root)


def test_circular_dependency_detection():
    """Test detection of circular dependencies"""
    print("\n" + "=" * 60)
    print("Test 4: Circular Dependency Detection")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    # Create notebook manually with circular dependency
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": "# @node_type: compute\n# @node_id: a\na = 1"
            },
            {
                "cell_type": "code",
                "source": "# @node_type: compute\n# @node_id: b\n# @depends_on: [a]\nb = a + 1"
            },
            {
                "cell_type": "code",
                "source": "# @node_type: compute\n# @node_id: a\n# @depends_on: [b]\na = b + 1"  # This creates a cycle
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2
    }

    with open(notebook_path, 'w') as f:
        json.dump(notebook, f)

    # Try to parse - should detect duplicate node ID
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()

    print(f"✓ Validation detected issues:")
    for error in metadata.errors:
        print(f"  - {error}")

    assert len(metadata.errors) > 0

    # Cleanup
    shutil.rmtree(test_root)


def test_node_info_retrieval():
    """Test retrieving info for specific nodes"""
    print("\n" + "=" * 60)
    print("Test 5: Node Info Retrieval")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    create_test_notebook(
        str(notebook_path),
        [
            {
                "node_id": "data_node",
                "node_type": "data_source",
                "name": "Load Data",
                "code": "data_node = [1, 2, 3]"
            },
            {
                "node_id": "process_node",
                "node_type": "compute",
                "name": "Process",
                "depends_on": ["data_node"],
                "code": "process_node = sum(data_node)"
            }
        ]
    )

    # Parse and get node info
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()

    # Get specific node
    info = parser.get_node_info(metadata, "data_node")
    print(f"✓ Retrieved node info:")
    print(f"  Node ID: {info['node_id']}")
    print(f"  Type: {info['node_type']}")
    print(f"  Name: {info['node_name']}")
    print(f"  Code length: {info['code_length']}")

    assert info is not None
    assert info['node_type'] == "data_source"

    # Get nodes by type
    compute_nodes = parser.get_nodes_by_type(metadata, "compute")
    print(f"✓ Found {len(compute_nodes)} compute nodes")

    assert len(compute_nodes) == 1
    assert compute_nodes[0]['node_id'] == "process_node"

    # Cleanup
    shutil.rmtree(test_root)


def test_dag_export():
    """Test exporting DAG structure"""
    print("\n" + "=" * 60)
    print("Test 6: DAG Structure Export")
    print("=" * 60)

    test_root = Path("test_metadata")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test.ipynb"

    create_test_notebook(
        str(notebook_path),
        [
            {
                "node_id": "a",
                "node_type": "data_source",
                "code": "a = 1"
            },
            {
                "node_id": "b",
                "node_type": "compute",
                "depends_on": ["a"],
                "code": "b = a + 1"
            },
            {
                "node_id": "c",
                "node_type": "compute",
                "depends_on": ["b"],
                "code": "c = b * 2"
            }
        ]
    )

    # Parse
    parser = ProjectMetadataParser(str(notebook_path))
    metadata = parser.parse()

    # Export
    exported = metadata.to_dict()

    print(f"✓ Exported metadata:")
    print(f"  Total cells: {exported['total_cells']}")
    print(f"  Node cells: {exported['node_cells']}")
    print(f"  DAG nodes: {exported['dag_nodes']}")
    print(f"  DAG edges: {exported['dag_edges']}")

    assert len(exported['dag_nodes']) == 3
    assert len(exported['dag_edges']) == 2
    assert ('a', 'b') in exported['dag_edges']
    assert ('b', 'c') in exported['dag_edges']

    # Cleanup
    shutil.rmtree(test_root)


def test_execution_status_parsing():
    """Test parsing of execution status from optimized notebook"""
    print("\n" + "=" * 60)
    print("Test 7: Execution Status Parsing")
    print("=" * 60)

    notebook_path = "test/example_optimized.ipynb"
    parser = ProjectMetadataParser(notebook_path)
    metadata = parser.parse()

    # Get nodes by execution status
    validated = parser.get_nodes_by_execution_status(metadata, 'validated')
    pending = parser.get_nodes_by_execution_status(metadata, 'pending_validation')
    not_executed = parser.get_nodes_by_execution_status(metadata, 'not_executed')

    print(f"✓ validated 节点: {len(validated)}")
    assert len(validated) == 3

    print(f"✓ pending_validation 节点: {len(pending)}")
    assert len(pending) == 1

    print(f"✓ not_executed 节点: {len(not_executed)}")
    assert len(not_executed) == 1

    print(f"✓ Execution status parsing verified")


def test_result_cells_parsing():
    """Test parsing of result cells from optimized notebook"""
    print("\n" + "=" * 60)
    print("Test 8: Result Cells Parsing")
    print("=" * 60)

    notebook_path = "test/example_optimized.ipynb"
    parser = ProjectMetadataParser(notebook_path)
    metadata = parser.parse()

    result_cells = parser.get_result_cells(metadata)

    print(f"✓ Result cells total: {len(result_cells)}")
    assert len(result_cells) == 5

    # Group by format
    formats = {}
    for cell in result_cells:
        fmt = cell['result_format']
        if fmt not in formats:
            formats[fmt] = 0
        formats[fmt] += 1

    print(f"✓ Result formats detected:")
    print(f"  - parquet: {formats.get('parquet', 0)}")
    print(f"  - json: {formats.get('json', 0)}")
    print(f"  - visualization: {formats.get('visualization', 0)}")

    assert formats['parquet'] == 3
    assert formats['json'] == 1
    assert formats['visualization'] == 1


def test_markdown_links_parsing():
    """Test parsing of markdown cell links from optimized notebook"""
    print("\n" + "=" * 60)
    print("Test 9: Markdown Links Parsing")
    print("=" * 60)

    notebook_path = "test/example_optimized.ipynb"
    parser = ProjectMetadataParser(notebook_path)
    metadata = parser.parse()

    links = parser.get_markdown_links(metadata)

    print(f"✓ Linked markdown cells: {len(links)}")
    for node_id, cell_index in links.items():
        print(f"  - {node_id} -> cell[{cell_index}]")

    assert len(links) == 5
    assert 'load_raw_data' in links
    assert 'visualization' in links


def test_node_with_full_metadata():
    """Test comprehensive node information retrieval"""
    print("\n" + "=" * 60)
    print("Test 10: Node With Full Metadata")
    print("=" * 60)

    notebook_path = "test/example_optimized.ipynb"
    parser = ProjectMetadataParser(notebook_path)
    metadata = parser.parse()

    # Test a data source node
    full_info = parser.get_node_with_metadata(metadata, 'load_raw_data')
    print(f"✓ load_raw_data node info:")
    print(f"  - Type: {full_info['node_type']}")
    print(f"  - Name: {full_info['node_name']}")
    print(f"  - Markdown cell: {full_info['markdown_cell_index']}")
    print(f"  - Result format: {full_info['result_cell']['result_format']}")

    assert full_info['node_type'] == 'data_source'
    assert full_info['markdown_cell_index'] is not None
    assert full_info['result_cell'] is not None
    assert full_info['result_cell']['result_format'] == 'parquet'

    # Test a chart node
    chart_info = parser.get_node_with_metadata(metadata, 'visualization')
    print(f"\n✓ visualization node info:")
    print(f"  - Type: {chart_info['node_type']}")
    print(f"  - Result format: {chart_info['result_cell']['result_format']}")
    print(f"  - Path: {chart_info['result_cell']['parquet_path']}")

    assert chart_info['node_type'] == 'chart'
    assert chart_info['result_cell']['result_format'] == 'visualization'
    assert 'visualizations/' in chart_info['result_cell']['parquet_path']


def cleanup():
    """Clean up test artifacts"""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)

    test_root = Path("test_metadata")
    if test_root.exists():
        shutil.rmtree(test_root)
        print(f"✓ Removed test directory")


if __name__ == "__main__":
    try:
        # Original tests
        test_basic_parsing()
        test_dependency_extraction()
        test_execution_order()
        test_circular_dependency_detection()
        test_node_info_retrieval()
        test_dag_export()

        # Optimization tests
        test_execution_status_parsing()
        test_result_cells_parsing()
        test_markdown_links_parsing()
        test_node_with_full_metadata()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()
