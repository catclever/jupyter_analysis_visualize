"""
Test NotebookManager

Test content:
1. Markdown cell association with nodes
2. Execution status tracking
3. Result cell generation
"""

import json
import sys
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from notebook_manager import NotebookManager, ExecutionStatus


def test_markdown_linked_to_node():
    """Test markdown cell association with nodes"""
    print("=" * 70)
    print("Test 1: Markdown Cell 关联到节点")
    print("=" * 70)

    test_root = Path("test_notebooks")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test_linked.ipynb"
    manager = NotebookManager(str(notebook_path))

    # Add markdown cell linked to node
    md_idx = manager.append_markdown_cell(
        "## 数据加载\n这个部分负责从 CSV 文件加载用户数据",
        linked_node_id="data_1"
    )
    print(f"✓ 添加关联 markdown cell (index: {md_idx})")

    # Add corresponding code node
    code_idx = manager.append_code_cell(
        code="df = pd.read_csv('users.csv')\ndata_1 = df",
        node_type="data_source",
        node_id="data_1",
        name="加载用户数据"
    )
    print(f"✓ 添加代码节点 (index: {code_idx})")

    # Save and verify
    manager.save()

    # Read and verify metadata
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    md_cell = nb['cells'][md_idx]
    code_cell = nb['cells'][code_idx]

    print(f"\n✓ Markdown cell 元数据:")
    print(f"  - linked_node_id: {md_cell['metadata'].get('linked_node_id')}")
    print(f"  - cell_type: {md_cell['cell_type']}")

    print(f"\n✓ Code cell 元数据:")
    print(f"  - node_id: {code_cell['metadata'].get('node_id')}")
    print(f"  - node_type: {code_cell['metadata'].get('node_type')}")
    print(f"  - execution_status: {code_cell['metadata'].get('execution_status')}")

    # Verify query functionality
    linked_md = manager.find_markdown_cells_by_linked_node("data_1")
    assert len(linked_md) == 1
    print(f"\n✓ 通过 node_id 查询关联的 markdown cell 成功")

    # Cleanup
    shutil.rmtree(test_root)
    print()


def test_execution_status_tracking():
    """Test execution status tracking"""
    print("=" * 70)
    print("Test 2: 执行状态记录和更新")
    print("=" * 70)

    test_root = Path("test_notebooks")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test_status.ipynb"
    manager = NotebookManager(str(notebook_path))

    # Add three nodes with different statuses
    manager.append_code_cell(
        code="data = [1, 2, 3]",
        node_type="data_source",
        node_id="node_1",
        execution_status=ExecutionStatus.VALIDATED.value
    )
    print("✓ 添加 node_1 (状态: validated)")

    manager.append_code_cell(
        code="result = sum(data)",
        node_type="compute",
        node_id="node_2",
        depends_on=["node_1"],
        execution_status=ExecutionStatus.PENDING_VALIDATION.value
    )
    print("✓ 添加 node_2 (状态: pending_validation)")

    manager.append_code_cell(
        code="chart = plot(result)",
        node_type="chart",
        node_id="node_3",
        depends_on=["node_2"]
    )
    print("✓ 添加 node_3 (状态: not_executed)")

    # Save
    manager.save()

    # Verify initial status
    print(f"\n✓ 初始状态检查:")
    validated = manager.list_cells_by_status(ExecutionStatus.VALIDATED.value)
    pending = manager.list_cells_by_status(ExecutionStatus.PENDING_VALIDATION.value)
    not_exec = manager.list_cells_by_status(ExecutionStatus.NOT_EXECUTED.value)

    print(f"  - validated: {len(validated)} 个节点")
    print(f"  - pending_validation: {len(pending)} 个节点")
    print(f"  - not_executed: {len(not_exec)} 个节点")

    # Update status
    manager.update_execution_status("node_2", ExecutionStatus.VALIDATED.value)
    print(f"\n✓ 更新 node_2 状态为 validated")

    manager.update_execution_status("node_3", ExecutionStatus.PENDING_VALIDATION.value)
    print(f"✓ 更新 node_3 状态为 pending_validation")

    manager.save()

    # Verify again
    validated = manager.list_cells_by_status(ExecutionStatus.VALIDATED.value)
    pending = manager.list_cells_by_status(ExecutionStatus.PENDING_VALIDATION.value)

    print(f"\n✓ 更新后的状态:")
    print(f"  - validated: {len(validated)} 个节点")
    print(f"  - pending_validation: {len(pending)} 个节点")

    assert len(validated) == 2
    assert len(pending) == 1

    # Cleanup
    shutil.rmtree(test_root)
    print()


