"""Test what happens when empty code is sent"""
import json
import requests
from pathlib import Path

PROJECT_ID = "dict_result_test"
NODE_ID = "create_summaries"

BASE_URL = "http://localhost:8000"

print("\n=== Testing Empty Code Save ===\n")

# First, get and show current code
print("1. Getting current code...")
response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code")
if response.ok:
    current_code = response.json()['code']
    print(f"✓ Current code length: {len(current_code)} chars")

# Save EMPTY code
print("\n2. Saving EMPTY code...")
EMPTY_CODE = ""
response = requests.put(
    f"{BASE_URL}/api/projects/{PROJECT_ID}/nodes/{NODE_ID}/code",
    json={"code": EMPTY_CODE},
    headers={"Content-Type": "application/json"}
)
if response.ok:
    result = response.json()
    print(f"✓ Response status: OK")
    print(f"  Returned code length: {len(result['code'])} chars")
    print(f"  Full returned code:\n{result['code']}")
else:
    print(f"✗ Failed: {response.status_code}")

# Check what's in the notebook
print("\n3. Checking notebook...")
notebook_path = Path("projects/dict_result_test/project.ipynb")
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

for i, cell in enumerate(notebook.get('cells', [])):
    if cell.get('cell_type') == 'code':
        metadata = cell.get('metadata', {})
        if metadata.get('node_id') == NODE_ID and not metadata.get('result_cell'):
            source = cell.get('source', '')
            if isinstance(source, list):
                source = ''.join(source)
            print(f"✓ Code cell in notebook:")
            print(f"  Length: {len(source)} chars")
            print(f"  Content:\n{source}")
            break

print("\n=== Test Complete ===\n")
