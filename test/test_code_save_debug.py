"""
Debug script for code save functionality
Helps diagnose what happens during code save operations
"""
import json
import requests
from pathlib import Path
from datetime import datetime

# Test parameters
PROJECT_ID = "dict_result_test"
NODE_ID = "create_summaries"
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def check_notebook_state(label):
    """Check and print the current notebook state"""
    print(f"\n[{datetime.now().isoformat()}] Checking notebook state ({label})...")

    notebook_path = Path("projects/dict_result_test/project.ipynb")
    if not notebook_path.exists():
        print(f"❌ Notebook not found: {notebook_path}")
        return None

    with open(notebook_path, 'r') as f:
        notebook = json.load(f)

    for i, cell in enumerate(notebook.get('cells', [])):
        if cell.get('cell_type') == 'code':
            metadata = cell.get('metadata', {})
            if metadata.get('node_id') == NODE_ID and not metadata.get('result_cell'):
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)

                print(f"✓ Found code cell at index {i}:")
                print(f"  Source length: {len(source)} chars")
                print(f"  Has @node_type: {'@node_type' in source}")
                print(f"  First 100 chars: {repr(source[:100])}")
                print(f"  Last 100 chars: {repr(source[-100:])}")

                return {
                    'index': i,
                    'length': len(source),
                    'source': source
                }

    print(f"❌ Code cell for node {NODE_ID} not found")
    return None


def test_save_operation():
    """Test a complete save operation with detailed logging"""

    print_section("INITIAL STATE")
    initial_state = check_notebook_state("initial")
    if not initial_state:
        return False

    print_section("GET CURRENT CODE")
    print(f"Fetching code from API...")
    response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
    if not response.ok:
        print(f"❌ Failed to get code: {response.status_code}")
        return False

    api_code = response.json()['code']
    print(f"✓ Got code from API:")
    print(f"  Length: {len(api_code)} chars")
    print(f"  First 100 chars: {repr(api_code[:100])}")

    print_section("PREPARE NEW CODE")
    # Create a modified version with a timestamp marker
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_code = f"""# Modified at {timestamp}
import pandas as pd
import os

# Load sample data
csv_path = os.path.join(os.getcwd(), 'sample_data.csv')
df = pd.read_csv(csv_path)

# Create summaries
create_summaries = {{
    'summary_1': df.head(),
    'summary_2': df.tail(),
}}
"""

    print(f"Prepared new code:")
    print(f"  Length: {len(new_code)} chars")
    print(f"  Marker: 'Modified at {timestamp}'")
    print(f"  First 100 chars: {repr(new_code[:100])}")

    print_section("SAVE CODE VIA API")
    print(f"Sending PUT request to /api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
    response = requests.put(
        f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code",
        json={"code": new_code},
        headers={"Content-Type": "application/json"}
    )

    if not response.ok:
        print(f"❌ Save failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    api_response = response.json()
    print(f"✓ Save successful:")
    print(f"  Response code length: {len(api_response['code'])} chars")
    print(f"  Response dependencies: {api_response.get('depends_on', [])}")
    print(f"  Response execution_status: {api_response.get('execution_status', 'unknown')}")

    print_section("VERIFY IN NOTEBOOK")
    saved_state = check_notebook_state("after save")
    if not saved_state:
        return False

    # Check if the timestamp marker is in the saved code
    if timestamp in saved_state['source']:
        print(f"\n✅ Code was saved correctly!")
        print(f"   Timestamp marker found in notebook")
        print(f"   Original length: {initial_state['length']} → New length: {saved_state['length']}")
        return True
    else:
        print(f"\n❌ Code was NOT saved correctly!")
        print(f"   Timestamp marker NOT found in notebook")
        print(f"   Expected to find: 'Modified at {timestamp}'")
        print(f"\n   Actual saved code:")
        print(f"   {repr(saved_state['source'][:200])}")
        return False


def test_api_request_logging():
    """Log what the API receives"""

    print_section("API REQUEST LOGGING TEST")

    test_code = "# Test code - can you see this?\nx = 42"

    print(f"Sending test code:")
    print(f"  Code: {repr(test_code)}")
    print(f"  Length: {len(test_code)} chars")

    print(f"\nMaking PUT request...")
    response = requests.put(
        f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code",
        json={"code": test_code},
        headers={"Content-Type": "application/json"}
    )

    print(f"\nResponse:")
    print(f"  Status: {response.status_code}")

    if response.ok:
        api_response = response.json()
        print(f"  Returned code length: {len(api_response['code'])} chars")

        # Check backend logs to see what it received
        print(f"\n📝 Check backend logs for:")
        print(f"   'DEBUG: code_content length=...'")
        print(f"   This will show what the backend actually received")
    else:
        print(f"  Error: {response.text}")


def main():
    """Run all diagnostics"""

    print("\n" + "=" * 80)
    print("CODE SAVE DEBUG & DIAGNOSTICS")
    print("=" * 80)

    print("\nThis script helps diagnose code save issues by:")
    print("  1. Checking the notebook state before and after saves")
    print("  2. Logging what the API sends and receives")
    print("  3. Verifying that changes are persisted")

    print("\n⚠️  Make sure the backend is running on http://localhost:8000")

    try:
        # Test 1: Full save operation
        print("\n[Test 1/2] Full save operation...")
        result1 = test_save_operation()

        # Test 2: API request logging
        print("\n[Test 2/2] API request logging...")
        test_api_request_logging()

        print_section("DIAGNOSTICS COMPLETE")

        if result1:
            print("✅ Code save is working correctly!")
        else:
            print("❌ Code save has issues!")
            print("\nNext steps:")
            print("  1. Check the backend logs for 'DEBUG:' output")
            print("  2. Open browser dev tools and check Console tab")
            print("  3. Look for '[DEBUG:handleCodeChange]' and '[DEBUG:handleCodeSave]' logs")
            print("  4. Share the logs to diagnose the issue")

        return result1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
