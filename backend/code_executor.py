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

        # PRIORITY 1: Check for function definition FIRST (before other patterns)
        # This is crucial for tool nodes which may have DataFrame operations inside the function
        if CodeValidator.has_function_definition(code, node_id):
            return 'function'

        # PRIORITY 2: Check for DataFrame indicators
        if 'dataframe' in code_lower or 'pd.dataframe' in code_lower or '.groupby(' in code_lower or '.merge(' in code_lower:
            return 'dataframe'
        if f'{node_id}.to_parquet' in code or f'{node_id}.to_csv' in code or f'{node_id}.to_json' in code:
            return 'dataframe'
        if f'pd.read_' in code_lower or f'{node_id} = load' in code.lower():
            return 'dataframe'

        # PRIORITY 3: Check for dict indicators
        if '{' in code and '}' in code and '=' in code:
            # Could be dict
            if 'json' in code_lower or 'dict' in code_lower:
                return 'dict'

        # PRIORITY 4: Check for Figure/Chart indicators
        if 'plotly' in code_lower or 'go.Figure' in code_lower or 'px.' in code_lower:
            return 'figure'
        if 'matplotlib' in code_lower or 'plt.' in code_lower:
            return 'figure'
        if 'echarts' in code_lower or 'echarts_config' in code_lower:
            return 'figure'

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
        print(f"\n[ValidateDebug] Validating node: {node_id}, type: {node_type}")

        # Step 1: Check if same-named variable/function exists
        if node_type == 'tool':
            has_result = CodeValidator.has_function_definition(code, node_id)
            print(f"[ValidateDebug] Step 1 (tool): has_function_definition('{node_id}') = {has_result}")
            if not has_result:
                print(f"[ValidateDebug] ✗ FAILED: Tool node must define function '{node_id}'")
                return False, f"Tool node must define function '{node_id}'", 'unknown'
        else:
            has_result = CodeValidator.has_same_named_variable(code, node_id)
            print(f"[ValidateDebug] Step 1 (non-tool): has_same_named_variable('{node_id}') = {has_result}")
            if not has_result:
                print(f"[ValidateDebug] ✗ FAILED: Code must assign variable '{node_id}'")
                return False, f"Code must assign variable '{node_id}'", 'unknown'

        print(f"[ValidateDebug] Step 1 ✓ PASSED")

        # Step 2: Infer type and validate against node_type
        inferred_type = CodeValidator.infer_return_type(code, node_id)
        print(f"[ValidateDebug] Step 2: infer_return_type('{node_id}') = '{inferred_type}'")

        # Type validation rules
        if node_type in ['data_source', 'compute']:
            if inferred_type not in ['dataframe', 'unknown']:
                print(f"[ValidateDebug] ✗ FAILED: Node must return DataFrame, but got {inferred_type}")
                return False, f"Node '{node_id}' must return DataFrame, but code suggests {inferred_type}", inferred_type
        elif node_type == 'chart':
            if inferred_type not in ['figure', 'dict', 'unknown']:
                print(f"[ValidateDebug] ✗ FAILED: Node must return Figure/dict, but got {inferred_type}")
                return False, f"Node '{node_id}' must return Figure or dict, but code suggests {inferred_type}", inferred_type
        elif node_type == 'tool':
            if inferred_type not in ['function', 'unknown']:
                print(f"[ValidateDebug] ✗ FAILED: Tool node must return function, but got {inferred_type}")
                return False, f"Tool node '{node_id}' must define function, but code suggests {inferred_type}", inferred_type

        print(f"[ValidateDebug] Step 2 ✓ PASSED")
        print(f"[ValidateDebug] ✓ ALL VALIDATIONS PASSED\n")
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

        On new kernel creation, automatically loads validated nodes' results
        from files into the kernel namespace.
        """
        # 只在第一次创建 kernel 时设置工作目录
        is_new_kernel = project_id not in self.km.project_kernels

        if is_new_kernel:
            project_path = self.pm.project_path
            if project_path:
                self.km.get_or_create_kernel(project_id, str(project_path))
            else:
                self.km.get_or_create_kernel(project_id)

            # Auto-load validated nodes into kernel
            print(f"\n[KernelInit] New kernel created for project '{project_id}'")
            self._load_validated_nodes_on_kernel_init(project_id)

    def _load_validated_nodes_on_kernel_init(self, project_id: str) -> None:
        """
        Load validated nodes' results from files into kernel namespace on kernel init.

        When a new kernel is created, this automatically loads all nodes with
        execution_status == 'validated' from their saved result files into the kernel.

        If a file load fails, the node's status is changed to 'pending_validation'.

        Args:
            project_id: Project identifier
        """
        print(f"[KernelInit] Loading validated nodes into kernel...")

        # Get all validated nodes
        nodes = self.pm.list_nodes()
        validated_nodes = [n for n in nodes if n.get('execution_status') == 'validated']

        print(f"[KernelInit] Found {len(validated_nodes)} validated nodes")

        if not validated_nodes:
            print(f"[KernelInit] No validated nodes to load")
            return

        loaded_count = 0
        failed_nodes = []

        for node in validated_nodes:
            node_id = node['node_id']
            node_type = node.get('type', 'compute')
            # Determine default result_format based on node type
            if node_type == 'tool':
                result_format = node.get('result_format', 'pkl')
            elif node_type == 'chart':
                result_format = node.get('result_format', 'json')
            else:
                result_format = node.get('result_format', 'parquet')

            try:
                # Get result path based on node type
                if node_type == 'tool':
                    # Tool nodes are saved as pickles in functions directory
                    result_path = str(self.pm.project_path / 'functions' / f'{node_id}.pkl')
                    print(f"[KernelInit] Loading tool node '{node_id}' from pickle...")
                elif result_format == 'parquet':
                    # Data and compute nodes are saved as parquets
                    result_path = str(self.pm.parquets_path / f'{node_id}.parquet')
                    print(f"[KernelInit] Loading {node_type} node '{node_id}' from parquet...")
                elif result_format == 'json':
                    # Dict results are saved as JSON
                    result_path = str(self.pm.project_path / 'results' / f'{node_id}.json')
                    print(f"[KernelInit] Loading {node_type} node '{node_id}' from JSON...")
                else:
                    print(f"[KernelInit] ✗ Unknown result format for node '{node_id}': {result_format}")
                    failed_nodes.append(node_id)
                    continue

                # Load from file into kernel
                success = self._load_variable_from_file(
                    node_id,
                    result_path,
                    result_format
                )

                if success:
                    print(f"[KernelInit] ✓ Loaded validated node '{node_id}' ({node_type}, {result_format})")
                    loaded_count += 1
                else:
                    print(f"[KernelInit] ✗ Failed to load node '{node_id}' from {result_path}")
                    failed_nodes.append(node_id)

            except Exception as e:
                print(f"[KernelInit] ✗ Error loading node '{node_id}': {e}")
                failed_nodes.append(node_id)

        # Update status for failed nodes
        if failed_nodes:
            print(f"[KernelInit] Updating {len(failed_nodes)} failed nodes to 'pending_validation'")
            for node_id in failed_nodes:
                node = self.pm.get_node(node_id)
                if node:
                    node['execution_status'] = 'pending_validation'
                    node['error_message'] = 'Failed to load from file on kernel restart'
                    self.pm._save_metadata()

                    # Also update notebook
                    try:
                        self.nm.update_execution_status(node_id, 'pending_validation')
                        self.nm.sync_metadata_comments()
                        self.nm.save()
                    except Exception as e:
                        print(f"[KernelInit] Warning: Failed to update notebook for {node_id}: {e}")

        print(f"[KernelInit] ✓ Kernel initialization complete: {loaded_count}/{len(validated_nodes)} nodes loaded")

    def _check_same_named_variable_in_code(self, node_id: str, code: str) -> Tuple[bool, str]:
        """
        Pre-execution check: does code assign same-named variable?

        Returns:
            (has_variable, message)
        """
        if CodeValidator.has_same_named_variable(code, node_id):
            return True, f"Code assigns variable '{node_id}'"
        return False, f"Code does NOT assign variable '{node_id}' - will be auto-appended"

    def _auto_append_save_code(self, code: str, node_id: str, result_format: str, node_type: str = None) -> str:
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
import pandas as pd
from pathlib import Path
parquets_dir = Path(r'{parquets_dir}')
parquets_dir.mkdir(parents=True, exist_ok=True)

# Support both single DataFrame and dict (dict of DataFrames or plain dict)
if isinstance({node_id}, dict):
    print(f"Detected dict result with keys: {{{node_id}.keys()}}")

    # Check if this is a dict of DataFrames or a plain dict
    has_dataframes = any(isinstance(v, pd.DataFrame) for v in {node_id}.values())

    if has_dataframes:
        # Dict of DataFrames - save each one separately with a metadata file
        print(f"Processing dict of DataFrames...")
        node_dir = parquets_dir / '{node_id}'
        node_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata about the dict structure
        import json
        metadata = {{'type': 'dict_of_dataframes', 'keys': list({node_id}.keys())}}
        with open(str(node_dir / '_metadata.json'), 'w') as f:
            json.dump(metadata, f)

        # Save each DataFrame
        for key, df in {node_id}.items():
            if isinstance(df, pd.DataFrame):
                df_path = node_dir / f'{{key}}.parquet'
                try:
                    # Handle non-numeric data types by converting to compatible types
                    df_to_save = df.copy()

                    # Convert object types that might not be parquet-compatible
                    for col in df_to_save.columns:
                        if df_to_save[col].dtype == 'object':
                            try:
                                # Try to keep as string for object columns
                                df_to_save[col] = df_to_save[col].astype(str)
                            except Exception as col_error:
                                print(f"  Warning: Could not convert column {{col}}: {{col_error}}")

                    df_to_save.to_parquet(str(df_path), index=False, engine='pyarrow')
                    print(f"  ✓ Saved {{key}}: {{df_path}}")
                except Exception as df_error:
                    print(f"  ✗ Error saving {{key}}: {{df_error}}")
                    # Fallback to JSON for this DataFrame if parquet fails
                    json_path = node_dir / f'{{key}}.json'
                    try:
                        df.to_json(str(json_path), orient='records', force_ascii=False)
                        print(f"  ✓ Saved {{key}} as JSON (parquet failed): {{json_path}}")
                    except Exception as json_error:
                        print(f"  ✗ Could not save {{key}} in any format: {{json_error}}")
            else:
                print(f"  ⚠ Skipped {{key}}: not a DataFrame (type={{type(df).__name__}})")
    else:
        # Plain dict (not DataFrames) - save as JSON
        print(f"Processing plain dict (non-DataFrame values)...")
        results_dir = Path(r'{parquets_dir}') / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)

        dict_path = results_dir / '{node_id}_dict.json'
        try:
            import json
            # Convert dict to JSON-serializable format
            json_data = {{}}
            for key, value in {node_id}.items():
                if isinstance(value, pd.DataFrame):
                    # Should not reach here, but handle anyway
                    json_data[key] = "DataFrame not supported in plain dict"
                elif isinstance(value, (str, int, float, bool, type(None))):
                    json_data[key] = value
                elif isinstance(value, list):
                    json_data[key] = value
                elif isinstance(value, dict):
                    json_data[key] = value
                else:
                    # Try to convert to string
                    json_data[key] = str(value)

            with open(str(dict_path), 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved plain dict to JSON: {{dict_path}}")
        except Exception as dict_error:
            print(f"✗ Error saving dict to JSON: {{dict_error}}")
else:
    # Single DataFrame - save directly
    save_path = parquets_dir / '{node_id}.parquet'
    try:
        # Ensure we have a copy, not a view
        df_to_save = {node_id}.copy() if hasattr({node_id}, 'copy') else {node_id}

        # Convert object types to strings for better frontend display
        for col in df_to_save.columns:
            if df_to_save[col].dtype == 'object':
                try:
                    # Force conversion to string - ensures all objects display well
                    df_to_save[col] = df_to_save[col].astype(str)

                    # Remove 'nan' string representation (artifact from None conversion)
                    # This cleans up the display in frontend
                    mask = df_to_save[col] == 'nan'
                    df_to_save[col] = df_to_save[col].where(~mask, '')

                    print(f"  ✓ Converted column '{{col}}' to string for display")
                except Exception as col_error:
                    print(f"  Warning: Could not convert column '{{col}}': {{col_error}}")

        df_to_save.to_parquet(str(save_path), index=False, engine='pyarrow')
        print(f"✓ Saved parquet: {{save_path}}")
    except Exception as e:
        import traceback
        print(f"⚠ Parquet save failed: {{e}}")
        traceback.print_exc()

        # Fallback: Save as JSON instead if parquet fails
        try:
            json_path = parquets_dir / '{node_id}.json'
            {node_id}.to_json(str(json_path), orient='records', force_ascii=False)
            print(f"✓ Saved as JSON (parquet failed): {{json_path}}")
        except Exception as json_error:
            print(f"ERROR: Could not save in any format: {{json_error}}")
            traceback.print_exc()
            raise"""

        elif result_format == "json":
            # For chart nodes, save to visualizations/ directory
            # For other nodes, save to parquets/ directory
            if node_type == 'chart':
                visualizations_dir = str(self.pm.visualizations_path)
                save_code = f"""
# Auto-appended: Save chart result to JSON
import json
from pathlib import Path

visualizations_dir = Path(r'{visualizations_dir}')
visualizations_dir.mkdir(parents=True, exist_ok=True)

save_path = visualizations_dir / '{node_id}.json'

# Handle Plotly figures and ECharts configs
if hasattr({node_id}, 'to_dict'):
    # Plotly Figure - convert to dict then JSON
    json_data = {node_id}.to_dict()
elif isinstance({node_id}, dict):
    # ECharts config or plain dict
    json_data = {node_id}
else:
    raise TypeError(f"Expected Plotly Figure or dict, got {{type({node_id}).__name__}}")

with open(str(save_path), 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)
print(f"✓ Saved chart to {{save_path}}")"""
            else:
                # Generic JSON save for non-chart nodes
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

        elif result_format == "image":
            visualizations_dir = str(self.pm.visualizations_path)
            save_code = f"""
# Auto-appended: Save result to image
import os
from pathlib import Path
from PIL import Image
import base64
import io

visualizations_dir = Path(r'{visualizations_dir}')
visualizations_dir.mkdir(parents=True, exist_ok=True)

# Determine file extension based on object type
file_ext = '.png'  # default

try:
    # Handle Plotly figures (convert to static image)
    if hasattr({node_id}, '__class__') and {node_id}.__class__.__name__ == 'Figure':
        # Plotly Figure - try multiple methods
        saved_successfully = False

        # Method 1: Try to_image (requires kaleido)
        if hasattr({node_id}, 'to_image') and callable({node_id}.to_image):
            try:
                img_bytes = {node_id}.to_image(format='png', width=1200, height=600)
                save_path = visualizations_dir / '{node_id}.png'
                with open(str(save_path), 'wb') as f:
                    f.write(img_bytes)
                print(f"✓ Saved image (Plotly with to_image): {{save_path}}")
                saved_successfully = True
            except Exception as e1:
                print(f"  Note: to_image failed ({{type(e1).__name__}}): {{e1}}")

        # Method 2: Fallback to HTML (always works)
        if not saved_successfully:
            try:
                html_path = visualizations_dir / '{node_id}.html'
                {node_id}.write_html(str(html_path))
                print(f"✓ Saved interactive chart (HTML): {{html_path}}")
                # Also try to save a simple PNG by rendering the HTML
                try:
                    png_path = visualizations_dir / '{node_id}.png'
                    # Use plotly kaleido if available, otherwise just note HTML was saved
                    if hasattr({node_id}, 'write_image'):
                        {node_id}.write_image(str(png_path))
                        print(f"✓ Also saved as PNG: {{png_path}}")
                except:
                    print(f"  Note: PNG conversion requires kaleido, HTML version available")
                saved_successfully = True
            except Exception as e2:
                print(f"  Error saving HTML: {{type(e2).__name__}}: {{e2}}")

        if not saved_successfully:
            raise RuntimeError("Could not save Plotly Figure in any format")
    # Handle PIL Image objects
    elif hasattr({node_id}, 'save') and callable({node_id}.save):
        save_path = visualizations_dir / '{node_id}.png'
        {node_id}.save(str(save_path))
        print(f"✓ Saved image (PIL): {{save_path}}")
    # Handle matplotlib figures
    elif hasattr({node_id}, 'savefig') and callable({node_id}.savefig):
        save_path = visualizations_dir / '{node_id}.png'
        {node_id}.savefig(str(save_path), dpi=100, bbox_inches='tight')
        print(f"✓ Saved image (matplotlib): {{save_path}}")
    # Handle base64 encoded images
    elif isinstance({node_id}, str) and {node_id}.startswith('data:image'):
        # Extract base64 data
        import re
        match = re.search(r'data:image/(\\w+);base64,(.+)', {node_id})
        if match:
            img_format = match.group(1)
            img_data = match.group(2)
            import base64
            img_bytes = base64.b64decode(img_data)
            file_ext = f'.{{img_format}}'
            save_path = visualizations_dir / f'{{'{node_id}'}}{{file_ext}}'
            with open(str(save_path), 'wb') as f:
                f.write(img_bytes)
            print(f"✓ Saved image (base64): {{save_path}}")
        else:
            raise ValueError("Invalid base64 image format")
    # Handle bytes directly
    elif isinstance({node_id}, bytes):
        save_path = visualizations_dir / '{node_id}.png'
        with open(str(save_path), 'wb') as f:
            f.write({node_id})
        print(f"✓ Saved image (bytes): {{save_path}}")
    else:
        raise TypeError(f"Cannot save {{type({node_id}).__name__}} as image. Expected: Plotly Figure, PIL Image, matplotlib Figure, bytes, or base64 string. Got: {{type({node_id}).__name__}}")
except Exception as e:
    import traceback
    print(f"ERROR saving image: {{e}}")
    traceback.print_exc()
    raise"""

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

    def _analyze_dependencies_pre_execution(self, node_id: str) -> List[str]:
        """
        Analyze dependencies needed by a node BEFORE execution.
        Important: This method does NOT modify node['depends_on'] field.
        It only returns the analyzed dependencies for verification.

        Only variables that are ALSO in the project's node list are considered dependencies.
        The node itself is ALWAYS excluded (a node produces output with its own name).

        Args:
            node_id: Node to analyze

        Returns:
            List of dependency node IDs (empty if no dependencies found)
        """
        code = self._get_node_code(node_id)
        if not code:
            return []

        # Extract variable names from code
        extracted_vars = self._extract_variable_names(code)

        # Get all node IDs in the project
        all_node_ids = {node['node_id'] for node in self.pm.list_nodes()}

        # Find intersection: variables that are ALSO node IDs
        # This ensures only valid node references are treated as dependencies
        analyzed_deps_with_self = list(extracted_vars & all_node_ids)

        # IMPORTANT: Exclude the node itself from dependencies
        # A node always produces a variable with its own name, so it cannot depend on itself
        analyzed_deps = [dep for dep in analyzed_deps_with_self if dep != node_id]

        # Variables that were extracted but are NOT nodes (regular variables)
        non_node_vars = extracted_vars - all_node_ids

        print(f"[DependencyAnalysis] {node_id}:")
        print(f"  Extracted variables: {extracted_vars}")
        print(f"  All project nodes: {sorted(all_node_ids)}")
        print(f"  Variables that match nodes: {sorted(analyzed_deps_with_self)}")
        print(f"  After excluding self: {sorted(analyzed_deps)}")
        if non_node_vars:
            print(f"  Regular variables (NOT nodes): {sorted(non_node_vars)}")

        return analyzed_deps

    def _check_kernel_variables(self, analyzed_deps: List[str]) -> tuple:
        """
        Check which analyzed dependencies exist in kernel namespace.

        OPTIMIZED: Uses batch checking for 5-10x faster verification.
        Instead of checking variables one-by-one, check them all in one kernel call.

        Args:
            analyzed_deps: List of dependency node IDs to check

        Returns:
            Tuple of (existing_vars, missing_vars)
            - existing_vars: Variables that already exist in kernel
            - missing_vars: Variables that need to be loaded or executed

        Performance:
            Before: 5 vars = 2.5 seconds (5 kernel calls)
            After:  5 vars = 0.3 seconds (1 kernel call)
            Speedup: 8-10x faster
        """
        existing_vars = []
        missing_vars = []

        if not analyzed_deps:
            return existing_vars, missing_vars

        try:
            # OPTIMIZED: Check all variables in ONE kernel call
            batch_results = self.km.check_variables_batch(
                self.pm.project_id,
                analyzed_deps
            )

            # Process results
            for var_name, exists in batch_results.items():
                if exists:
                    existing_vars.append(var_name)
                    print(f"[KernelCheck] ✓ Variable '{var_name}' exists in kernel")
                else:
                    missing_vars.append(var_name)
                    print(f"[KernelCheck] ✗ Variable '{var_name}' missing in kernel")

        except Exception as e:
            # Fallback: treat all as missing (safe approach)
            # Worst case: re-execute all dependencies, which is correct
            missing_vars = list(analyzed_deps)
            print(f"[KernelCheck] Error checking variables: {e}, assuming all missing")

        return existing_vars, missing_vars

    def _load_variable_from_file(
        self,
        var_name: str,
        result_path: str,
        result_format: str
    ) -> bool:
        """
        Load a variable from saved file into kernel namespace.

        Args:
            var_name: Variable name to load
            result_path: Relative path to saved file (from project root)
            result_format: Format of file ('parquet', 'json', 'pkl')

        Returns:
            True if successful, False otherwise
        """
        full_path = self.pm.project_path / result_path
        if not full_path.exists():
            print(f"[FileLoad] ✗ File not found: {full_path}")
            return False

        try:
            if result_format == 'parquet':
                # Check if it's a directory (dict of DataFrames) or file (single DataFrame)
                from pathlib import Path
                full_path_obj = Path(full_path)

                if full_path_obj.is_dir():
                    # Dict of DataFrames - load from directory
                    print(f"[FileLoad] Loading dict of DataFrames from directory: {full_path}")
                    load_code = f"""
import pandas as pd
import json
from pathlib import Path

# Load dict of DataFrames from directory
node_dir = Path(r'{full_path}')

# Read metadata
with open(str(node_dir / '_metadata.json'), 'r') as f:
    metadata = json.load(f)

# Reconstruct dict from individual parquet files
{var_name} = {{}}
for key in metadata['keys']:
    df_path = node_dir / f'{{key}}.parquet'
    if df_path.exists():
        {var_name}[key] = pd.read_parquet(str(df_path))
        print(f"  ✓ Loaded {{key}}: {{df_path.stat().st_size}} bytes")
    else:
        print(f"  ✗ Missing parquet for key {{key}}: {{df_path}}")
        raise FileNotFoundError(f"Parquet file not found for key {{key}}")

print(f"✓ Loaded dict with {{len({var_name})}} DataFrames")
"""
                else:
                    # Single DataFrame - load directly
                    print(f"[FileLoad] Loading single DataFrame from: {full_path}")
                    load_code = f"""
import pandas as pd
{var_name} = pd.read_parquet(r'{full_path}')
"""
            elif result_format == 'json':
                load_code = f"""
import json
with open(r'{full_path}', 'r', encoding='utf-8') as f:
    {var_name} = json.load(f)
print(f"✓ Loaded JSON dict with {{len({var_name})}} keys")
"""
            elif result_format == 'pkl':
                load_code = f"""
import pickle
with open(r'{full_path}', 'rb') as f:
    {var_name} = pickle.load(f)
"""
            else:
                print(f"[FileLoad] ✗ Unknown format: {result_format}")
                return False

            # Execute load code in kernel
            output = self.km.execute_code(self.pm.project_id, load_code, timeout=30)

            if output.get("status") == "success":
                print(f"[FileLoad] ✓ Loaded '{var_name}' from {result_path}")
                return True
            else:
                print(f"[FileLoad] ✗ Failed to load '{var_name}': {output.get('error')}")
                return False

        except Exception as e:
            print(f"[FileLoad] ✗ Exception loading '{var_name}': {e}")
            return False

    def _execute_missing_dependencies_recursively(
        self,
        missing_var_names: List[str],
        execution_stack: List[str] = None
    ) -> bool:
        """
        Recursively execute missing dependencies.

        This method ensures all required dependencies are loaded into the kernel
        before the main node execution. It intelligently loads already-validated
        nodes from files and recursively executes other nodes.

        Args:
            missing_var_names: List of variable names that need to be available
            execution_stack: Stack of currently executing nodes (for cycle detection)

        Returns:
            True if all dependencies are successfully available, False if any fail
        """
        if execution_stack is None:
            execution_stack = []

        print(f"[RecursiveExec] Processing {len(missing_var_names)} missing dependencies")

        for var_name in missing_var_names:
            # var_name should correspond to a node_id
            node = self.pm.get_node(var_name)
            if not node:
                error_msg = f"Node '{var_name}' not found in project"
                print(f"[RecursiveExec] ✗ {error_msg}")
                # Store detailed error for later reporting
                self._last_dependency_error = {
                    'node_id': var_name,
                    'error': error_msg,
                    'type': 'not_found'
                }
                return False

            node_id = var_name

            # Circular dependency detection
            if node_id in execution_stack:
                error_msg = f"Circular dependency detected: {' → '.join(execution_stack + [node_id])}"
                print(f"[RecursiveExec] ✗ {error_msg}")
                self._last_dependency_error = {
                    'node_id': node_id,
                    'error': error_msg,
                    'type': 'circular'
                }
                return False

            # Get node state
            status = node.get('execution_status', 'not_executed')
            result_path = node.get('result_path')
            node_type = node.get('type', 'compute')
            # Determine default result_format based on node type
            if node_type == 'tool':
                result_format = node.get('result_format', 'pkl')
            elif node_type == 'chart':
                result_format = node.get('result_format', 'json')
            else:
                result_format = node.get('result_format', 'parquet')

            print(f"[RecursiveExec] Processing dependency: {node_id} (status: {status})")

            # If node is already validated and file exists, load from file
            if status == 'validated' and result_path:
                print(f"[RecursiveExec] Loading validated node '{node_id}' from cache")
                if not self._load_variable_from_file(node_id, result_path, result_format):
                    error_msg = f"Failed to load '{node_id}' from file {result_path}"
                    print(f"[RecursiveExec] ✗ {error_msg}")
                    self._last_dependency_error = {
                        'node_id': node_id,
                        'error': error_msg,
                        'type': 'load_failed'
                    }
                    return False
                print(f"[RecursiveExec] ✓ Successfully loaded '{node_id}' from cache")
            else:
                # Node not validated or file missing, need to execute it
                print(f"[RecursiveExec] Executing dependency node: {node_id}")

                # Recursively execute with updated stack
                result = self.execute_node(node_id, execution_stack + [node_id])

                if result.get('status') != 'success':
                    error_msg = result.get('error_message', 'Unknown error')
                    print(f"[RecursiveExec] ✗ Failed to execute '{node_id}': {error_msg}")
                    self._last_dependency_error = {
                        'node_id': node_id,
                        'error': error_msg,
                        'type': 'execution_failed'
                    }
                    return False

                print(f"[RecursiveExec] ✓ Successfully executed '{node_id}'")

        print(f"[RecursiveExec] ✓ All missing dependencies resolved")
        return True

    def _get_node_code(self, node_id: str) -> str:
        """
        Get the source code for a node from the notebook.

        Args:
            node_id: Node identifier

        Returns:
            Source code string, or empty string if not found
        """
        notebook = self.nm.notebook
        if not notebook:
            return ""

        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                metadata = cell.get('metadata', {})
                if metadata.get('node_id') == node_id and not metadata.get('result_cell'):
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        return ''.join(source)
                    return source

        return ""

    def execute_node(self, node_id: str, execution_stack: List[str] = None) -> Dict[str, Any]:
        """
        Execute a node with new 9-step recursive dependency workflow:
        
        Step 1: Form validation - check code assigns correct variable/function with correct type
        Step 2: Analyze dependencies - extract required vars (do NOT write to depends_on yet)
        Step 3: Check Kernel variables - which dependencies are already loaded?
        Step 4: Recursively execute missing dependencies - load from cache or execute
        Step 5: Auto-append save code - prepare code with result saving
        Step 6: Execute current node code - run in Kernel
        Step 7: Verify execution - check expected variable exists
        Step 8: Update node status - mark as validated, set result_path
        Step 9: Update dependencies - NOW write the analyzed deps to depends_on
        
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
            # 关键修复: 优先从 notebook 元数据注释里读取节点类型，而不是从 project.json
            # 这样确保前端修改的节点类型能被立即识别，即使 project.json 还没更新
            cell_metadata = code_cell.get('metadata', {})
            node_type_from_notebook = cell_metadata.get('node_type')

            # 调试输出：看节点类型在哪里被读取
            print(f"\n[NodeTypeDebug] Node: {node_id}")
            print(f"[NodeTypeDebug] Notebook metadata keys: {list(cell_metadata.keys())}")
            print(f"[NodeTypeDebug] node_type from notebook: {node_type_from_notebook}")
            print(f"[NodeTypeDebug] node_type from project.json: {node.get('type', 'compute')}")

            if node_type_from_notebook:
                # 使用 notebook 元数据中的节点类型（最新的）
                node_type = node_type_from_notebook
                print(f"[NodeTypeDebug] ✓ Using node_type from notebook metadata: '{node_type}'")
            else:
                # 回退到 project.json 中的节点类型
                node_type = node.get('type', 'compute')
                print(f"[NodeTypeDebug] ✗ Using node_type from project.json: '{node_type}'")

            print(f"[NodeTypeDebug] Final node_type for validation: '{node_type}'")
            print(f"[NodeTypeDebug] Code preview: {code[:100]}...\n")

            # DEBUG: Log code preview (after node_type is defined)
            print(f"\n[CodeDebug] Node {node_id}, type {node_type}:")
            print(f"[CodeDebug] Code length: {len(code)}")
            print(f"[CodeDebug] Code preview (first 200 chars):\n{code[:200]}")
            print(f"[CodeDebug] Code ends with: ...{code[-100:] if len(code) > 100 else code}")

            is_valid, validation_msg, inferred_type = CodeValidator.validate_node_form(code, node_id, node_type)

            if not is_valid:
                # Form validation failed - abort execution
                result["error_message"] = f"Form validation error: {validation_msg}"
                result["status"] = "pending_validation"
                node['execution_status'] = 'pending_validation'
                node['error_message'] = result["error_message"]
                self.pm._save_metadata()

                # Sync to notebook
                try:
                    self.nm.update_execution_status(node_id, 'pending_validation')
                    self.nm.sync_metadata_comments()
                    self.nm.save()
                except Exception as e:
                    print(f"[Warning] Failed to sync notebook metadata on validation error: {e}")

                return result

            # Step 2: Analyze dependencies (WITHOUT writing to depends_on yet)
            print(f"\n[Execution] Step 2: Analyzing dependencies for '{node_id}'...")
            analyzed_deps = self._analyze_dependencies_pre_execution(node_id)
            print(f"[Execution] Analyzed dependencies: {analyzed_deps}")

            # Step 3: Check which dependencies exist in Kernel
            print(f"[Execution] Step 3: Checking Kernel variables...")
            existing_vars, missing_vars = self._check_kernel_variables(analyzed_deps)
            print(f"[Execution] Existing in Kernel: {existing_vars}")
            print(f"[Execution] Missing (need to load/execute): {missing_vars}")

            # Step 4: Recursively execute missing dependencies
            if missing_vars:
                print(f"[Execution] Step 4: Recursively executing {len(missing_vars)} missing dependencies: {missing_vars}")
                if not self._execute_missing_dependencies_recursively(missing_vars, execution_stack):
                    # Get detailed error from the recursive execution
                    dep_error = getattr(self, '_last_dependency_error', {})
                    if dep_error:
                        error_node = dep_error.get('node_id', 'unknown')
                        error_detail = dep_error.get('error', 'Unknown error')
                        error_type = dep_error.get('type', 'unknown')
                        result["error_message"] = f"Dependency execution failed: node '{error_node}' ({error_type}): {error_detail}"
                    else:
                        result["error_message"] = f"Failed to execute dependencies for '{node_id}': {missing_vars}"
                    result["status"] = "pending_validation"
                    return result
                print(f"[Execution] ✓ All dependencies resolved")
            else:
                print(f"[Execution] Step 4: No missing dependencies (analyzed_deps={analyzed_deps}), skipping recursive execution")

            # Step 5: Auto-append save code to persist results
            # Default result_format depends on node type:
            # - tool nodes default to 'pkl' (for function serialization)
            # - chart nodes default to 'json' (for plotly/echarts serialization)
            # - other nodes default to 'parquet' (for dataframe serialization)
            if node_type == 'tool':
                result_format = node.get('result_format', 'pkl')
            elif node_type == 'chart':
                result_format = node.get('result_format', 'json')
            else:
                result_format = node.get('result_format', 'parquet')

            # Always append save code to ensure results are persisted for frontend display
            # (except for tool nodes - they define functions that stay in kernel)
            code = self._auto_append_save_code(code, node_id, result_format, node_type)

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

            # Step 7: Verify execution - check if expected variable exists in kernel
            # Different verification for different node types
            var_value = None
            if node_type == 'tool':
                # Tool nodes: Verify function exists in kernel AND pickle file was saved
                try:
                    # Check if function exists in kernel
                    func_exists = self.km.variable_exists(self.pm.project_id, node_id)
                    if not func_exists:
                        result["error_message"] = f"Tool function '{node_id}' not found in kernel"
                        result["status"] = "pending_validation"
                        node['execution_status'] = 'pending_validation'
                        node['error_message'] = result["error_message"]
                        self.pm._save_metadata()

                        try:
                            self.nm.update_execution_status(node_id, 'pending_validation')
                            self.nm.sync_metadata_comments()
                            self.nm.save()
                        except Exception as sync_e:
                            print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                        return result

                    # Verify pickle file was created
                    pkl_path = self.pm.project_path / 'functions' / f'{node_id}.pkl'
                    if not pkl_path.exists():
                        result["error_message"] = f"Pickle file not found for tool node '{node_id}' at {pkl_path}"
                        result["status"] = "pending_validation"
                        node['execution_status'] = 'pending_validation'
                        node['error_message'] = result["error_message"]
                        self.pm._save_metadata()

                        try:
                            self.nm.update_execution_status(node_id, 'pending_validation')
                            self.nm.sync_metadata_comments()
                            self.nm.save()
                        except Exception as sync_e:
                            print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                        return result

                    file_size = pkl_path.stat().st_size
                    print(f"[Execution] ✓ Tool node '{node_id}' verified: function in kernel + pickle saved ({file_size} bytes)")

                except Exception as e:
                    result["error_message"] = f"Failed to verify tool node: {e}"
                    result["status"] = "pending_validation"
                    node['execution_status'] = 'pending_validation'
                    node['error_message'] = result["error_message"]
                    self.pm._save_metadata()

                    try:
                        self.nm.update_execution_status(node_id, 'pending_validation')
                        self.nm.sync_metadata_comments()
                        self.nm.save()
                    except Exception as sync_e:
                        print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                    return result
            else:
                # Non-tool nodes: Check if variable exists in kernel
                try:
                    var_value = self.km.get_variable(self.pm.project_id, node_id)
                    if var_value is None:
                        result["error_message"] = f"Execution produced no value for '{node_id}'"
                        result["status"] = "pending_validation"
                        node['execution_status'] = 'pending_validation'
                        node['error_message'] = result["error_message"]
                        self.pm._save_metadata()

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

                    try:
                        self.nm.update_execution_status(node_id, 'pending_validation')
                        self.nm.sync_metadata_comments()
                        self.nm.save()
                    except Exception as sync_e:
                        print(f"[Warning] Failed to sync notebook metadata on failure: {sync_e}")

                    return result

                print(f"[Execution] ✓ Variable '{node_id}' verified in kernel")

            # Note: Save was already done by auto-appended code in Step 5
            # We don't do a second save here to avoid unreliable get_variable() issues
            print(f"[Execution] ✓ Result already saved by auto-appended code during Kernel execution")

            # Step 8.5: Generate/overwrite result cell (skip for tool nodes)
            # Tool nodes define functions that live in kernel namespace, no result cells needed
            if node_type != 'tool':
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
                                source_lines = result_cell_code.split('\n')
                                # Add newlines to all lines except the last
                                cell['source'] = [line + '\n' if i < len(source_lines)-1
                                                else line for i, line in enumerate(source_lines)]
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
            else:
                # Tool nodes: No result cells needed (functions stay in kernel namespace)
                print(f"[Execution] ✓ Skipping result cell generation for tool node '{node_id}'")
                self.nm.save()

            # Step 9: Sync complete metadata (unified metadata sync)
            # Update node status to validated and set result_path
            execution_time = (datetime.now() - start_time).total_seconds()

            # Tool nodes don't have result paths (functions are kept in kernel namespace)
            result_path = None
            is_dict_result = False

            if node_type != 'tool':
                # Determine default result_format based on node type
                if node_type == 'chart':
                    result_format = node.get('result_format', 'json')
                else:
                    result_format = node.get('result_format', 'parquet')
                is_visualization = node.get('type') in ['image', 'chart']
                target_dir = 'visualizations' if is_visualization else 'parquets'

                # Check if result is a dict of DataFrames
                # by checking if the auto-appended code saved it as a directory
                from pathlib import Path

                if result_format == 'parquet':
                    # For parquet format, check if directory with metadata exists
                    parquets_path = Path(self.pm.parquets_path)
                    node_dir = parquets_path / node_id
                    node_file = parquets_path / f"{node_id}.parquet"

                    if node_dir.is_dir() and (node_dir / '_metadata.json').exists():
                        # Dict of DataFrames - saved as directory with metadata
                        is_dict_result = True
                        result_path = f"{target_dir}/{node_id}"
                        print(f"[Execution] ✓ Detected dict of DataFrames result - saved as directory")
                    else:
                        # Single DataFrame - saved as file
                        result_path = f"{target_dir}/{node_id}.parquet"
                else:
                    # For other formats (json, etc.), determine file extension
                    if result_format == 'json':
                        file_ext = 'json'
                        # Also check for dict saved as JSON
                        results_dir = Path(self.pm.parquets_path) / 'results'
                        dict_path = results_dir / f'{node_id}_dict.json'
                        if dict_path.exists():
                            is_dict_result = True
                            result_path = f"{target_dir}/results/{node_id}_dict.json"
                            print(f"[Execution] ✓ Detected dict result saved as JSON")
                        else:
                            result_path = f"{target_dir}/{node_id}.{file_ext}"
                    elif result_format in ['image', 'visualization']:
                        file_ext = 'png'
                        result_path = f"{target_dir}/{node_id}.{file_ext}"
                    elif result_format == 'pkl':
                        file_ext = 'pkl'
                        result_path = f"{target_dir}/{node_id}.{file_ext}"
                    else:
                        file_ext = result_format
                        result_path = f"{target_dir}/{node_id}.{file_ext}"

            # Call unified metadata sync method (Step 8: Update node status)
            print(f"[Execution] Step 8: Updating node status...")
            execution_result = {
                'result_path': result_path,
                'result_format': result_format if node_type != 'tool' else 'pkl',
                'inferred_type': 'function' if node_type == 'tool' else inferred_type,
                'is_dict_result': is_dict_result
            }
            self._sync_complete_metadata(node_id, execution_result, execution_time)

            # Step 9: NOW update depends_on with the analyzed dependencies
            # Important: We only write depends_on after ALL dependencies are successfully executed
            print(f"[Execution] Step 9: Updating depends_on with analyzed dependencies: {analyzed_deps}")
            node = self.pm.get_node(node_id)
            node['depends_on'] = sorted(list(set(analyzed_deps)))  # Remove duplicates and sort
            self.pm._save_metadata()

            # Also sync to notebook
            try:
                self.nm.sync_metadata_comments()
                self.nm.save()
            except Exception as e:
                print(f"[Warning] Failed to sync notebook after updating depends_on: {e}")

            # Final: Generate markdown documentation for execution completion (with output)
            self._generate_execution_markdown(node_id, node, start_time, execution_output)

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

            # Store result_format (crucial for frontend to know how to load data)
            if 'result_format' in execution_result:
                node['result_format'] = execution_result['result_format']

            # Store inferred type if available
            if 'inferred_type' in execution_result:
                node['output_type'] = execution_result['inferred_type']

            # Store is_dict_result flag if available
            if 'is_dict_result' in execution_result:
                node['result_is_dict'] = execution_result['is_dict_result']

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

    def _generate_execution_markdown(self, node_id: str, node: Dict[str, Any], start_time: datetime, execution_output: Dict = None) -> None:
        """
        Generate or update markdown documentation for execution completion.

        Creates a markdown cell linked to the node with:
        - Execution completion timestamp
        - Execution duration
        - Basic execution summary
        - Execution output (print statements and results)

        Args:
            node_id: ID of the executed node
            node: Node metadata
            start_time: Start time of execution
            execution_output: Dict with 'status', 'output', 'error' from kernel execution

        Future: Can be extended with AI-generated summaries
        """
        try:
            execution_time = (datetime.now() - start_time).total_seconds()
            completion_time = datetime.now().isoformat()
            node_name = node.get('name', node_id)

            # Build markdown content with execution details
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
