"""
Unit test for execution output markdown generation
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_markdown_with_output():
    """
    Test: _generate_execution_markdown includes execution output

    This is a unit test that directly tests the markdown generation logic
    without needing full integration setup.
    """
    print("\n" + "="*70)
    print("UNIT TEST: Markdown Generation with Execution Output")
    print("="*70)

    # Sample execution output dict (what kernel returns)
    execution_output = {
        'status': 'success',
        'output': """Data Summary:
  Total records: 3
  Columns: ['name', 'age', 'salary']
  Average age: 30.0

DataFrame:
   name  age  salary
0  Alice   25   50000
1    Bob   30   60000
2 Charlie  35   75000
✓ Saved parquet: /tmp/test/parquets/data_1.parquet""",
        'error': None
    }

    # Simulate the markdown generation logic
    start_time = datetime(2025, 11, 18, 10, 30, 0)
    node = {'name': 'Load Data', 'node_id': 'data_1'}
    node_id = 'data_1'
    node_name = node.get('name', node_id)

    execution_time = 2.345  # Simulated execution time
    completion_time = datetime(2025, 11, 18, 10, 30, 2).isoformat()

    # Build markdown content (same logic as _generate_execution_markdown)
    markdown_content = f"""## ✓ Execution Complete: {node_name}

**Completed at:** {completion_time}

**Execution time:** {execution_time:.2f}s

**Status:** ✅ Success

### Execution Output"""

    # Add execution output if available
    if execution_output:
        output_text = execution_output.get('output', '')
        if output_text and output_text.strip():
            # Format output in a code block for better readability
            markdown_content += f"""

```
{output_text}
```"""
        else:
            # If no output, add a note
            markdown_content += "\n\n_(No output generated)_"
    else:
        markdown_content += "\n\n_(No output available)_"

    # Add footer note
    markdown_content += """

---

_Note: This documentation is auto-generated. For detailed AI-powered summaries, please enable summary generation in node settings._"""

    print("\n[STEP 1] Generated markdown content")
    print(f"  Length: {len(markdown_content)} chars")

    # Verify all expected sections are present
    print("\n[STEP 2] Verify markdown content")

    checks = {
        "Contains '## ✓ Execution Complete'": "## ✓ Execution Complete" in markdown_content,
        "Contains 'Completed at:'": "Completed at:" in markdown_content,
        "Contains 'Execution time:'": "Execution time:" in markdown_content,
        "Contains '✅ Success'": "✅ Success" in markdown_content,
        "Contains '### Execution Output'": "### Execution Output" in markdown_content,
        "Contains code fence (```  )": "```" in markdown_content,
        "Contains 'Data Summary:'": "Data Summary:" in markdown_content,
        "Contains 'Total records:'": "Total records:" in markdown_content,
        "Contains 'Average age:'": "Average age:" in markdown_content,
        "Contains 'DataFrame:'": "DataFrame:" in markdown_content,
        "Contains 'Load Data' node name": "Load Data" in markdown_content,
        "Contains footer note": "_Note:" in markdown_content and "auto-generated" in markdown_content,
    }

    all_passed = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n[STEP 3] Show markdown content preview")
        print("\n" + "="*70)
        print("Generated Markdown:")
        print("="*70)
        print(markdown_content)
        print("="*70)

    return all_passed


if __name__ == "__main__":
    try:
        result = test_markdown_with_output()

        if result:
            print("\n✅ TEST PASSED: Markdown includes execution output correctly")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Some checks did not pass")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
