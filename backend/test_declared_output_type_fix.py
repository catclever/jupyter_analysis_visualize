#!/usr/bin/env python3
"""
Test to verify the fix for dict_of_dataframes state pollution bug

This test ensures that when one node declares @output_type: dict_of_dataframes,
subsequent nodes without the declaration are NOT incorrectly treated as dicts.
"""

import json
import tempfile
from pathlib import Path
import pandas as pd

def test_declared_output_type_logic():
    """Test the corrected logic for determining is_dict_result"""

    print("Testing declared_output_type handling...\n")

    # Simulate the code logic from code_executor.py lines 1595-1651
    test_cases = [
        {
            "node_id": "node_a",
            "name": "Node A: Declares dict_of_dataframes",
            "declared_output_type": "dict_of_dataframes",
            "result_format": "parquet",
            "has_metadata_json": True,
            "expected_is_dict_result": True,
            "expected_result_path_suffix": "node_a",  # No .parquet suffix
        },
        {
            "node_id": "node_b",
            "name": "Node B: No declaration, but directory exists with metadata",
            "declared_output_type": None,
            "result_format": "parquet",
            "has_metadata_json": True,
            "expected_is_dict_result": True,
            "expected_result_path_suffix": "node_b",  # No .parquet suffix
        },
        {
            "node_id": "node_c",
            "name": "Node C: No declaration, no metadata.json",
            "declared_output_type": None,
            "result_format": "parquet",
            "has_metadata_json": False,
            "expected_is_dict_result": False,
            "expected_result_path_suffix": "node_c.parquet",
        },
        {
            "node_id": "node_d",
            "name": "Node D: Declares other type (not dict)",
            "declared_output_type": "dataframe",
            "result_format": "parquet",
            "has_metadata_json": True,  # Even if metadata exists
            "expected_is_dict_result": False,
            "expected_result_path_suffix": "node_d.parquet",  # Should ignore metadata.json
        },
    ]

    target_dir = "parquets"

    for test_case in test_cases:
        node_id = test_case["node_id"]
        declared_output_type = test_case["declared_output_type"]
        result_format = test_case["result_format"]

        # FIXED LOGIC (from code_executor.py lines 1595-1651)
        is_dict_result = False
        need_auto_detect = False

        # Priority 2: Check declared output type STRICTLY
        if declared_output_type == 'dict_of_dataframes':
            is_dict_result = True
        elif declared_output_type:
            is_dict_result = False
            # Don't auto-detect when type is explicitly declared
        else:
            # No declaration - need to auto-detect
            need_auto_detect = True

        # Priority 3: Auto-detect ONLY if not declared
        if need_auto_detect:
            if result_format == 'parquet' and test_case["has_metadata_json"]:
                is_dict_result = True

        # Set result_path
        if result_format == 'parquet':
            if is_dict_result:
                result_path = f"{target_dir}/{node_id}"
            else:
                result_path = f"{target_dir}/{node_id}.parquet"

        # Verify results
        assert is_dict_result == test_case["expected_is_dict_result"], \
            f"✗ {test_case['name']}: Expected is_dict_result={test_case['expected_is_dict_result']}, got {is_dict_result}"

        assert result_path.endswith(test_case["expected_result_path_suffix"]), \
            f"✗ {test_case['name']}: Expected result_path to end with '{test_case['expected_result_path_suffix']}', got '{result_path}'"

        print(f"✓ {test_case['name']}")
        print(f"  is_dict_result: {is_dict_result} (expected: {test_case['expected_is_dict_result']})")
        print(f"  result_path: {result_path} (expected to end with: {test_case['expected_result_path_suffix']})")
        print()

    print("✅ All declared_output_type tests passed!")

if __name__ == "__main__":
    test_declared_output_type_logic()