def test_result_cells():
    """Test result cell generation"""
    print("=" * 70)
    print("Test 3: 结果 Cell 生成和关联")
    print("=" * 70)

    test_root = Path("test_notebooks")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test_results.ipynb"
    manager = NotebookManager(str(notebook_path))

    # Add data node
    manager.append_code_cell(
        code="df = pd.read_csv('data.csv')\ndata_1 = df",
        node_type="data_source",
        node_id="data_1",
        execution_status=ExecutionStatus.VALIDATED.value
    )
    print("✓ 添加数据节点 data_1")

    # Add result cell
    result_idx = manager.append_result_cell(
        node_id="data_1",
        parquet_path="/path/to/results/data_1.parquet",
        result_format="parquet"
    )
    print(f"✓ 添加结果 cell (index: {result_idx})")

    # Add compute node
    manager.append_code_cell(
        code="result = data_1.sum()",
        node_type="compute",
        node_id="compute_1",
        depends_on=["data_1"],
        execution_status=ExecutionStatus.VALIDATED.value
    )
    print("✓ 添加计算节点 compute_1")

    # Add computation result
    result_idx2 = manager.append_result_cell(
        node_id="compute_1",
        parquet_path="/path/to/results/compute_1.parquet"
    )
    print(f"✓ 添加计算结果 cell (index: {result_idx2})")

    manager.save()

    # Verify structure
    print(f"\n✓ 验证结构:")
    node_info = manager.get_node_with_results("data_1")
    print(f"  - data_1 有结果: {node_info['has_results']}")
    print(f"  - 结果 cell 数量: {len(node_info['results'])}")

    node_info2 = manager.get_node_with_results("compute_1")
    print(f"  - compute_1 有结果: {node_info2['has_results']}")
    print(f"  - 结果 cell 数量: {len(node_info2['results'])}")

    # Read notebook to see generated code
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    result_cell = nb['cells'][result_idx]
    print(f"\n✓ 生成的结果 cell 代码:")
    code_lines = result_cell['source']
    for line in code_lines[:5]:
        print(f"    {line.rstrip()}")

    # Cleanup
    shutil.rmtree(test_root)
    print()


def test_complete_workflow():
    """Test complete workflow"""
    print("=" * 70)
    print("Test 4: 完整工作流 (描述+代码+结果)")
    print("=" * 70)

    test_root = Path("test_notebooks")
    test_root.mkdir(exist_ok=True)

    notebook_path = test_root / "test_complete.ipynb"
    manager = NotebookManager(str(notebook_path))

    # Add project title
    manager.append_markdown_cell("# 数据分析项目")

    # ===== Stage 1 =====
    manager.append_markdown_cell(
        "## 阶段 1: 数据加载\n加载源数据文件",
        linked_node_id="load_data"
    )

    manager.append_code_cell(
        code="import pandas as pd\ndf = pd.read_csv('users.csv')\nload_data = df",
        node_type="data_source",
        node_id="load_data",
        name="加载用户数据",
        execution_status=ExecutionStatus.VALIDATED.value
    )

    manager.append_result_cell(
        node_id="load_data",
        parquet_path="results/load_data.parquet"
    )

    # ===== Stage 2 =====
    manager.append_markdown_cell(
        "## 阶段 2: 数据处理\n清理和转换数据",
        linked_node_id="process_data"
    )

    manager.append_code_cell(
        code="cleaned_df = load_data.dropna()\nprocess_data = cleaned_df",
        node_type="compute",
        node_id="process_data",
        depends_on=["load_data"],
        name="数据清理",
        execution_status=ExecutionStatus.VALIDATED.value
    )

    manager.append_result_cell(
        node_id="process_data",
        parquet_path="results/process_data.parquet"
    )

    # ===== Stage 3 =====
    manager.append_markdown_cell(
        "## 阶段 3: 可视化\n生成数据可视化图表",
        linked_node_id="plot_data"
    )

    manager.append_code_cell(
        code="import plotly.express as px\nfig = px.bar(process_data)\nplot_data = fig",
        node_type="chart",
        node_id="plot_data",
        depends_on=["process_data"],
        name="柱状图",
        execution_status=ExecutionStatus.PENDING_VALIDATION.value
    )

    manager.save()

    # Statistics
    print(f"\n✓ 生成的 notebook 统计:")
    all_cells = manager.get_cells()
    code_cells = manager.list_code_cells()
    node_cells = manager.list_node_cells()

    print(f"  - 总 cell 数: {len(all_cells)}")
    print(f"  - 代码 cell 数: {len(code_cells)}")
    print(f"  - 节点 cell 数: {len(node_cells)}")

    # Check status
    validated = manager.list_cells_by_status(ExecutionStatus.VALIDATED.value)
    pending = manager.list_cells_by_status(ExecutionStatus.PENDING_VALIDATION.value)

    print(f"  - validated 节点: {len(validated)}")
    print(f"  - pending_validation 节点: {len(pending)}")

    # Check complete info
    print(f"\n✓ 节点完整信息:")
    for node_id in ["load_data", "process_data", "plot_data"]:
        info = manager.get_node_with_results(node_id)
        if info:
            print(f"  - {node_id}: 有结果={info['has_results']}")

    # Open file to view
    print(f"\n✓ Notebook 已保存到: {notebook_path}")
    print(f"✓ 可以在 Jupyter 中打开查看!")

    # Cleanup
    shutil.rmtree(test_root)
    print()


if __name__ == "__main__":
    try:
        test_markdown_linked_to_node()
        test_execution_status_tracking()
        test_result_cells()
        test_complete_workflow()

        print("=" * 70)
        print("所有测试通过! ✓")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
