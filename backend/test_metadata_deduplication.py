"""
Test for metadata comment deduplication fix

This test verifies that when a node is executed multiple times,
the system-managed metadata comments are not duplicated in the cell source.

Issue: When a node was executed multiple times, metadata comments could accumulate
in the cell source, creating duplicate headers like:
  # ===== System-managed metadata =====
  # @node_type: compute
  # @node_id: node1
  # ===== End of system-managed metadata =====
  # ===== System-managed metadata =====
  # @node_type: compute
  # @node_id: node1
  # ===== End of system-managed metadata =====
  actual code here

Fix: Modified _get_node_code() to always extract code after metadata comments,
preventing duplicates from accumulating during repeated executions.
"""

import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

# Add backend to path
import sys
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from notebook_manager import NotebookManager


class TestMetadataDeduplication(unittest.TestCase):
    """Test metadata deduplication on repeated node executions"""

    def setUp(self):
        """Create temporary test directory and project"""
        self.test_dir = tempfile.mkdtemp(prefix="test_metadata_dedup_")
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_extract_code_after_metadata_single(self):
        """Test that code after single metadata block is correctly extracted"""
        code_with_metadata = """# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: compute
# @node_id: node_1
# ===== End of system-managed metadata =====

x = 5
y = x + 10
print(y)"""

        expected_code = """
x = 5
y = x + 10
print(y)"""

        actual_code = NotebookManager._extract_code_after_metadata(code_with_metadata)

        # Compare without leading/trailing whitespace differences
        self.assertEqual(actual_code.strip(), expected_code.strip())

    def test_extract_code_after_metadata_no_metadata(self):
        """Test that code without metadata is returned as-is"""
        code_without_metadata = """x = 5
y = x + 10
print(y)"""

        actual_code = NotebookManager._extract_code_after_metadata(code_without_metadata)

        self.assertEqual(actual_code.strip(), code_without_metadata.strip())

    def test_extract_code_with_empty_lines_after_metadata(self):
        """Test that empty lines after metadata are preserved"""
        code_with_metadata = """# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: compute
# @node_id: node_1
# ===== End of system-managed metadata =====


# This code has empty lines after metadata
x = 5
y = x + 10"""

        actual_code = NotebookManager._extract_code_after_metadata(code_with_metadata)

        # Should preserve empty lines and the actual code
        self.assertIn("x = 5", actual_code)
        self.assertIn("y = x + 10", actual_code)
        self.assertNotIn("@node_type", actual_code)

    def test_extract_code_prevents_duplicate_accumulation(self):
        """
        Test that extracting code multiple times prevents metadata duplication.

        This is the core scenario: if we call _extract_code_after_metadata
        multiple times (simulating repeated executions), it should always
        return clean code without metadata.
        """
        original_code = "x = 42\ncompute_1 = x * 2"

        # Create code with metadata (as if it was executed once)
        metadata_header = """# ===== System-managed metadata (auto-generated, understand to edit) =====
# @node_type: compute
# @node_id: compute_1
# ===== End of system-managed metadata =====
"""

        code_first_execution = metadata_header + "\n" + original_code

        # Extract code after first execution
        extracted_first = NotebookManager._extract_code_after_metadata(code_first_execution)

        # If metadata were to be added again (simulating next execution)
        # The metadata should only be added once when sync happens
        code_second_execution = metadata_header + "\n" + extracted_first

        # Extract code after second execution
        extracted_second = NotebookManager._extract_code_after_metadata(code_second_execution)

        # Both extractions should yield the same clean code
        self.assertEqual(extracted_first.strip(), extracted_second.strip())
        self.assertEqual(extracted_first.strip(), original_code.strip())

        # Verify no metadata in either extraction
        self.assertNotIn("System-managed metadata", extracted_first)
        self.assertNotIn("System-managed metadata", extracted_second)


if __name__ == '__main__':
    unittest.main()
