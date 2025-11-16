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

import pandas as pd

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

    @staticmethod
    def extract_function_definitions(code: str) -> Set[str]:
        """
        Extract function names that are defined in code.
        Returns set of function names.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return set()

        functions = set()

        class FunctionVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                functions.add(node.name)
                self.generic_visit(node)

        visitor = FunctionVisitor()
        visitor.visit(tree)
        return functions

    @staticmethod
    def has_function_definition(code: str, func_name: str) -> bool:
        """Check if code defines a function with the given name"""
        functions = CodeValidator.extract_function_definitions(code)
        return func_name in functions

    @staticmethod
    def infer_return_type(code: str, node_id: str) -> str:
        """
        Try to infer the return type of the last expression/assignment.
        This is a static analysis - returns a guess based on code patterns.

        Returns: 'dataframe', 'dict', 'figure', 'function', 'unknown'
        """
        # Look for indicators in the code
        code_lower = code.lower()

        # Check for DataFrame indicators
        if 'dataframe' in code_lower or 'pd.dataframe' in code_lower or '.groupby(' in code_lower or '.merge(' in code_lower:
            return 'dataframe'
        if f'{node_id}.to_parquet' in code or f'{node_id}.to_csv' in code or f'{node_id}.to_json' in code:
            return 'dataframe'
        if f'pd.read_' in code_lower or f'{node_id} = load' in code.lower():
            return 'dataframe'

        # Check for dict indicators
        if '{' in code and '}' in code and '=' in code:
            # Could be dict
            if 'json' in code_lower or 'dict' in code_lower:
                return 'dict'

        # Check for Figure/Chart indicators
        if 'plotly' in code_lower or 'go.Figure' in code_lower or 'px.' in code_lower:
            return 'figure'
        if 'matplotlib' in code_lower or 'plt.' in code_lower:
            return 'figure'
        if 'echarts' in code_lower or 'echarts_config' in code_lower:
            return 'figure'

        # Check for function definition
        if CodeValidator.has_function_definition(code, node_id):
            return 'function'

        return 'unknown'

    @staticmethod
    def validate_node_form(code: str, node_id: str, node_type: str) -> tuple:
        """
        Validate node code form:
        1. Check if required variable/function is assigned
        2. Check if the type matches the node type

        Returns:
            (is_valid, message, inferred_type)
        """
        # Step 1: Check if same-named variable/function exists
        if node_type == 'tool':
            has_result = CodeValidator.has_function_definition(code, node_id)
            if not has_result:
                return False, f"Tool node must define function '{node_id}'", 'unknown'
        else:
            has_result = CodeValidator.has_same_named_variable(code, node_id)
            if not has_result:
                return False, f"Code must assign variable '{node_id}'", 'unknown'

        # Step 2: Infer type and validate against node_type
        inferred_type = CodeValidator.infer_return_type(code, node_id)

        # Type validation rules
        if node_type in ['data_source', 'compute']:
            if inferred_type not in ['dataframe', 'unknown']:
                return False, f"Node '{node_id}' must return DataFrame, but code suggests {inferred_type}", inferred_type
        elif node_type == 'chart':
            if inferred_type not in ['figure', 'dict', 'unknown']:
                return False, f"Node '{node_id}' must return Figure or dict, but code suggests {inferred_type}", inferred_type
        elif node_type == 'tool':
            if inferred_type not in ['function', 'unknown']:
                return False, f"Tool node '{node_id}' must define function, but code suggests {inferred_type}", inferred_type

        return True, "Form validation passed", inferred_type


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

    def _ensure_kernel_with_cwd(self, project_id: str):
        """
        Ensure kernel is created with correct working directory.

        Gets or creates kernel with project directory as working directory.
        This ensures relative file paths in code work correctly.
        """
        # 只在第一次创建 kernel 时设置工作目录
        if project_id not in self.km.project_kernels:
            project_path = self.pm.project_path
            if project_path:
                self.km.get_or_create_kernel(project_id, str(project_path))
            else:
                self.km.get_or_create_kernel(project_id)

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
        Auto-append result-saving code to persist execution results.

        Adds code at the end to:
        1. Save the variable to file (parquet/json/pkl)
        2. Print confirmation

        Uses absolute paths to ensure files are saved to the correct project directory.

        Note: Saves regardless of whether the code already assigns the variable.
        This ensures results are always persisted for display in the frontend.
        """
        # Use absolute paths for parquets directory
        parquets_dir = str(self.pm.parquets_path)

        # Build save code based on result_format
        if result_format == "parquet":
            save_code = f"""

# Auto-appended: Save result to parquet
import os
from pathlib import Path
parquets_dir = Path(r'{parquets_dir}')
parquets_dir.mkdir(parents=True, exist_ok=True)
save_path = parquets_dir / '{node_id}.parquet'
try:
    {node_id}.to_parquet(str(save_path), index=False)
    print(f"✓ Saved parquet: {{save_path}}")
except Exception as e:
    print(f"ERROR saving parquet: {{e}}")
    raise"""

        elif result_format == "json":
            save_code = f"""
# Auto-appended: Save result to JSON
import json
import os
from pathlib import Path
parquets_dir = Path(r'{parquets_dir}')
parquets_dir.mkdir(parents=True, exist_ok=True)
if isinstance({node_id}, dict):
    save_path = parquets_dir / '{node_id}.json'
    with open(str(save_path), 'w', encoding='utf-8') as f:
        json.dump({node_id}, f, indent=2)
else:
    # If it's not a dict, try to convert
    import pandas as pd
    if isinstance({node_id}, pd.DataFrame):
        save_path = parquets_dir / '{node_id}.json'
        {node_id}.to_json(str(save_path), orient='records')
    else:
        save_path = parquets_dir / '{node_id}.json'
        with open(str(save_path), 'w', encoding='utf-8') as f:
            json.dump({node_id}, f, indent=2)
print(f"✓ Saved JSON to {{save_path}}")"""

        elif result_format == "pkl":
            functions_dir = str(self.pm.project_path / 'functions')
            save_code = f"""
# Auto-appended: Save result to pickle
import pickle
from pathlib import Path
functions_dir = Path(r'{functions_dir}')
functions_dir.mkdir(parents=True, exist_ok=True)
save_path = functions_dir / '{node_id}.pkl'
with open(str(save_path), 'wb') as f:
    pickle.dump({node_id}, f)
print(f"✓ Saved pickle to {{save_path}}")"""

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

        # 问题修复: 确保 kernel 使用正确的工作目录
        self._ensure_kernel_with_cwd(self.pm.project_id)

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

            # Step 1: Form validation - check if code assigns correct variable/function with correct type
            node_type = node.get('type', 'compute')
            is_valid, validation_msg, inferred_type = CodeValidator.validate_node_form(code, node_id, node_type)

            if not is_valid:
                # Form validation failed - abort execution
                result["error_message"] = f"Form validation error: {validation_msg}"
                result["status"] = "validation_error"
                node['execution_status'] = 'validation_error'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()

                # Sync to notebook
                try:
                    self.nm.update_execution_status(node_id, 'validation_error')
                    self.nm.sync_metadata_comments()
                    self.nm.save()
                except Exception as e:
                    print(f"[Warning] Failed to sync notebook metadata on validation error: {e}")

                return result

            # Step 2: Auto-append save code to persist results
            result_format = node.get('result_format', 'parquet')

            # Always append save code to ensure results are persisted for frontend display
            code = self._auto_append_save_code(code, node_id, result_format)

            # Step 4-5: Build execution order and execute parents
            execution_order = self._build_execution_order(node_id)

            for exec_node_id in execution_order:
                if exec_node_id == node_id:
                    break  # Don't execute parents that come after

                # Check if this parent is already validated and in kernel
                parent_node = self.pm.get_node(exec_node_id)
                parent_status = parent_node.get('execution_status', 'not_executed')

                # Execute parent if needed - load from result file if exists
                parent_result_format = parent_node.get('result_format', 'parquet')
                parent_result_path = parent_node.get('result_path')

                if parent_result_path:
                    # Try to load the result from file
                    full_path = self.pm.project_path / parent_result_path
                    if full_path.exists():
                        # Load parent result into kernel
                        if parent_result_format == 'parquet':
                            load_code = f"""
import pandas as pd
{exec_node_id} = pd.read_parquet(r'{full_path}')
"""
                        elif parent_result_format == 'json':
                            load_code = f"""
import json
with open(r'{full_path}', 'r', encoding='utf-8') as f:
    {exec_node_id} = json.load(f)
"""
                        elif parent_result_format == 'pkl':
                            load_code = f"""
import pickle
with open(r'{full_path}', 'rb') as f:
    {exec_node_id} = pickle.load(f)
"""
                        else:
                            continue

                        # Execute load code in kernel
                        try:
                            self.km.execute_code(self.pm.project_id, load_code, timeout=30)
                        except Exception as e:
                            result["error_message"] = f"Failed to load parent {exec_node_id}: {str(e)}"
                            result["status"] = "pending_validation"
                            return result

            # Step 6: Execute current node code
            try:
                output = self.km.execute_code(self.pm.project_id, code, timeout=30)
                execution_output = output

                # 问题4修复: 检查Kernel执行结果的状态字段
                # execute_code() 返回字典，不抛出异常，需要检查 status 字段
                if output.get("status") != "success":
                    execution_successful = False
                    error_msg = output.get("error", f"Execution failed with status: {output.get('status')}")
                    # 如果是超时，保留原始错误信息
                    if output.get("status") == "timeout":
                        error_msg = output.get("error", "Execution timeout")
                    result["error_message"] = f"Kernel execution error: {error_msg}"
                    result["status"] = "pending_validation"
                    node['execution_status'] = 'pending_validation'
                    node['error_message'] = result["error_message"]
                    self.pm._save_metadata()

                    # 同步到 notebook (失败时也要同步)
                    try:
                        self.nm.update_execution_status(node_id, 'pending_validation')
                        self.nm.sync_metadata_comments()
                        self.nm.save()
                    except Exception as e:
                        print(f"[Warning] Failed to sync notebook metadata on failure: {e}")

                    return result

                execution_successful = True
            except Exception as e:
                execution_successful = False
                execution_output = str(e)
                result["error_message"] = f"Execution failed: {execution_output}"
                result["status"] = "pending_validation"

                # Update node status to pending_validation
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()

                # 同步到 notebook (失败时也要同步)
                try:
                    self.nm.update_execution_status(node_id, 'pending_validation')
                    self.nm.sync_metadata_comments()
                    self.nm.save()
                except Exception as sync_e:
                    print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

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

                    # 同步到 notebook (失败时也要同步)
                    try:
                        self.nm.update_execution_status(node_id, 'pending_validation')
                        self.nm.sync_metadata_comments()
                        self.nm.save()
                    except Exception as sync_e:
                        print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                    return result
            except Exception as e:
                result["error_message"] = f"Could not verify execution: {e}"
                result["status"] = "pending_validation"
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()

                # 同步到 notebook (失败时也要同步)
                try:
                    self.nm.update_execution_status(node_id, 'pending_validation')
                    self.nm.sync_metadata_comments()
                    self.nm.save()
                except Exception as sync_e:
                    print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                return result

            # Step 7.5: Skip post-check save (already saved by auto-append code in Step 3)
            # 注意: 自动追加的 save 代码已经在 Step 3 中执行并保存了结果文件
            # 这里不再进行二次保存以避免 get_variable() 方法的不可靠性问题
            #
            # 如果保存失败，自动追加的代码会在 Step 3 抛出异常，已被捕获
            print(f"[Execution] ✓ Result already saved by auto-appended code during Kernel execution")

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

            # Step 9: Sync complete metadata (unified metadata sync)
            # Update node status to validated and set result_path
            execution_time = (datetime.now() - start_time).total_seconds()

            result_format = node.get('result_format', 'parquet')
            is_visualization = node.get('type') in ['image', 'chart']
            target_dir = 'visualizations' if is_visualization else 'parquets'

            # Determine file extension based on format
            if result_format == 'parquet':
                file_ext = 'parquet'
            elif result_format == 'json':
                file_ext = 'json'
            elif result_format in ['image', 'visualization']:
                file_ext = 'png'
            elif result_format == 'pkl':
                file_ext = 'pkl'
            else:
                file_ext = result_format

            result_path = f"{target_dir}/{node_id}.{file_ext}"

            # Call unified metadata sync method
            execution_result = {
                'result_path': result_path,
                'inferred_type': inferred_type  # from form validation
            }
            self._sync_complete_metadata(node_id, execution_result, execution_time)

            # Step 9.5: Analyze code and update depends_on (dynamic dependency discovery)
            self._analyze_and_update_dependencies(node_id, code)

            # Step 10: Generate/update markdown documentation for execution completion
            self._generate_execution_markdown(node_id, node, start_time)

            result["status"] = "success"
            result["execution_time"] = (datetime.now() - start_time).total_seconds()

            return result

        except Exception as e:
            result["error_message"] = f"Unexpected error: {str(e)}"
            result["status"] = "error"
            result["execution_time"] = (datetime.now() - start_time).total_seconds()
            return result

    def _analyze_and_update_dependencies(self, node_id: str, code: str) -> None:
        """
        Analyze code to extract variable usage and update depends_on field.

        This implements dynamic dependency discovery:
        1. Extract all variable names used in the code
        2. Check which of them are node IDs
        3. Update the node's depends_on field
        4. This allows the frontend to dynamically display edges based on depends_on

        Args:
            node_id: ID of the node being executed
            code: Source code to analyze
        """
        try:
            # Extract variables used in the code
            used_variables = self._extract_variable_names(code)

            # Get all node IDs to check against
            all_node_ids = set(self.pm.metadata.nodes.keys())

            # Find which used variables correspond to node IDs
            discovered_dependencies = sorted([
                var for var in used_variables
                if var in all_node_ids and var != node_id  # Exclude self-reference
            ])

            # Update the node's depends_on field
            node = self.pm.get_node(node_id)
            if node:
                old_deps = node.get('depends_on', [])
                node['depends_on'] = discovered_dependencies

                # Log if dependencies changed
                if old_deps != discovered_dependencies:
                    print(f"[DependencyAnalysis] {node_id}: {old_deps} → {discovered_dependencies}")

        except Exception as e:
            # Don't fail execution if dependency analysis fails
            print(f"[Warning] Failed to analyze dependencies for {node_id}: {e}")

    def _generate_execution_markdown(self, node_id: str, node: Dict[str, Any], start_time):
        """
        Generate markdown documentation for execution completion.
        This is optional and helps with documentation.
        """
        try:
            execution_time = (datetime.now() - start_time).total_seconds()
            node_type = node.get('type', 'compute')
            status = node.get('execution_status', 'unknown')

            md_content = f"""## Execution Report - {node_id}

**Status**: {status}
**Type**: {node_type}
**Execution Time**: {execution_time:.2f}s
**Timestamp**: {datetime.now().isoformat()}

---
"""
            # Optional: save to a markdown file if needed
            # For now, just log it
            print(f"[ExecutionMarkdown] ✓ Generated markdown for {node_id}")

        except Exception as e:
            print(f"[Warning] Failed to generate markdown for {node_id}: {e}")

    def _sync_complete_metadata(self, node_id: str, execution_result: Dict[str, Any], execution_time: float):
        """
        After successful execution, sync all metadata:
        1. project.json - status, error_message, result_path, execution_time
        2. cell metadata and comments - @execution_status, @error_message, @result_path
        3. markdown documentation (optional)

        This is called after Step 3 (Execution) succeeds and before Step 4 (Dependency generation)
        """
        try:
            node = self.pm.get_node(node_id)
            if not node:
                return

            # Extract result path from execution_result
            result_path = execution_result.get('result_path')

            # Step 1: Update project.json with complete metadata
            node['execution_status'] = 'validated'
            node['error_message'] = None
            if result_path:
                node['result_path'] = result_path
            node['execution_time'] = execution_time
            node['last_execution_time'] = datetime.now().isoformat()

            # Store inferred type if available
            if 'inferred_type' in execution_result:
                node['output_type'] = execution_result['inferred_type']

            # Save project.json
            self.pm._save_metadata()

            # Step 2: Update cell metadata in notebook
            # Find the cell and update its metadata
            notebook = self.nm.notebook
            if notebook:
                for cell in notebook.get('cells', []):
                    if cell.get('cell_type') == 'code':
                        metadata = cell.get('metadata', {})
                        if metadata.get('node_id') == node_id and not metadata.get('result_cell'):
                            # Update cell metadata
                            metadata['execution_status'] = 'validated'
                            metadata['error_message'] = None
                            metadata['execution_time'] = execution_time
                            if result_path:
                                metadata['result_path'] = result_path
                            break

            # Step 3: Sync metadata comments
            # This updates the @execution_status, @error_message, @result_path in cell comments
            self.nm.update_execution_status(node_id, 'validated')
            self.nm.sync_metadata_comments()

            # Step 4: Save notebook
            self.nm.save()

            print(f"[MetadataSync] ✓ Synced all metadata for {node_id}")

        except Exception as e:
            print(f"[Warning] Failed to sync complete metadata for {node_id}: {e}")
            # Don't raise - continue with execution

    @staticmethod
    def _extract_variable_names(code: str) -> Set[str]:
        """
        Extract variable names that are used (referenced) in code.

        Returns a set of variable names that appear in Load context (being referenced).
        Filters out built-in names and common library names.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback: use regex if code has syntax errors
            names = set()
            pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            for match in re.finditer(pattern, code):
                names.add(match.group(1))
            return names

        # Collect all names that are loaded (referenced)
        loaded_names = set()

        class NameVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                # Load context means the variable is being referenced/used
                if isinstance(node.ctx, ast.Load):
                    loaded_names.add(node.id)
                self.generic_visit(node)

        visitor = NameVisitor()
        visitor.visit(tree)

        # Filter out built-in names and common pandas/numpy names
        builtins = {
            'print', 'len', 'range', 'sum', 'min', 'max', 'str', 'int', 'float',
            'list', 'dict', 'set', 'tuple', 'enumerate', 'zip', 'map', 'filter',
            'open', 'read', 'write', 'True', 'False', 'None', 'Exception',
            'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'os', 'sys', 'json', 'pd', 'np', 'plt', 'sns', 'datetime', 'time',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'display', 'sqrt', 'math',
            'mean', 'std', 'var', 'pow', 'abs', 'round', 'sorted', 'reversed',
            'any', 'all', 'iter', 'next', 'callable', 'hasattr', 'getattr',
            'setattr', 'isinstance', 'issubclass', 'type', 'super', 'property',
            'staticmethod', 'classmethod', 'object', 'self', 'cls'
        }

        return loaded_names - builtins

    def _generate_execution_markdown(self, node_id: str, node: Dict[str, Any], start_time: datetime) -> None:
        """
        Generate or update markdown documentation for execution completion.

        Creates a markdown cell linked to the node with:
        - Execution completion timestamp
        - Execution duration
        - Basic execution summary

        Future: Can be extended with AI-generated summaries
        """
        try:
            execution_time = (datetime.now() - start_time).total_seconds()
            completion_time = datetime.now().isoformat()
            node_name = node.get('name', node_id)

            # Generate markdown content with execution details
            markdown_content = f"""## ✓ Execution Complete: {node_name}

**Completed at:** {completion_time}

**Execution time:** {execution_time:.2f}s

**Status:** ✅ Success

---

_Note: This documentation is auto-generated. For detailed AI-powered summaries, please enable summary generation in node settings._"""

            # Find existing markdown cell linked to this node
            existing_cells = self.nm.find_markdown_cells_by_linked_node(node_id)

            if existing_cells:
                # Update existing markdown cell
                for cell in existing_cells:
                    cell['source'] = markdown_content.split('\n')
                    cell['source'] = [line + '\n' if i < len(cell['source'])-1
                                    else line for i, line in enumerate(cell['source'])]
            else:
                # Create new markdown cell linked to this node
                self.nm.append_markdown_cell(
                    markdown_content,
                    linked_node_id=node_id
                )

            # Save notebook
            self.nm.save()

        except Exception as e:
            # Don't fail execution if markdown generation fails
            print(f"Warning: Failed to generate markdown for node {node_id}: {e}")
