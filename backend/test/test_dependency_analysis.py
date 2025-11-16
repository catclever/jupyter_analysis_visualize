#!/usr/bin/env python3
"""
Test the dynamic dependency analysis system.

This tests the new _analyze_and_update_dependencies() method that automatically
discovers dependencies by analyzing code and matching variable names to node IDs.
"""

import unittest
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_executor import CodeExecutor
from project_manager import ProjectManager


class TestDependencyAnalysis(unittest.TestCase):
    """Test dynamic dependency analysis during node execution."""

    @classmethod
    def setUpClass(cls):
        """Set up test project."""
        cls.projects_root = Path(__file__).parent.parent.parent / 'projects'
        cls.project_id = 'ecommerce_analytics'
        cls.project_dir = cls.projects_root / cls.project_id
        assert cls.project_dir.exists(), f"Test project not found: {cls.project_dir}"

    def setUp(self):
        """Create a fresh project manager for each test."""
        self.pm = ProjectManager(str(self.projects_root), self.project_id)
        self.pm.load()  # Load project metadata

    def test_extract_variable_names_simple(self):
        """Test extracting variable names from simple code (only Load context)."""
        code = """
x = 5
y = x + 10
result = y * 2
"""
        names = CodeExecutor._extract_variable_names(code)
        print(f"\nSimple code variables: {names}")
        # Only x and y are referenced (Load context), result is only assigned (Store context)
        self.assertIn('x', names)
        self.assertIn('y', names)
        self.assertNotIn('result', names)  # result is assigned, not referenced

    def test_extract_variable_names_pandas(self):
        """Test extracting variable names from pandas code."""
        code = """
import pandas as pd
result = load_orders_data.groupby('date').sum()
final = result.reset_index()
"""
        names = CodeExecutor._extract_variable_names(code)
        print(f"\nPandas code variables: {names}")
        # Should include the referenced (Load context) custom variables
        self.assertIn('load_orders_data', names)
        self.assertIn('result', names)  # result is referenced in final = result.reset_index()
        # final is only assigned, not referenced
        self.assertNotIn('final', names)
        # Should NOT include pandas/builtin
        self.assertNotIn('pd', names)
        self.assertNotIn('groupby', names)
        self.assertNotIn('sum', names)

    def test_extract_variable_names_filters_builtins(self):
        """Test that built-in functions are filtered out."""
        code = """
x = len(data)
y = print(x)
z = pd.DataFrame(result)
"""
        names = CodeExecutor._extract_variable_names(code)
        print(f"\nFiltered variables: {names}")
        # Should include custom variables
        self.assertIn('data', names)
        self.assertIn('result', names)
        # Should NOT include builtins
        self.assertNotIn('len', names)
        self.assertNotIn('print', names)
        self.assertNotIn('pd', names)

    def test_analyze_dependencies_p1_daily_sales(self):
        """Test analyzing p1_daily_sales node which uses load_orders_data."""
        # Get the code for p1_daily_sales
        node = self.pm.get_node('p1_daily_sales')
        self.assertIsNotNone(node, "p1_daily_sales node not found")

        # Get the actual code from the notebook
        notebook_path = self.project_dir / 'project.ipynb'
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        # Find the p1_daily_sales cell
        code = None
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                if '@node_id: p1_daily_sales' in source:
                    code = source
                    break

        self.assertIsNotNone(code, "p1_daily_sales code not found in notebook")

        # Analyze dependencies using static method
        print(f"\n\nAnalyzing p1_daily_sales:")
        print(f"Current depends_on: {node.get('depends_on', [])}")

        used_variables = CodeExecutor._extract_variable_names(code)
        print(f"Used variables: {used_variables}")

        all_node_ids = set(self.pm.metadata.nodes.keys())
        discovered = sorted([var for var in used_variables if var in all_node_ids])
        print(f"Discovered dependencies: {discovered}")

        # Should have load_orders_data as dependency
        self.assertIn('load_orders_data', discovered,
                      "load_orders_data should be discovered as a dependency")

    def test_analyze_dependencies_p1_sales_chart(self):
        """Test analyzing p1_sales_chart node which uses p1_category_sales."""
        # Get the code for p1_sales_chart
        node = self.pm.get_node('p1_sales_chart')
        self.assertIsNotNone(node, "p1_sales_chart node not found")

        # Get the actual code from the notebook
        notebook_path = self.project_dir / 'project.ipynb'
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        # Find the p1_sales_chart cell
        code = None
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                if '@node_id: p1_sales_chart' in source:
                    code = source
                    break

        self.assertIsNotNone(code, "p1_sales_chart code not found in notebook")

        # Analyze dependencies using static method
        print(f"\n\nAnalyzing p1_sales_chart:")
        print(f"Current depends_on: {node.get('depends_on', [])}")

        used_variables = CodeExecutor._extract_variable_names(code)
        print(f"Used variables: {used_variables}")

        all_node_ids = set(self.pm.metadata.nodes.keys())
        discovered = sorted([var for var in used_variables if var in all_node_ids])
        print(f"Discovered dependencies: {discovered}")

        # Should have p1_category_sales as dependency
        self.assertIn('p1_category_sales', discovered,
                      "p1_category_sales should be discovered as a dependency")

    def test_analyze_multiple_nodes(self):
        """Test analyzing multiple nodes to build dependency graph."""
        # Analyze several nodes
        nodes_to_analyze = [
            ('p1_daily_sales', ['load_orders_data']),
            ('p1_category_sales', ['load_orders_data']),
            ('p1_sales_chart', ['p1_category_sales']),
        ]

        notebook_path = self.project_dir / 'project.ipynb'
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        all_node_ids = set(self.pm.metadata.nodes.keys())
        print("\n\nAnalyzing multiple nodes:")
        for node_id, expected_deps in nodes_to_analyze:
            # Find the node code
            code = None
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = ''.join(cell.get('source', []))
                    if f'@node_id: {node_id}' in source:
                        code = source
                        break

            self.assertIsNotNone(code, f"Code for {node_id} not found")

            # Analyze using static method
            used_variables = CodeExecutor._extract_variable_names(code)
            discovered = sorted([var for var in used_variables if var in all_node_ids and var != node_id])
            print(f"  {node_id}: {discovered}")

            for expected_dep in expected_deps:
                self.assertIn(expected_dep, discovered,
                            f"{expected_dep} should be a dependency of {node_id}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
