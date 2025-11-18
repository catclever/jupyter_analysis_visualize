"""Test script to verify code save functionality"""
import json
import requests
from pathlib import Path

# Test parameters
PROJECT_ID = "dict_result_test"
NODE_ID = "create_summaries"
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

BASE_URL = "http://localhost:8000"

print("\n=== Testing Code Save Flow ===\n")

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
except Exception as e:
    print(f"✗ Error: {e}")

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
except Exception as e:
    print(f"✗ Error: {e}")

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
                break
except Exception as e:
    print(f"✗ Error: {e}")

print("\n=== Test Complete ===\n")
