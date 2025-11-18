"""
Diagnostic Script: Check Node Type Synchronization

This script helps identify and fix mismatches between:
1. Frontend node types (from notebook cell metadata comments)
2. Backend node types (from project.json)

It also helps fix metadata if there are synchronization issues.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def read_project_metadata(project_dir: str) -> Dict:
    """Read project.json metadata"""
    project_json = Path(project_dir) / 'project.json'
    if not project_json.exists():
        print(f"ERROR: project.json not found at {project_json}")
        return {}

    with open(project_json, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_node_types(project_dir: str):
    """
    Check node types in project.json and report any mismatches.

    Usage:
        python diagnose_node_types.py /path/to/project/directory
    """
    project_dir = Path(project_dir)

    print(f"\n{'='*60}")
    print("Tool Node Diagnostic Report")
    print(f"{'='*60}\n")

    print(f"Project Directory: {project_dir}")

    # Read metadata
    metadata = read_project_metadata(str(project_dir))
    if not metadata:
        return

    nodes = metadata.get('nodes', [])
    print(f"Total nodes found: {len(nodes)}\n")

    # Analyze node types
    tool_nodes = []
    compute_nodes = []
    data_source_nodes = []
    chart_nodes = []
    unknown_nodes = []

    for node in nodes:
        node_id = node.get('node_id', 'UNKNOWN')
        node_type = node.get('type', 'unknown')

        print(f"  Node: {node_id:20s} | Type: {node_type:15s}")

        if node_type == 'tool':
            tool_nodes.append(node_id)
        elif node_type == 'compute':
            compute_nodes.append(node_id)
        elif node_type == 'data_source':
            data_source_nodes.append(node_id)
        elif node_type == 'chart':
            chart_nodes.append(node_id)
        else:
            unknown_nodes.append((node_id, node_type))

    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    print(f"  Tool Nodes:       {len(tool_nodes)}")
    print(f"  Compute Nodes:    {len(compute_nodes)}")
    print(f"  Data Source Nodes: {len(data_source_nodes)}")
    print(f"  Chart Nodes:      {len(chart_nodes)}")
    print(f"  Unknown Types:    {len(unknown_nodes)}")

    if unknown_nodes:
        print(f"\n  Unknown node types found:")
        for node_id, node_type in unknown_nodes:
            print(f"    - {node_id}: '{node_type}'")

    # Check if preprocess_df exists
    print(f"\n{'='*60}")
    print("Specific Node Check: 'preprocess_df'")
    print(f"{'='*60}")

    preprocess_df = next((n for n in nodes if n.get('node_id') == 'preprocess_df'), None)
    if preprocess_df:
        print(f"✓ Node 'preprocess_df' found!")
        print(f"  Type in project.json: '{preprocess_df.get('type', 'MISSING')}'")
        print(f"  Result Format: '{preprocess_df.get('result_format', 'MISSING')}'")
        print(f"  Dependencies: {preprocess_df.get('depends_on', [])}")

        if preprocess_df.get('type') != 'tool':
            print(f"\n  ⚠ WARNING: preprocess_df is marked as '{preprocess_df.get('type')}' but should be 'tool'!")
            print(f"  This will cause validation error: 'Code must assign variable preprocess_df'")
    else:
        print(f"✗ Node 'preprocess_df' NOT found in project.json")
        print(f"  Available nodes: {[n.get('node_id') for n in nodes]}")

    print(f"\n{'='*60}\n")

def fix_node_type(project_dir: str, node_id: str, new_type: str):
    """
    Fix a node's type in project.json

    Usage:
        python diagnose_node_types.py --fix /path/to/project node_id new_type
        python diagnose_node_types.py --fix /path/to/project preprocess_df tool
    """
    project_dir = Path(project_dir)
    project_json = project_dir / 'project.json'

    if not project_json.exists():
        print(f"ERROR: project.json not found at {project_json}")
        return False

    with open(project_json, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Find and fix the node
    nodes = metadata.get('nodes', [])
    node_found = False

    for node in nodes:
        if node.get('node_id') == node_id:
            old_type = node.get('type')
            node['type'] = new_type
            node_found = True

            # Also update result_format if switching to/from tool
            if new_type == 'tool':
                node['result_format'] = 'pkl'
            elif old_type == 'tool':
                node['result_format'] = 'parquet'  # Default for non-tool nodes

            print(f"✓ Updated {node_id}: '{old_type}' → '{new_type}'")
            break

    if not node_found:
        print(f"✗ Node '{node_id}' not found in project.json")
        return False

    # Save the updated metadata
    with open(project_json, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved updated project.json")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python diagnose_node_types.py /path/to/project              # Check node types")
        print("  python diagnose_node_types.py --fix /path/to/project node_id new_type  # Fix a node type")
        print("\nExample:")
        print("  python diagnose_node_types.py C:\\path\\to\\project")
        print("  python diagnose_node_types.py --fix C:\\path\\to\\project preprocess_df tool")
        sys.exit(1)

    if sys.argv[1] == '--fix':
        if len(sys.argv) < 4:
            print("ERROR: --fix requires 2 arguments: node_id and new_type")
            sys.exit(1)
        project_dir = sys.argv[2]
        node_id = sys.argv[3]
        new_type = sys.argv[4] if len(sys.argv) > 4 else 'tool'
        fix_node_type(project_dir, node_id, new_type)
    else:
        project_dir = sys.argv[1]
        check_node_types(project_dir)
