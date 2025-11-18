#!/usr/bin/env python3
"""
P3 Top Products 优化验证脚本

测试目标:
1. 验证 P0: notebook cell 拆分是否正确
2. 验证 P1: kernel_manager 对 DataFrame 的支持
3. 验证 P2: execution_manager 的异常处理
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

def test_p0_notebook_structure():
    """验证 P0: notebook cell 代码是否正确拆分"""
    print("\n" + "="*80)
    print("【P0 验证】Notebook Cell 代码拆分")
    print("="*80)

    notebook_path = Path(__file__).parent.parent.parent / "projects/ecommerce_analytics.init/project.ipynb"

    try:
        import nbformat
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)

        # 找到 p3_top_products cell
        p3_cell = None
        for cell in notebook.cells:
            if cell.get('metadata', {}).get('tags') or 'p3_top_products' in str(cell.get('source', '')):
                if 'p3_top_products' in str(cell.get('source', '')):
                    p3_cell = cell
                    break

        if p3_cell:
            source = p3_cell['source']

            # 检查是否包含拆分后的代码模式
            if '.sort_values' in source and '.head(10)' in source:
                # 计算有多少行代码
                lines = source.split('\n')
                assignment_lines = [l for l in lines if '=' in l and 'p3_top_products' in l]

                if len(assignment_lines) >= 2:
                    print("✅ P0 验证通过: Cell 代码已正确拆分为多行")
                    print(f"   - 找到 {len(assignment_lines)} 个赋值操作")
                    print(f"   - 拆分后便于追踪变量")
                    return True
                else:
                    print("⚠️  P0 验证警告: 仍然是单行赋值")
                    print("   - 建议检查 cell 是否正确编辑")
                    return False
            else:
                print("❌ P0 验证失败: 未找到预期的代码结构")
                return False
        else:
            print("⚠️  无法读取 notebook")
            return False

    except Exception as e:
        print(f"⚠️  P0 验证出错: {e}")
        return False


def test_p1_kernel_manager_dataframe():
    """验证 P1: kernel_manager 是否支持 DataFrame"""
    print("\n" + "="*80)
    print("【P1 验证】kernel_manager 对 DataFrame 支持")
    print("="*80)

    try:
        from kernel_manager import KernelManager

        # 检查源代码是否包含 DataFrame 处理
        import inspect
        source = inspect.getsource(KernelManager.get_variable)

        if "if var_type == 'DataFrame'" in source:
            print("✅ P1 验证通过: kernel_manager 已添加 DataFrame 处理")

            # 检查是否使用 pickle
            if 'pickle.dumps' in source or 'cloudpickle' in source:
                print("   - 使用了 pickle/cloudpickle 序列化")

            # 检查是否有反序列化逻辑
            if 'pickle.loads' in source:
                print("   - 包含反序列化逻辑")

            return True
        else:
            print("❌ P1 验证失败: 未找到 DataFrame 处理代码")
            return False

    except Exception as e:
        print(f"❌ P1 验证出错: {e}")
        return False


def test_p2_exception_handling():
    """验证 P2: execution_manager 是否改进了异常处理"""
    print("\n" + "="*80)
    print("【P2 验证】execution_manager 异常处理")
    print("="*80)

    try:
        from execution_manager import ExecutionManager

        # 检查源代码是否改进了异常处理
        import inspect
        source = inspect.getsource(ExecutionManager.execute_node)

        checks = {
            "logging": "logging" in source or "logger" in source,
            "error_logging": "logger.warning" in source or "logger.error" in source,
            "error_complete": "execution.complete(error=" in source,
            "exception_info": "type(e).__name__" in source or "str(e)" in source
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        if passed >= 3:  # 至少 3 个检查通过
            print(f"✅ P2 验证通过: 异常处理已改进 ({passed}/{total})")

            if checks["logging"]:
                print("   - 添加了日志记录")
            if checks["error_complete"]:
                print("   - 错误状态会被正确标记")
            if checks["exception_info"]:
                print("   - 异常信息被记录")

            return True
        else:
            print(f"❌ P2 验证失败: 异常处理改进不足 ({passed}/{total})")
            for check, status in checks.items():
                print(f"   - {check}: {'✅' if status else '❌'}")
            return False

    except Exception as e:
        print(f"❌ P2 验证出错: {e}")
        return False


def test_parquet_existence():
    """验证: 检查 parquet 文件是否存在"""
    print("\n" + "="*80)
    print("【文件验证】Parquet 文件检查")
    print("="*80)

    project_path = Path(__file__).parent.parent.parent / "projects/ecommerce_analytics.init/parquets"

    files_to_check = [
        "load_orders_data.parquet",
        "load_products_data.parquet",
        "p3_top_products.parquet"
    ]

    results = {}
    for filename in files_to_check:
        filepath = project_path / filename
        exists = filepath.exists()
        results[filename] = exists

        status = "✅" if exists else "❌"
        print(f"{status} {filename}: {'存在' if exists else '不存在'}")

    return results


def test_project_json():
    """验证: 检查 project.json 的记录"""
    print("\n" + "="*80)
    print("【配置验证】project.json 记录检查")
    print("="*80)

    config_path = Path(__file__).parent.parent.parent / "projects/ecommerce_analytics.init/project.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 找到 p3_top_products 节点配置
        p3_node = None
        for node in config.get('nodes', []):
            if node.get('node_id') == 'p3_top_products':
                p3_node = node
                break

        if p3_node:
            print(f"✅ 找到 p3_top_products 节点配置")
            print(f"   - 执行状态: {p3_node.get('execution_status')}")
            print(f"   - 结果路径: {p3_node.get('result_path')}")
            print(f"   - 执行耗时: {p3_node.get('execution_time', 'N/A')} 秒")
            print(f"   - 输出类型: {p3_node.get('output_type')}")

            return p3_node
        else:
            print("❌ 未找到 p3_top_products 节点配置")
            return None

    except Exception as e:
        print(f"❌ 读取 project.json 失败: {e}")
        return None


def main():
    """主测试函数"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "P3 优化方案 - 完整验证" + " "*32 + "║")
    print("╚" + "="*78 + "╝")

    results = {
        "P0 (Notebook 拆分)": test_p0_notebook_structure(),
        "P1 (DataFrame 支持)": test_p1_kernel_manager_dataframe(),
        "P2 (异常处理)": test_p2_exception_handling(),
    }

    # 检查文件
    file_results = test_parquet_existence()
    project_node = test_project_json()

    # 总结
    print("\n" + "="*80)
    print("【验证总结】")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {check}: {'通过' if status else '未通过'}")

    print(f"\n总体: {passed}/{total} 项通过")

    if passed == total:
        print("\n🎉 所有优化验证通过！")
        print("\n后续步骤:")
        print("1. 在 Backend 中重新执行 p3_top_products 节点")
        print("2. 验证 parquets/p3_top_products.parquet 文件是否生成")
        print("3. 验证文件大小和数据完整性")
    else:
        print(f"\n⚠️  仍有 {total - passed} 项需要修复")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
