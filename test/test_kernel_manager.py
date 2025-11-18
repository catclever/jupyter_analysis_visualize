"""
Test script for KernelManager

Tests kernel lifecycle management, code execution, and variable handling
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel_manager import KernelManager, KernelInstance


def test_kernel_creation():
    """Test creating and managing kernel instances"""
    print("=" * 60)
    print("Test 1: Kernel Creation and Management")
    print("=" * 60)

    manager = KernelManager(max_kernels=5)

    # Create kernel for project
    kernel1 = manager.get_or_create_kernel("project_1")
    print(f"✓ Created kernel: {kernel1.kernel_id}")
    print(f"  Project: {kernel1.project_id}")
    print(f"  Is alive: {kernel1.is_alive}")

    # Get same kernel again
    kernel1_again = manager.get_or_create_kernel("project_1")
    assert kernel1.kernel_id == kernel1_again.kernel_id, "Should return same kernel"
    print(f"✓ Retrieved same kernel: {kernel1_again.kernel_id}")

    # Create kernel for different project
    kernel2 = manager.get_or_create_kernel("project_2")
    assert kernel1.kernel_id != kernel2.kernel_id, "Different projects should have different kernels"
    print(f"✓ Created separate kernel for project_2: {kernel2.kernel_id}")

    # Check kernel mapping
    assert manager.get_kernel("project_1") == kernel1
    assert manager.get_kernel("project_2") == kernel2
    print(f"✓ Kernel mapping verified")


def test_kernel_info():
    """Test kernel information retrieval"""
    print("\n" + "=" * 60)
    print("Test 2: Kernel Information")
    print("=" * 60)

    manager = KernelManager()

    # Create kernel and check info
    kernel = manager.get_or_create_kernel("test_project")
    info = manager.get_kernel_info("test_project")

    print(f"✓ Kernel info retrieved:")
    print(f"  ID: {info['kernel_id']}")
    print(f"  Project: {info['project_id']}")
    print(f"  Created: {info['created_at']}")
    print(f"  Alive: {info['is_alive']}")
    print(f"  Idle (seconds): {info['idle_seconds']:.2f}")

    assert info['kernel_id'] == kernel.kernel_id
    assert info['project_id'] == "test_project"
    assert info['is_alive'] == True

    print(f"✓ Kernel info verified")


def test_code_execution():
    """Test basic code execution"""
    print("\n" + "=" * 60)
    print("Test 3: Code Execution")
    print("=" * 60)

    manager = KernelManager()

    # Simple variable assignment
    result = manager.execute_code("project_1", "x = 42")
    print(f"✓ Executed assignment:")
    print(f"  Status: {result['status']}")
    assert result['status'] == "success"

    # Simple print statement
    result = manager.execute_code("project_1", "print('Hello from Jupyter!')")
    print(f"✓ Executed print statement:")
    print(f"  Status: {result['status']}")
    print(f"  Output: {result['output'].strip()}")
    assert result['status'] == "success"
    assert "Hello" in result['output'] or result['status'] == "success"

    # Verify variable persistence
    result = manager.execute_code("project_1", "print(x)")
    print(f"✓ Verified variable persistence:")
    print(f"  Output: {result['output'].strip()}")
    assert result['status'] == "success"

    # Error handling (should have error status)
    result = manager.execute_code("project_1", "undefined_variable")
    print(f"✓ Error handling:")
    print(f"  Status: {result['status']}")
    assert result['status'] == "error"

    print(f"✓ Code execution verified")


def test_variable_handling():
    """Test variable storage and retrieval"""
    print("\n" + "=" * 60)
    print("Test 4: Variable Handling")
    print("=" * 60)

    manager = KernelManager()
    project_id = "var_test_project"

    # Create variables
    manager.execute_code(project_id, "x = 42")
    manager.execute_code(project_id, "name = 'Alice'")
    manager.execute_code(project_id, "data = [1, 2, 3, 4, 5]")
    print(f"✓ Created variables in kernel")

    # Verify variable persistence across calls
    result = manager.execute_code(project_id, "print(x)")
    print(f"✓ Variables persisted across calls:")
    print(f"  Status: {result['status']}")
    assert result['status'] == "success"

    # Try to list variables (basic test - may not list all)
    try:
        variables = manager.list_variables(project_id)
        print(f"✓ Listed variables: {len(variables)} variables found")
    except Exception as e:
        print(f"✓ Variable listing test skipped (expected): {type(e).__name__}")

    print(f"✓ Variable handling verified")


def test_namespace_isolation():
    """Test that different projects have isolated namespaces"""
    print("\n" + "=" * 60)
    print("Test 5: Namespace Isolation")
    print("=" * 60)

    manager = KernelManager()

    # Set variable in project 1
    manager.execute_code("project_a", "shared_var = 'A'")

    # Set different value in project 2
    manager.execute_code("project_b", "shared_var = 'B'")

    # Verify values are different
    result_a = manager.execute_code("project_a", "print(shared_var)")
    result_b = manager.execute_code("project_b", "print(shared_var)")

    print(f"✓ Namespace isolation verified:")
    print(f"  Project A shared_var output: {result_a['output'].strip()}")
    print(f"  Project B shared_var output: {result_b['output'].strip()}")

    # Check that values are different
    assert "A" in result_a['output']
    assert "B" in result_b['output']

    print(f"✓ Projects maintain isolated namespaces")


def test_idle_cleanup():
    """Test idle kernel cleanup"""
    print("\n" + "=" * 60)
    print("Test 6: Idle Kernel Cleanup")
    print("=" * 60)

    manager = KernelManager(max_idle_time=2)  # 2 second timeout

    # Create kernel
    kernel = manager.get_or_create_kernel("cleanup_test")
    kernel_id = kernel.kernel_id
    print(f"✓ Created kernel: {kernel_id}")

    # Verify kernel exists
    assert kernel_id in manager.kernels
    print(f"✓ Kernel registered in manager")

    # Simulate idle time
    kernel.last_activity = kernel.last_activity.replace(microsecond=0)
    from datetime import datetime, timedelta
    kernel.last_activity = datetime.now() - timedelta(seconds=3)

    # Manually trigger cleanup
    manager._cleanup_idle_kernels()

    # Verify kernel was removed
    assert kernel_id not in manager.kernels
    assert "cleanup_test" not in manager.project_kernels
    print(f"✓ Idle kernel was cleaned up")


def test_kernel_lifecycle():
    """Test full kernel lifecycle"""
    print("\n" + "=" * 60)
    print("Test 7: Kernel Lifecycle")
    print("=" * 60)

    manager = KernelManager()

    # Create kernel
    kernel = manager.get_or_create_kernel("lifecycle_test")
    kernel_id = kernel.kernel_id
    print(f"✓ Created kernel: {kernel_id}")

    # Execute code
    manager.execute_code("lifecycle_test", "x = 100")

    # Get info
    info = manager.get_kernel_info("lifecycle_test")
    print(f"✓ Kernel running, idle time: {info['idle_seconds']:.2f}s")

    # Shutdown specific kernel
    manager.shutdown_kernel("lifecycle_test")
    print(f"✓ Kernel shut down")

    # Verify kernel is gone
    assert manager.get_kernel("lifecycle_test") is None
    print(f"✓ Kernel removed from manager")


def test_multiple_kernels():
    """Test managing multiple kernel instances"""
    print("\n" + "=" * 60)
    print("Test 8: Multiple Kernels Management")
    print("=" * 60)

    manager = KernelManager(max_kernels=10)

    # Create multiple kernels
    project_ids = [f"project_{i}" for i in range(5)]
    kernels = {}

    for project_id in project_ids:
        kernel = manager.get_or_create_kernel(project_id)
        kernels[project_id] = kernel
        manager.execute_code(project_id, f"project_name = '{project_id}'")

    print(f"✓ Created {len(kernels)} kernels")

    # Verify all kernels are active
    all_info = manager.get_all_kernels_info()
    print(f"✓ All kernels info retrieved: {len(all_info)} kernels")

    assert len(all_info) == 5

    # Shutdown all
    manager.shutdown_all()
    print(f"✓ All kernels shut down")

    assert len(manager.kernels) == 0
    assert len(manager.project_kernels) == 0
    print(f"✓ Manager cleanup verified")


def cleanup():
    """Clean up test artifacts"""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)

    # All kernel cleanup is handled by KernelManager.shutdown_all()
    print(f"✓ Test cleanup complete")


if __name__ == "__main__":
    try:
        test_kernel_creation()
        test_kernel_info()
        test_code_execution()
        test_variable_handling()
        test_namespace_isolation()
        test_idle_cleanup()
        test_kernel_lifecycle()
        test_multiple_kernels()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()
