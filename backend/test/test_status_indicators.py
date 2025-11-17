#!/usr/bin/env python3
"""
Test script to verify that status indicators work correctly in the frontend.
"""

import json
from pathlib import Path


def test_status_indicators_in_project_json():
    """Verify that execution_status field exists and is correct"""

    project_path = Path(__file__).parent.parent.parent / "projects" / "ecommerce_analytics"
    project_json = project_path / "project.json"

    print("=" * 80)
    print("TESTING STATUS INDICATORS")
    print("=" * 80)

    # Load project data
    with open(project_json) as f:
        project_data = json.load(f)

    nodes = project_data.get('nodes', {})
    print(f"\n✓ Project has {len(nodes)} nodes\n")

    # Check each node has execution_status
    status_distribution = {}
    all_valid = True

    for node_id, node in nodes.items():
        status = node.get('execution_status', 'MISSING')
        if status not in ['validated', 'pending_validation', 'not_executed']:
            all_valid = False
            print(f"✗ Node '{node_id}': Invalid status '{status}'")

        status_distribution[status] = status_distribution.get(status, 0) + 1

    print("Status Distribution:")
    for status, count in sorted(status_distribution.items()):
        print(f"  • {status:25} : {count:3} nodes")

    # Show example data for frontend
    print("\n" + "=" * 80)
    print("EXAMPLE DATA FORMAT FOR FRONTEND")
    print("=" * 80)

    sample_node_id = list(nodes.keys())[0]
    sample_node = nodes[sample_node_id]

    frontend_data = {
        "id": sample_node['node_id'],
        "label": sample_node.get('name', 'Unknown'),
        "type": sample_node.get('node_type', 'unknown'),
        "execution_status": sample_node.get('execution_status', 'not_executed'),
        "error_message": sample_node.get('error_message'),
        "depends_on": sample_node.get('depends_on', [])
    }

    print(f"\nSample node: {sample_node_id}")
    print(json.dumps(frontend_data, indent=2))

    # Show what CSS class would be applied
    status = frontend_data['execution_status']
    css_classes = f"flow-node-{frontend_data['type']} status-{status}"
    print(f"\nCSS class applied: {css_classes}")
    print(f"Expected visual: ", end="")

    if status == 'validated':
        print("🟢 Green border (#22c55e) - Node executed successfully")
    elif status == 'pending_validation':
        print("🔴 Red border (#ef4444) - Node execution failed")
    elif status == 'not_executed':
        print("⚪ Gray border (#999999) - Node not yet executed")

    # Test all nodes have the structure
    print("\n" + "=" * 80)
    print("STATUS INDICATOR IMPLEMENTATION CHECKLIST")
    print("=" * 80)

    checks = {
        "Project has 'nodes' object": 'nodes' in project_data,
        "All nodes have 'node_id'": all('node_id' in n for n in nodes.values()),
        "All nodes have 'node_type'": all('node_type' in n for n in nodes.values()),
        "All nodes have 'execution_status'": all('execution_status' in n for n in nodes.values()),
        "execution_status values are valid": all(
            n.get('execution_status') in ['validated', 'pending_validation', 'not_executed']
            for n in nodes.values()
        ),
        "All nodes have 'depends_on'": all('depends_on' in n for n in nodes.values()),
        "All nodes have 'result_format'": all('result_format' in n for n in nodes.values()),
    }

    for check, passed in checks.items():
        status_icon = "✓" if passed else "✗"
        print(f"  [{status_icon}] {check}")

    all_passed = all(checks.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Status indicators are properly configured!")
        print("\nFrontend will display nodes with:")
        print("  🟢 GREEN border  - for validated nodes")
        print("  🔴 RED border    - for nodes with errors")
        print("  ⚪ GRAY border   - for not yet executed nodes")
    else:
        print("✗ SOME CHECKS FAILED - Please review the errors above")

    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = test_status_indicators_in_project_json()
    exit(0 if success else 1)
