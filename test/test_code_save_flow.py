"""
Test script to verify code save functionality
Tests the complete flow of saving code through the API
"""
import json
import requests
from pathlib import Path

# Test parameters
PROJECT_ID = "dict_result_test"
NODE_ID = "create_summaries"

BASE_URL = "http://localhost:8000"

def test_code_save_with_valid_code():
    """Test saving valid code"""
    NEW_CODE = """import pandas as pd
import os

# Load sample data (EDITED)
csv_path = os.path.join(os.getcwd(), 'sample_data.csv')
df = pd.read_csv(csv_path)

# Create multiple summaries as dict (EDITED)
create_summaries = {
    'daily_summary': df.groupby('date').agg({'value': 'sum'}).reset_index(),
    'category_summary': df.groupby('category').agg({'value': ['sum', 'mean']}).reset_index(),
    'all_records': df,
}"""

    print("\n=== Test 1: Code Save with Valid Code ===\n")

    # Step 1: Get current code
    print(f"1. Getting current code for node {NODE_ID}...")
    try:
        response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
        if response.ok:
            code_data = response.json()
            print(f"✓ Got code, length: {len(code_data['code'])} chars")
            print(f"  Preview: {code_data['code'][:100]}...")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Step 2: Save new code
    print(f"\n2. Saving new code (length: {len(NEW_CODE)} chars)...")
    try:
        response = requests.put(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code",
            json={"code": NEW_CODE},
            headers={"Content-Type": "application/json"}
        )
        if response.ok:
            result = response.json()
            print(f"✓ Code saved successfully")
            print(f"  Returned code length: {len(result['code'])} chars")
            print(f"  Returned dependencies: {result.get('depends_on', [])}")
            print(f"  Preview: {result['code'][:100]}...")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Step 3: Verify saved code in notebook
    print(f"\n3. Verifying saved code in notebook...")
    try:
        notebook_path = Path("projects/dict_result_test/project.ipynb")
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        # Find the code cell
        for i, cell in enumerate(notebook.get('cells', [])):
            if cell.get('cell_type') == 'code':
                metadata = cell.get('metadata', {})
                if metadata.get('node_id') == NODE_ID and not metadata.get('result_cell'):
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        source = ''.join(source)
                    print(f"✓ Found code cell at index {i}")
                    print(f"  Cell source length: {len(source)} chars")
                    print(f"  Contains 'EDITED': {'EDITED' in source}")
                    print(f"  Preview: {source[:100]}...")

                    # Verify the code was actually saved
                    if 'EDITED' in source and len(source) > 200:
                        print(f"\n✅ Test PASSED: Code saved correctly")
                        return True
                    else:
                        print(f"\n❌ Test FAILED: Code was not saved properly")
                        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_code_save_with_empty_code():
    """Test saving empty code (should not happen, but test it)"""
    print("\n\n=== Test 2: Code Save with Empty Code ===\n")

    EMPTY_CODE = ""

    # Get current code first
    print("1. Getting current code...")
    response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
    if not response.ok:
        print(f"✗ Failed to get code: {response.status_code}")
        return False

    current_code = response.json()['code']
    print(f"✓ Got code, length: {len(current_code)} chars")

    # Save EMPTY code
    print("\n2. Saving EMPTY code...")
    response = requests.put(
        f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code",
        json={"code": EMPTY_CODE},
        headers={"Content-Type": "application/json"}
    )

    if response.ok:
        result = response.json()
        print(f"✓ Response status: OK")
        print(f"  Returned code length: {len(result['code'])} chars")
        print(f"  Returned code contains only metadata: {len(result['code']) < 100}")

        # This is expected - saving empty code should return only metadata
        if len(result['code']) < 200:
            print(f"\n✅ Test PASSED: Empty code handled correctly (returned metadata only)")
            return True
        else:
            print(f"\n❌ Test FAILED: Expected metadata-only response")
            return False
    else:
        print(f"✗ Failed: {response.status_code}")
        return False


def test_code_retrieval():
    """Test retrieving code"""
    print("\n\n=== Test 3: Code Retrieval ===\n")

    print(f"Getting code for node {NODE_ID}...")
    try:
        response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
        if response.ok:
            code_data = response.json()
            print(f"✓ Code retrieved successfully")
            print(f"  Code length: {len(code_data['code'])} chars")
            print(f"  Language: {code_data.get('language', 'unknown')}")
            print(f"  Contains metadata: {'@node_type' in code_data['code']}")

            if len(code_data['code']) > 0:
                print(f"\n✅ Test PASSED: Code retrieved correctly")
                return True
            else:
                print(f"\n❌ Test FAILED: No code returned")
                return False
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("CODE SAVE FUNCTIONALITY TEST SUITE")
    print("=" * 80)

    results = []

    # Test 1: Code retrieval
    results.append(("Code Retrieval", test_code_retrieval()))

    # Test 2: Code save with valid code
    results.append(("Code Save (Valid)", test_code_save_with_valid_code()))

    # Test 3: Code save with empty code
    results.append(("Code Save (Empty)", test_code_save_with_empty_code()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
