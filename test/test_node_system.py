"""
Test script for the new node type system

Tests:
1. Node type registration and discovery
2. Node instantiation and validation
3. Output type inference
4. Integration with ExecutionManager
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.graph_objects as go

from node_types import (
    get_node_type,
    NodeTypeRegistry,
    NodeMetadata,
    OutputType,
    DisplayType,
    ResultFormat
)
from execution_manager import ExecutionManager
from project_manager import ProjectManager


def test_node_type_registration():
    """Test that node types are properly registered"""
    print("\n=== Test 1: Node Type Registration ===")

    registered_types = NodeTypeRegistry.list_types()
    print(f"Registered node types: {registered_types}")

    expected_types = ['data_source', 'compute', 'chart', 'image']
    for node_type in expected_types:
        if NodeTypeRegistry.is_registered(node_type):
            print(f"✓ {node_type} is registered")
        else:
            print(f"✗ {node_type} is NOT registered")
            return False

    return True


def test_data_source_node():
    """Test DataSourceNode creation and validation"""
    print("\n=== Test 2: DataSourceNode ===")

    # Create metadata for a data source node
    metadata = NodeMetadata(
        node_id="test_data",
        node_type="data_source",
        name="Test Data Source",
        depends_on=[]
    )

    # Instantiate the node
    NodeClass = get_node_type('data_source')
    node = NodeClass(metadata)
    print(f"✓ Created DataSourceNode: {node}")

    # Test output inference with DataFrame
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    output = node.infer_output(df)

    print(f"✓ DataFrame inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - display_type: {output.display_type.value}")
    print(f"  - result_format: {output.result_format.value}")
    print(f"  - description: {output.description}")

    assert output.output_type == OutputType.DATAFRAME
    assert output.display_type == DisplayType.TABLE
    assert output.result_format == ResultFormat.PARQUET
    print("✓ Output type is correct")

    return True


def test_compute_node():
    """Test ComputeNode creation and validation"""
    print("\n=== Test 3: ComputeNode ===")

    # Create metadata for a compute node
    metadata = NodeMetadata(
        node_id="test_compute",
        node_type="compute",
        name="Test Compute Node",
        depends_on=["test_data"]
    )

    # Instantiate the node
    NodeClass = get_node_type('compute')
    node = NodeClass(metadata)
    print(f"✓ Created ComputeNode: {node}")

    # Test output inference with DataFrame
    df = pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
    output = node.infer_output(df)

    print(f"✓ DataFrame inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - display_type: {output.display_type.value}")

    assert output.output_type == OutputType.DATAFRAME
    assert output.display_type == DisplayType.TABLE
    print("✓ Output type is correct")

    # Test that compute node rejects dict output
    print("\nTesting dict rejection...")
    try:
        node.infer_output({'key': 'value'})
        print("✗ Compute node should reject dict output!")
        return False
    except TypeError as e:
        print(f"✓ Correctly rejected dict output: {str(e)[:50]}...")

    return True


def test_chart_node():
    """Test ChartNode creation and validation"""
    print("\n=== Test 4: ChartNode ===")

    # Create metadata for a chart node
    metadata = NodeMetadata(
        node_id="test_chart",
        node_type="chart",
        name="Test Chart Node",
        depends_on=["test_compute"]
    )

    # Instantiate the node
    NodeClass = get_node_type('chart')
    node = NodeClass(metadata)
    print(f"✓ Created ChartNode: {node}")

    # Test output inference with Plotly Figure
    fig = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=[1, 2, 3])])
    output = node.infer_output(fig)

    print(f"✓ Plotly Figure inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - display_type: {output.display_type.value}")
    print(f"  - result_format: {output.result_format.value}")

    assert output.output_type == OutputType.PLOTLY
    assert output.display_type == DisplayType.PLOTLY_CHART
    assert output.result_format == ResultFormat.JSON
    print("✓ Output type is correct")

    # Test ECharts configuration
    print("\nTesting ECharts configuration...")
    echarts_config = {
        'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', 'Wed']},
        'yAxis': {'type': 'value'},
        'series': [{'data': [120, 200, 150], 'type': 'line'}]
    }
    output = node.infer_output(echarts_config)

    print(f"✓ ECharts configuration inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - display_type: {output.display_type.value}")
    print(f"  - result_format: {output.result_format.value}")

    assert output.output_type == OutputType.ECHARTS
    assert output.display_type == DisplayType.ECHARTS_CHART
    assert output.result_format == ResultFormat.JSON
    print("✓ Output type is correct")

    return True


def test_image_node():
    """Test ImageNode creation and validation"""
    print("\n=== Test 4b: ImageNode ===")

    # Create metadata for an image node
    metadata = NodeMetadata(
        node_id="test_image",
        node_type="image",
        name="Test Image Node",
        depends_on=["test_compute"]
    )

    # Instantiate the node
    NodeClass = get_node_type('image')
    node = NodeClass(metadata)
    print(f"✓ Created ImageNode: {node}")

    # Test output inference with file path
    image_path = "output/chart.png"
    output = node.infer_output(image_path)

    print(f"✓ Image file path inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - display_type: {output.display_type.value}")
    print(f"  - result_format: {output.result_format.value}")

    assert output.output_type == OutputType.IMAGE
    assert output.display_type == DisplayType.IMAGE_VIEWER
    assert output.result_format == ResultFormat.IMAGE
    print("✓ Output type is correct")

    # Test with JPG file
    print("\nTesting JPG file path...")
    jpg_path = "results/chart.jpg"
    output = node.infer_output(jpg_path)

    print(f"✓ JPG file inference:")
    print(f"  - output_type: {output.output_type.value}")
    print(f"  - result_format: {output.result_format.value}")

    assert output.output_type == OutputType.IMAGE
    assert output.result_format == ResultFormat.IMAGE
    print("✓ JPG output type is correct")

    return True


def test_execution_manager_integration():
    """Test integration with ExecutionManager"""
    print("\n=== Test 5: ExecutionManager Integration ===")

    projects_root = Path(__file__).parent.parent.parent / "projects"

    # Test with actual project
    pm = ProjectManager(str(projects_root), "test_sales_performance_report")
    if not pm.exists():
        print("✗ Test project not found")
        return False

    pm.load()
    print(f"✓ Loaded project: {pm.project_id}")

    # Create execution manager
    em = ExecutionManager(str(projects_root), pm)

    # Test output type inference on sales_data node
    print("\nTesting infer_output_type method...")
    test_df = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02'],
        'product': ['A', 'B'],
        'region': ['North', 'South'],
        'amount': [100, 200]
    })

    try:
        output = em.infer_output_type("sales_data", test_df)
        print(f"✓ Inferred output type for sales_data:")
        print(f"  - output_type: {output.output_type.value}")
        print(f"  - display_type: {output.display_type.value}")
        assert output.output_type == OutputType.DATAFRAME
        print("✓ Output type inference works correctly")
    except Exception as e:
        print(f"✗ Error inferring output type: {e}")
        return False

    # Test chart node with Plotly
    print("\nTesting chart node inference...")
    fig = go.Figure(data=[go.Bar(x=['North', 'South'], y=[300, 400])])
    try:
        output = em.infer_output_type("visualization", fig)
        print(f"✓ Inferred output type for visualization:")
        print(f"  - output_type: {output.output_type.value}")
        print(f"  - display_type: {output.display_type.value}")
        assert output.output_type == OutputType.PLOTLY
        print("✓ Plotly inference works correctly")
    except Exception as e:
        print(f"✗ Error inferring output type: {e}")
        return False

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Node Type System Tests")
    print("=" * 60)

    tests = [
        ("Node Type Registration", test_node_type_registration),
        ("DataSourceNode", test_data_source_node),
        ("ComputeNode", test_compute_node),
        ("ChartNode", test_chart_node),
        ("ImageNode", test_image_node),
        ("ExecutionManager Integration", test_execution_manager_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
