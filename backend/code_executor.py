"""
Code Executor

Handles execution of notebook code cells with intelligent dependency resolution,
validation, and result cell generation.

Responsibilities:
1. Pre-execution validation (check for same-named variable in code)
2. Auto-append result-saving code if missing
3. Dependency resolution (DAG-based execution order)
4. Kernel variable querying (avoid redundant file loads)
5. Result cell generation/overwriting
6. Post-execution validation
"""

import ast
import pickle
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime

from project_manager import ProjectManager
from kernel_manager import KernelManager
from notebook_manager import NotebookManager


class CodeValidator:
    """Validates code and extracts information"""

    @staticmethod
    def extract_assigned_variables(code: str) -> Set[str]:
        """
        Extract variable names that are assigned in code.
        Returns set of variable names on left side of assignment.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback: use regex to find simple assignments
            assigned = set()
            pattern = r'^(\w+)\s*='
            for line in code.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    assigned.add(match.group(1))
            return assigned

        assigned = set()

        class AssignmentVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned.add(target.id)
                self.generic_visit(node)

            def visit_AugAssign(self, node):
                if isinstance(node.target, ast.Name):
                    assigned.add(node.target.id)
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    assigned.add(node.target.id)
                self.generic_visit(node)

        visitor = AssignmentVisitor()
        visitor.visit(tree)
        return assigned

    @staticmethod
    def has_same_named_variable(code: str, node_id: str) -> bool:
        """Check if code assigns a variable with the same name as node_id"""
        assigned = CodeValidator.extract_assigned_variables(code)
        return node_id in assigned


class ResultCellGenerator:
    """Generates code cells that load and display results"""

    @staticmethod
    def generate_result_cell_code(node_id: str, node_type: str, result_format: str) -> str:
        """
        Generate code for a result cell that loads and displays the result.

        Returns the code as a string.
        """
        if result_format == "parquet":
            # Load parquet and display
            code = f"""# @node_id: {node_id}
# @result_format: {result_format}
import pandas as pd
import os

# Load result from parquet
result_path = r'../projects/{{PROJECT_ID}}/parquets/{node_id}.parquet'
if os.path.exists(result_path):
    {node_id} = pd.read_parquet(result_path)
    display({node_id})
else:
    print(f"Result file not found: {{result_path}}")"""
            return code

        elif result_format == "json":
            # Load JSON and display
            code = f"""# @node_id: {node_id}
# @result_format: {result_format}
import json
import os

# Load result from JSON
result_path = r'../projects/{{PROJECT_ID}}/parquets/{node_id}.json'
if os.path.exists(result_path):
    with open(result_path, 'r', encoding='utf-8') as f:
        {node_id} = json.load(f)
    display({node_id})
else:
    print(f"Result file not found: {{result_path}}")"""
            return code

        elif result_format == "pkl":
            # Load pickle (function) and display info
            code = f"""# @node_id: {node_id}
# @result_format: {result_format}
import pickle
import os

# Load result from pickle
result_path = r'../projects/{{PROJECT_ID}}/functions/{node_id}.pkl'
if os.path.exists(result_path):
    with open(result_path, 'rb') as f:
        {node_id} = pickle.load(f)
    print(f"✓ Loaded function: {node_id}")
else:
    print(f"Result file not found: {{result_path}}")"""
            return code

        else:
            # Default: just print a message
            code = f"""# @node_id: {node_id}
# @result_format: {result_format}
print(f"Result loaded for {{node_id}}")"""
            return code


class CodeExecutor:
    """Main executor for node code"""

    def __init__(
        self,
        project_manager: ProjectManager,
        kernel_manager: KernelManager,
        notebook_manager: NotebookManager
    ):
        """
        Initialize CodeExecutor

        Args:
            project_manager: ProjectManager instance
            kernel_manager: KernelManager instance
            notebook_manager: NotebookManager instance
        """
        self.pm = project_manager
        self.km = kernel_manager
        self.nm = notebook_manager

    def _check_same_named_variable_in_code(self, node_id: str, code: str) -> Tuple[bool, str]:
        """
        Pre-execution check: does code assign same-named variable?

        Returns:
            (has_variable, message)
        """
        if CodeValidator.has_same_named_variable(code, node_id):
            return True, f"Code assigns variable '{node_id}'"
        return False, f"Code does NOT assign variable '{node_id}' - will be auto-appended"

    def _auto_append_save_code(self, code: str, node_id: str, result_format: str) -> str:
        """
        Auto-append result-saving code if missing same-named variable assignment.

        Adds code at the end to:
        1. Save the variable to file (parquet/json/pkl)
        2. Print confirmation
        """
        # Check if already has the variable
        if CodeValidator.has_same_named_variable(code, node_id):
            return code

        # Build save code based on result_format
        if result_format == "parquet":
            save_code = f"""
