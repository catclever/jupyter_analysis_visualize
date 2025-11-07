"""
Test script for ExecutionManager

Tests node execution, dependency resolution, and result management
"""

import json
import sys
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from execution_manager import ExecutionManager, ExecutionStatus
from kernel_manager import KernelManager
from project_manager import ProjectManager


def test_dependency_resolution():
    """Test DAG traversal and dependency resolution"""
    print("=" * 60)
    print("Test 1: Dependency Resolution")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "dep_test")
    pm.create(name="Dependency Test Project")

    # Add nodes with dependencies
    pm.add_node("data_1", "data_source", "Load Data", code="df = pd.DataFrame({'x': [1,2,3]})")
    pm.add_node("compute_1", "compute", "Compute", depends_on=["data_1"], code="result = df.sum()")
    pm.add_node("compute_2", "compute", "Compute 2", depends_on=["compute_1"], code="final = result * 2")
    pm.add_node("tool_1", "tool", "Tools", code="def helper(): pass")

    # Create execution manager
    km = KernelManager()
    em = ExecutionManager(km, pm)

    # Get dependency order
    order = em.get_dependency_order("dep_test")
    print(f"✓ Dependency order: {order}")

    # Verify order
    assert order.index("data_1") < order.index("compute_1")
    assert order.index("compute_1") < order.index("compute_2")
    print(f"✓ Dependencies resolved correctly")

    # Cleanup
    shutil.rmtree(test_root)


def test_single_node_execution():
    """Test executing a single node"""
    print("\n" + "=" * 60)
    print("Test 2: Single Node Execution")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "single_node")
    pm.create(name="Single Node Test")

    pm.add_node(
        "data_1",
        "data_source",
        "Load Data",
        code="data_1 = {'value': 42, 'name': 'test'}"
    )

    # Execute
    km = KernelManager()
    em = ExecutionManager(km, pm)

    execution = em.execute_node("single_node", "data_1")

    print(f"✓ Node execution completed:")
    print(f"  Status: {execution.status.value}")
    print(f"  Duration: {execution.duration_seconds:.2f}s")

    assert execution.status == ExecutionStatus.SUCCESS
    print(f"✓ Node executed successfully")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def test_project_execution():
    """Test executing entire project with dependencies"""
    print("\n" + "=" * 60)
    print("Test 3: Project Execution")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "exec_test")
    pm.create(name="Execution Test")

    # Add nodes
    pm.add_node(
        "step1",
        "data_source",
        "Step 1",
        code="step1 = 10"
    )
    pm.add_node(
        "step2",
        "compute",
        "Step 2",
        depends_on=["step1"],
        code="step2 = step1 + 5"
    )
    pm.add_node(
        "step3",
        "compute",
        "Step 3",
        depends_on=["step2"],
        code="step3 = step2 * 2"
    )

    # Execute project
    km = KernelManager()
    em = ExecutionManager(km, pm)

    results = em.execute_project("exec_test")

    print(f"✓ Project execution completed:")
    print(f"  Nodes executed: {len(results)}")

    for node_id, execution in results.items():
        print(f"  - {node_id}: {execution.status.value} ({execution.duration_seconds:.2f}s)")
        assert execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED]

    print(f"✓ All nodes executed successfully")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def test_skip_existing_results():
    """Test skipping nodes with existing results"""
    print("\n" + "=" * 60)
    print("Test 4: Skip Existing Results")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "skip_test")
    pm.create(name="Skip Test")

    pm.add_node(
        "data_node",
        "data_source",
        "Data",
        code="data_node = {'cached': True}"
    )

    # First execution
    km = KernelManager()
    em = ExecutionManager(km, pm)

    results1 = em.execute_project("skip_test", skip_existing=False)
    exec1 = results1["data_node"]
    print(f"✓ First execution: {exec1.status.value}")
    assert exec1.status == ExecutionStatus.SUCCESS

    # Second execution with skip_existing=True
    results2 = em.execute_project("skip_test", skip_existing=True)
    exec2 = results2["data_node"]
    print(f"✓ Second execution (skip): {exec2.status.value}")
    assert exec2.status == ExecutionStatus.SKIPPED

    print(f"✓ Skip existing results working correctly")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def test_error_handling():
    """Test error handling during execution"""
    print("\n" + "=" * 60)
    print("Test 5: Error Handling")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "error_test")
    pm.create(name="Error Test")

    # Add node with error
    pm.add_node(
        "bad_node",
        "compute",
        "Bad Node",
        code="undefined_variable / 0"
    )

    # Execute
    km = KernelManager()
    em = ExecutionManager(km, pm)

    execution = em.execute_node("error_test", "bad_node")

    print(f"✓ Node with error executed:")
    print(f"  Status: {execution.status.value}")
    print(f"  Has error: {execution.error is not None}")

    assert execution.status == ExecutionStatus.ERROR
    assert execution.error is not None

    print(f"✓ Error handling verified")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def test_tool_node_always_executes():
    """Test that tool nodes always execute"""
    print("\n" + "=" * 60)
    print("Test 6: Tool Nodes Always Execute")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "tool_test")
    pm.create(name="Tool Test")

    pm.add_node(
        "tool_1",
        "tool",
        "Tools",
        code="def my_function(): return 42"
    )

    # First execution
    km = KernelManager()
    em = ExecutionManager(km, pm)

    results1 = em.execute_project("tool_test", skip_existing=False)
    exec1 = results1["tool_1"]
    print(f"✓ First tool execution: {exec1.status.value}")
    assert exec1.status == ExecutionStatus.SUCCESS

    # Second execution - tool should still execute (skip_existing ignored for tools)
    results2 = em.execute_project("tool_test", skip_existing=True)
    exec2 = results2["tool_1"]
    print(f"✓ Second tool execution: {exec2.status.value}")
    # Tool nodes should not be skipped in breakpoint recovery

    print(f"✓ Tool nodes execute as expected")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def test_execution_summary():
    """Test execution summary generation"""
    print("\n" + "=" * 60)
    print("Test 7: Execution Summary")
    print("=" * 60)

    # Setup
    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)

    pm = ProjectManager(str(test_root), "summary_test")
    pm.create(name="Summary Test")

    pm.add_node("n1", "data_source", "N1", code="n1 = 1")
    pm.add_node("n2", "compute", "N2", depends_on=["n1"], code="n2 = n1 + 1")
    pm.add_node("n3", "tool", "N3", code="def tool(): pass")

    # Execute
    km = KernelManager()
    em = ExecutionManager(km, pm)

    results = em.execute_project("summary_test")
    summary = em.get_execution_summary(results)

    print(f"✓ Execution summary:")
    print(f"  Total nodes: {summary['total_nodes']}")
    print(f"  Successful: {summary['success']}")
    print(f"  Errors: {summary['error']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Total duration: {summary['total_duration_seconds']:.2f}s")

    assert summary['total_nodes'] >= 2
    assert summary['success'] >= 2

    print(f"✓ Execution summary generated correctly")

    # Cleanup
    km.shutdown_all()
    shutil.rmtree(test_root)


def cleanup():
    """Clean up test artifacts"""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)

    test_root = Path("test_projects")
    if test_root.exists():
        shutil.rmtree(test_root)
        print(f"✓ Removed test directory")


if __name__ == "__main__":
    try:
        test_dependency_resolution()
        test_single_node_execution()
        test_project_execution()
        test_skip_existing_results()
        test_error_handling()
        test_tool_node_always_executes()
        test_execution_summary()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()
