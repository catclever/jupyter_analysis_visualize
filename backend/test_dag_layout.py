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
    """Test that nodes are layered correctly"""
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

    # Compute nodes should be in layer 1
    assert positions['compute1']['x'] == 300, "Compute nodes should be at layer 1 (x=300)"
    assert positions['compute2']['x'] == 300, "Compute nodes should be at layer 1 (x=300)"

    # Chart should be in layer 2
    assert positions['chart']['x'] == 600, "Chart node should be at layer 2 (x=600)"

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
    """Test special positioning for layer 0 nodes with single child"""
    nodes = [
        {'id': 'source', 'type': 'data_source', 'first_execution_time': None},
        {'id': 'compute', 'type': 'compute', 'first_execution_time': None},
    ]
    edges = [('source', 'compute')]

    positions = calculate_node_positions(nodes, edges)

    # Source should be moved to left-bottom of compute
    compute_x = positions['compute']['x']
    source_x = positions['source']['x']

    # Source x should be less than compute x (moved left)
    assert source_x < compute_x, "Single child positioning: source should be left of compute"

    print("✓ Single child positioning test passed")


def test_single_parent_positioning():
    """Test special positioning for leaf nodes with single parent"""
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

    # Chart should be positioned to the right-top of compute2
    compute2_x = positions['compute2']['x']
    chart_x = positions['chart']['x']

    # Chart x should be greater than compute2 x (moved right)
    assert chart_x > compute2_x, "Single parent positioning: chart should be right of compute2"

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