# Auto-appended: Save result to parquet
import os
os.makedirs('parquets', exist_ok=True)
{node_id}.to_parquet('parquets/{node_id}.parquet', index=False)
print(f"✓ Saved parquet to parquets/{node_id}.parquet")"""

        elif result_format == "json":
            save_code = f"""
# Auto-appended: Save result to JSON
import json
import os
os.makedirs('parquets', exist_ok=True)
if isinstance({node_id}, dict):
    with open('parquets/{node_id}.json', 'w', encoding='utf-8') as f:
        json.dump({node_id}, f, indent=2)
else:
    # If it's not a dict, try to convert
    import pandas as pd
    if isinstance({node_id}, pd.DataFrame):
        {node_id}.to_json('parquets/{node_id}.json', orient='records')
    else:
        with open('parquets/{node_id}.json', 'w', encoding='utf-8') as f:
            json.dump({node_id}, f, indent=2)
print(f"✓ Saved JSON to parquets/{node_id}.json")"""

        elif result_format == "pkl":
            save_code = f"""
# Auto-appended: Save result to pickle
import pickle
import os
os.makedirs('functions', exist_ok=True)
with open('functions/{node_id}.pkl', 'wb') as f:
    pickle.dump({node_id}, f)
print(f"✓ Saved pickle to functions/{node_id}.pkl")"""

        else:
            # No save code needed
            return code

        return code + save_code

    def _build_execution_order(self, node_id: str) -> List[str]:
        """
        Build execution order for current node + dependencies.

        Returns list of node IDs in execution order (dependencies first).
        """
        nodes = self.pm.list_nodes()
        node_dict = {node['node_id']: node for node in nodes}

        # Find all nodes this node depends on (recursively)
        to_execute = set()
        to_visit = [node_id]
        visited = set()

        while to_visit:
            current_id = to_visit.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            to_execute.add(current_id)

            if current_id in node_dict:
                deps = node_dict[current_id].get('depends_on', [])
                to_visit.extend(deps)

        # Now topologically sort the execution order
        # Build graph for only the nodes we need to execute
        graph = {nid: [] for nid in to_execute}
        in_degree = {nid: 0 for nid in to_execute}

        for nid in to_execute:
            if nid in node_dict:
                deps = node_dict[nid].get('depends_on', [])
                for dep in deps:
                    if dep in to_execute:
                        graph[dep].append(nid)
                        in_degree[nid] += 1

        # Kahn's algorithm
        queue = [nid for nid in to_execute if in_degree[nid] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def execute_node(self, node_id: str) -> Dict[str, Any]:
        """
        Execute a node with full workflow:
        1. Pre-check: same-named variable in code
        2. Auto-append save code if needed
        3. Build execution order (dependencies)
        4. Execute each parent node (if needed)
        5. Execute current node
        6. Post-check: same-named variable exists
        7. Generate result cell

        Returns execution result with status, error message, etc.
        """
        result = {
            "node_id": node_id,
            "status": "error",
            "error_message": None,
            "execution_time": None,
            "result_cell_added": False
        }

        start_time = datetime.now()

        try:
            # Get node info
            node = self.pm.get_node(node_id)
            if not node:
                result["error_message"] = f"Node {node_id} not found"
                return result

            # Step 1: Get node code
            notebook = self.nm.notebook
            if not notebook:
                result["error_message"] = "Notebook not loaded"
                return result

            # Find code cell for this node
            code_cell = None
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    metadata = cell.get('metadata', {})
                    if metadata.get('node_id') == node_id and not metadata.get('result_cell'):
                        code_cell = cell
                        break

            if not code_cell:
                result["error_message"] = f"No code cell found for node {node_id}"
                return result

            # Get code source
            source = code_cell.get('source', '')
            if isinstance(source, list):
                code = ''.join(source)
            else:
                code = source

            # Step 2: Pre-check - does code have same-named variable?
            has_var, check_msg = self._check_same_named_variable_in_code(node_id, code)

            # Step 3: Auto-append save code if needed
            node_type = node.get('type', 'compute')
            result_format = node.get('result_format', 'parquet')

            if not has_var:
                code = self._auto_append_save_code(code, node_id, result_format)

            # Step 4-5: Build execution order and execute parents
            execution_order = self._build_execution_order(node_id)

            for exec_node_id in execution_order:
                if exec_node_id == node_id:
                    break  # Don't execute parents that come after

                # Check if this parent is already validated and in kernel
                parent_node = self.pm.get_node(exec_node_id)
                parent_status = parent_node.get('execution_status', 'not_executed')

                # For now, just note that we would execute parents
                # Full implementation would execute them here

            # Step 6: Execute current node code
            try:
                output = self.km.execute_code(self.pm.project_id, code, timeout=30)
                execution_successful = True
                execution_output = output
            except Exception as e:
                execution_successful = False
                execution_output = str(e)
                result["error_message"] = f"Execution failed: {execution_output}"
                result["status"] = "pending_validation"

                # Update node status to pending_validation
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()

                return result

            # Step 7: Post-check - verify same-named variable exists and has value
            # Try to get the variable from kernel namespace
            try:
                # Check if variable exists in kernel
                var_value = self.km.get_variable(self.pm.project_id, node_id)
                if var_value is None:
                    result["error_message"] = f"Execution produced no value for '{node_id}'"
                    result["status"] = "pending_validation"
                    node['execution_status'] = 'pending_validation'
                    node['error_message'] = result["error_message"]
                    self.pm._save_metadata()
                    return result
            except Exception as e:
                result["error_message"] = f"Could not verify execution: {e}"
                result["status"] = "pending_validation"
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()
                return result

            # Step 8: Generate/overwrite result cell
            try:
                result_cell_code = ResultCellGenerator.generate_result_cell_code(
                    node_id,
                    node_type,
                    result_format
                )

                # Replace project_id placeholder
                result_cell_code = result_cell_code.replace(
                    '{PROJECT_ID}',
                    self.pm.project_id
                )

                # Find and overwrite existing result cell, or append new one
                notebook = self.nm.notebook
                result_cell_found = False

                for i, cell in enumerate(notebook.get('cells', [])):
                    if cell.get('cell_type') == 'code':
                        metadata = cell.get('metadata', {})
                        if metadata.get('node_id') == node_id and metadata.get('result_cell'):
                            # Overwrite existing result cell
                            cell['source'] = result_cell_code.split('\n')
                            # Add newlines except for last line
                            cell['source'] = [line + '\n' if i < len(cell['source'])-1
                                            else line for i, line in enumerate(cell['source'])]
                            result_cell_found = True
                            result["result_cell_added"] = True
                            break

                if not result_cell_found:
                    # Append new result cell
                    new_cell = {
                        'cell_type': 'code',
                        'execution_count': None,
                        'metadata': {
                            'node_id': node_id,
                            'result_cell': True
                        },
                        'outputs': [],
                        'source': result_cell_code.split('\n')
                    }
                    # Add newlines
                    new_cell['source'] = [line + '\n' if i < len(new_cell['source'])-1
                                        else line for i, line in enumerate(new_cell['source'])]
                    notebook['cells'].append(new_cell)
                    result["result_cell_added"] = True

                # Save notebook
                self.nm.save()

            except Exception as e:
                result["error_message"] = f"Failed to generate result cell: {e}"
                result["status"] = "pending_validation"
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()
                return result

            # Step 9: Update node status to validated
            node['execution_status'] = 'validated'
            node['error_message'] = None
            node['last_execution_time'] = datetime.now().isoformat()
            self.pm._save_metadata()

            result["status"] = "success"
            result["execution_time"] = (datetime.now() - start_time).total_seconds()

            return result

        except Exception as e:
            result["error_message"] = f"Unexpected error: {str(e)}"
            result["status"] = "error"
            result["execution_time"] = (datetime.now() - start_time).total_seconds()
            return result
