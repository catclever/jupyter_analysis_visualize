#!/usr/bin/env python3
"""
Test script for DAG layout algorithm
"""

import json
from dag_layout import DAGLayout, calculate_node_positions


def test_tool_node_positioning():
    """Test that tool nodes are positioned at the top"""
    nodes = [
        {'id': 'tool1', 'type': 'tool', 'first_execution_time': '2024-01-01T10:00:00'},
        {'id': 'tool2', 'type': 'tool', 'first_execution_time': '2024-01-01T09:00:00'},
        {'id': 'data_1', 'type': 'data_source', 'first_execution_time': None},
    ]
    edges = [('tool1', 'data_1'), ('tool2', 'data_1')]

    positions = calculate_node_positions(nodes, edges)

    # Tool nodes should have negative y positions
    assert positions['tool1']['y'] < 0, "Tool nodes should have negative y"
    assert positions['tool2']['y'] < 0, "Tool nodes should have negative y"

    # Tool2 should come before tool1 (sorted by execution time)
    assert positions['tool2']['x'] < positions['tool1']['x'], "Nodes should be sorted by execution time"

    # Data source node should have positive or zero y
    assert positions['data_1']['y'] >= 0, "Non-tool nodes should have non-negative y"

    print("✓ Tool node positioning test passed")


def test_hierarchical_layering():
    """Test that nodes are layered correctly (left to right with LAYER_SPACING=100)"""
    nodes = [
        {'id': 'source', 'type': 'data_source', 'first_execution_time': None},
        {'id': 'compute1', 'type': 'compute', 'first_execution_time': None},
        {'id': 'compute2', 'type': 'compute', 'first_execution_time': None},
        {'id': 'chart', 'type': 'chart', 'first_execution_time': None},
    ]
    edges = [
        ('source', 'compute1'),
        ('source', 'compute2'),
        ('compute1', 'chart'),
        ('compute2', 'chart'),
    ]

    positions = calculate_node_positions(nodes, edges)

    # Source should be in layer 0 (leftmost)
    assert positions['source']['x'] == 0, "Source node should be at x=0"

    # Compute nodes should be in layer 1 (x = 0 + LAYER_SPACING = 100)
    assert positions['compute1']['x'] == 100, "Compute nodes should be at layer 1 (x=100)"
    assert positions['compute2']['x'] == 100, "Compute nodes should be at layer 1 (x=100)"

    # Chart should be in layer 2 (x = 100 + LAYER_SPACING = 200)
    assert positions['chart']['x'] == 200, "Chart node should be at layer 2 (x=200)"

    print("✓ Hierarchical layering test passed")


def test_execution_time_sorting():
    """Test that nodes are sorted by execution time within layers"""
    nodes = [
        {'id': 'source', 'type': 'data_source', 'first_execution_time': None},
        {'id': 'compute1', 'type': 'compute', 'first_execution_time': '2024-01-01T10:00:00'},
        {'id': 'compute2', 'type': 'compute', 'first_execution_time': '2024-01-01T09:00:00'},
        {'id': 'compute3', 'type': 'compute', 'first_execution_time': None},
    ]
    edges = [
        ('source', 'compute1'),
        ('source', 'compute2'),
        ('source', 'compute3'),
    ]

    positions = calculate_node_positions(nodes, edges)

    # Executed nodes should come before unexecuted
    # compute2 (9:00) should come before compute1 (10:00)
    # compute3 (unexecuted) should come last
    y_compute2 = positions['compute2']['y']
    y_compute1 = positions['compute1']['y']
    y_compute3 = positions['compute3']['y']

    assert y_compute2 < y_compute1, "compute2 should be above compute1 (earlier execution time)"
    assert y_compute1 < y_compute3, "Executed nodes should be above unexecuted"

    print("✓ Execution time sorting test passed")


def test_single_child_positioning():
    """Test special positioning for layer 0 nodes with single child (parent moves to left-top of child)"""
    nodes = [
        {'id': 'source', 'type': 'data_source', 'first_execution_time': None},
        {'id': 'compute', 'type': 'compute', 'first_execution_time': None},
    ]
    edges = [('source', 'compute')]

    positions = calculate_node_positions(nodes, edges)

    # Source should be moved to left-top of compute (SPECIAL_OFFSET = 20)
    compute_x = positions['compute']['x']
    compute_y = positions['compute']['y']
    source_x = positions['source']['x']
    source_y = positions['source']['y']

    # Source should be offset by SPECIAL_OFFSET (20) to the left and up
    assert source_x == compute_x - 20, f"Source x should be {compute_x - 20}, got {source_x}"
    assert source_y == compute_y - 20, f"Source y should be {compute_y - 20}, got {source_y}"

    print("✓ Single child positioning test passed")


def test_single_parent_positioning():
    """Test special positioning for leaf nodes with single parent (child moves to right-bottom of parent)"""
    nodes = [
        {'id': 'compute1', 'type': 'compute', 'first_execution_time': None},
        {'id': 'compute2', 'type': 'compute', 'first_execution_time': None},
        {'id': 'chart', 'type': 'chart', 'first_execution_time': None},
    ]
    edges = [
        ('compute1', 'compute2'),
        ('compute2', 'chart'),
    ]

    positions = calculate_node_positions(nodes, edges)

    # Chart should be positioned to the right-bottom of compute2 (SPECIAL_OFFSET = 20)
    compute2_x = positions['compute2']['x']
    compute2_y = positions['compute2']['y']
    chart_x = positions['chart']['x']
    chart_y = positions['chart']['y']

    # Chart should be offset by SPECIAL_OFFSET (20) to the right and down
    assert chart_x == compute2_x + 20, f"Chart x should be {compute2_x + 20}, got {chart_x}"
    assert chart_y == compute2_y + 20, f"Chart y should be {compute2_y + 20}, got {chart_y}"

    print("✓ Single parent positioning test passed")


if __name__ == '__main__':
    print("Testing DAG layout algorithm...\n")

    try:
        test_tool_node_positioning()
        test_hierarchical_layering()
        test_execution_time_sorting()
        test_single_child_positioning()
        test_single_parent_positioning()

        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
