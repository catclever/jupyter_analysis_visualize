#!/usr/bin/env python3
"""
验证脚本 - 检查DataFrame字典执行的完整逻辑

用途: 在执行create_dict节点后，运行此脚本验证所有步骤是否正确
"""

import json
import sys
from pathlib import Path

def print_header(text):
    """打印分隔符和标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_status(check_name, passed, details=""):
    """打印检查状态"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {check_name}")
    if details:
        print(f"       {details}")

def verify_project():
    """验证整个执行流程"""

    project_dir = Path(__file__).parent
    project_json = project_dir / "project.json"
    parquets_dir = project_dir / "parquets"
    dict_dir = parquets_dir / "create_dict"
    metadata_file = dict_dir / "_metadata.json"

    results = []

    # ==================== 检查1: project.json存在且有效 ====================
    print_header("检查1: project.json 有效性")

    if not project_json.exists():
        print_status("project.json 存在", False)
        return False

    try:
        with open(project_json) as f:
            data = json.load(f)
        print_status("project.json 可解析", True)
    except Exception as e:
        print_status("project.json 可解析", False, str(e))
        return False

    # ==================== 检查2: 节点信息 ====================
    print_header("检查2: 节点信息")

    nodes = data.get("nodes", [])
    create_dict_node = next((n for n in nodes if n.get("node_id") == "create_dict"), None)

    if not create_dict_node:
        print_status("find create_dict node", False)
        return False

    print_status("find create_dict node", True)

    # 检查执行状态
    status = create_dict_node.get("execution_status")
    is_executed = status == "validated"
    print_status("execution_status = 'validated'", is_executed, f"当前: {status}")

    # 检查result_format
    result_format = create_dict_node.get("result_format")
    has_result_format = result_format == "parquet"
    print_status("result_format = 'parquet'", has_result_format, f"当前: {result_format}")

    # 检查result_is_dict
    is_dict = create_dict_node.get("result_is_dict")
    print_status("result_is_dict = true", is_dict, f"当前: {is_dict}")

    # 检查result_path
    result_path = create_dict_node.get("result_path")
    correct_path = result_path == "parquets/create_dict"
    print_status("result_path = 'parquets/create_dict'", correct_path, f"当前: {result_path}")

    if not is_executed:
        print("\n⚠️  节点未执行！请先通过API执行节点")
        return False

    # ==================== 检查3: 文件系统结构 ====================
    print_header("检查3: 文件系统结构")

    # 检查parquets目录
    if not parquets_dir.exists():
        print_status("parquets/ 目录存在", False)
        return False
    print_status("parquets/ 目录存在", True)

    # 检查dict子目录
    if not dict_dir.exists():
        print_status("parquets/create_dict/ 目录存在", False)
        return False
    print_status("parquets/create_dict/ 目录存在", True)

    # 检查_metadata.json
    if not metadata_file.exists():
        print_status("parquets/create_dict/_metadata.json 文件存在", False)
        return False

    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
        print_status("parquets/create_dict/_metadata.json 有效", True)
    except Exception as e:
        print_status("parquets/create_dict/_metadata.json 有效", False, str(e))
        return False

    # 检查metadata内容
    expected_keys = {"sales", "customers", "products"}
    actual_keys = set(metadata.get("keys", []))
    keys_match = actual_keys == expected_keys
    print_status(f"metadata.keys = {expected_keys}", keys_match, f"实际: {actual_keys}")

    # 检查parquet文件
    print("\n检查各个DataFrame的parquet文件:")
    all_parquets_exist = True
    for key in expected_keys:
        parquet_file = dict_dir / f"{key}.parquet"
        exists = parquet_file.exists()
        all_parquets_exist = all_parquets_exist and exists

        if exists:
            size = parquet_file.stat().st_size
            print_status(f"  parquets/create_dict/{key}.parquet", True, f"大小: {size} bytes")
        else:
            print_status(f"  parquets/create_dict/{key}.parquet", False)

    # ==================== 检查4: 元数据完整性 ====================
    print_header("检查4: 元数据完整性")

    required_fields = {
        "execution_status": "validated",
        "result_format": "parquet",
        "result_is_dict": True,
        "result_path": "parquets/create_dict"
    }

    all_fields_ok = True
    for field, expected_value in required_fields.items():
        actual_value = create_dict_node.get(field)
        is_correct = actual_value == expected_value
        all_fields_ok = all_fields_ok and is_correct

        print_status(
            f"{field}",
            is_correct,
            f"期望: {expected_value}, 实际: {actual_value}"
        )

    # ==================== 总结 ====================
    print_header("执行流程验证总结")

    all_checks_passed = (
        is_executed and
        has_result_format and
        is_dict and
        correct_path and
        dict_dir.exists() and
        metadata_file.exists() and
        keys_match and
        all_parquets_exist and
        all_fields_ok
    )

    if all_checks_passed:
        print("✅ 所有检查通过！")
        print("\n执行流程正确:")
        print("  1. 节点执行成功")
        print("  2. dict结果被正确识别")
        print("  3. 文件保存到正确位置")
        print("  4. project.json元数据完整")
        print("\n前端应该能够:")
        print("  ✅ 识别result_is_dict = true")
        print("  ✅ 使用result_format = 'parquet'加载数据")
        print("  ✅ 显示DictResultDisplay组件")
        print("  ✅ 展示3个DataFrame表格")
        return True
    else:
        print("❌ 部分检查失败")
        print("\n需要排查的项目:")

        if not is_executed:
            print("  - 节点执行状态不是'validated'")
        if not has_result_format:
            print("  - result_format 没有保存到project.json")
        if not is_dict:
            print("  - result_is_dict 标志不正确")
        if not correct_path:
            print("  - result_path 不正确")
        if not dict_dir.exists():
            print("  - parquets/create_dict/ 目录不存在")
        if not all_parquets_exist:
            print("  - parquet文件缺失")
        if not keys_match:
            print("  - _metadata.json 的keys不匹配")

        return False

def print_file_structure():
    """打印项目的文件结构"""
    print_header("项目文件结构")

    project_dir = Path(__file__).parent
    print(f"项目路径: {project_dir}\n")

    def print_tree(path, prefix="", is_last=True):
        """递归打印目录树"""
        if not path.exists():
            return

        # 打印当前项
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{path.name}")

        # 如果是目录，递归打印子项
        if path.is_dir():
            children = sorted(list(path.iterdir()))
            # 过滤掉__pycache__等
            children = [c for c in children if c.name not in {'__pycache__', '.ipynb_checkpoints'}]

            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                extension = "    " if is_last else "│   "
                print_tree(child, prefix + extension, is_last_child)

    print_tree(project_dir, is_last=True)

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  DataFrame 字典执行流程验证工具")
    print("="*60)

    # 显示文件结构
    print_file_structure()

    # 执行验证
    success = verify_project()

    # 返回
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
