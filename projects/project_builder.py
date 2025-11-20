import json
import sys
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import argparse
import shutil # For copying files in deploy mode

# --- NodeMetadata ---
@dataclass
class NodeMetadata:
    """Represents extracted or inferred node metadata"""
    node_id: str
    node_type: str  # 'data_source', 'compute', 'chart', 'tool', 'image'
    name: Optional[str] = None
    depends_on: List[str] = None
    # declared_output_type is not inferred by this script, but kept for consistency if present in comments
    declared_output_type: Optional[str] = None 

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []

# --- Helper Functions for Inference and Comment Handling ---

def _infer_node_id(code: str) -> Optional[str]:
    """
    Infers the node_id from the last assignment in the code,
    ignoring assignments inside loops (for, while) and function/class definitions.
    Returns the target variable name of the last valid assignment.
    """
    try:
        tree = ast.parse(code)
        last_assign_target = None
        
        # We want to find the *last* assignment in top-level scope (or allowed scopes like if/try)
        # We can walk the tree but need to track context.
        # A simpler way for this specific requirement is to iterate top-level nodes
        # and recurse only into allowed structures (If, Try, With).
        
        def find_last_assignment(nodes: List[ast.AST]) -> Optional[str]:
            last_target = None
            for node in nodes:
                if isinstance(node, ast.Assign):
                    # Get the last target of the assignment
                    if node.targets:
                        target = node.targets[-1]
                        if isinstance(target, ast.Name):
                            last_target = target.id
                        elif isinstance(target, (ast.Tuple, ast.List)):
                            # If it's a tuple/list assignment, take the last element
                            if target.elts:
                                last_elt = target.elts[-1]
                                if isinstance(last_elt, ast.Name):
                                    last_target = last_elt.id
                elif isinstance(node, ast.AnnAssign):
                     if isinstance(node.target, ast.Name):
                        last_target = node.target.id
                elif isinstance(node, (ast.If, ast.Try, ast.With, ast.AsyncWith)):
                    # Recurse into blocks that don't create a "loop" scope for our purpose
                    # (though technically they share scope in Python, we treat them as "main flow")
                    # We check all branches and take the very last one found in the entire structure
                    
                    # For If: body and orelse
                    # For Try: body, handlers, orelse, finalbody
                    # For With: body
                    
                    child_nodes = []
                    if isinstance(node, ast.If):
                        child_nodes.extend(node.body)
                        child_nodes.extend(node.orelse)
                    elif isinstance(node, ast.Try):
                        child_nodes.extend(node.body)
                        for handler in node.handlers:
                            child_nodes.extend(handler.body)
                        child_nodes.extend(node.orelse)
                        child_nodes.extend(node.finalbody)
                    elif isinstance(node, (ast.With, ast.AsyncWith)):
                        child_nodes.extend(node.body)
                    
                    # Recursively find in children
                    child_result = find_last_assignment(child_nodes)
                    if child_result:
                        last_target = child_result
                
                # Explicitly IGNORE: ast.For, ast.AsyncFor, ast.While, ast.FunctionDef, ast.ClassDef
                # We do not recurse into them.
            
            return last_target

        last_assign_target = find_last_assignment(tree.body)
        
        if last_assign_target:
            return last_assign_target

        # Fallback: If no assignment found, check if the last top-level statement is a function or class definition
        # This supports "Tool" nodes that are just definitions.
        if tree.body:
            last_node = tree.body[-1]
            if isinstance(last_node, (ast.FunctionDef, ast.ClassDef)):
                return last_node.name

        return None

    except SyntaxError:
        return None # Invalid Python code, cannot parse AST

def _infer_node_type(code: str) -> str:
    """
    Infers the node_type based on keywords/imports in the code.
    """
    code_lower = code.lower()

    # Data Source
    data_source_keywords = ['pd.read_csv', 'pd.read_excel', 'pd.read_sql', 'pd.read_parquet', 'spark.read', 'open(']
    if any(keyword in code_lower for keyword in data_source_keywords):
        return 'data_source'

    # Chart / Image
    chart_keywords = ['plt.figure', 'plt.plot', 'sns.scatterplot', 'go.figure', 'px.line', 'altair.chart']
    image_keywords = ['pil.image', 'image.open', 'matplotlib.figure.figure'] # Matplotlib figure can be image
    if any(keyword in code_lower for keyword in chart_keywords):
        return 'chart'
    if any(keyword in code_lower for keyword in image_keywords):
        return 'image'

    # Tool (if the last top-level statement is a function or class definition)
    try:
        tree = ast.parse(code)
        last_top_level_statement = None
        # Find the last top-level statement
        if tree.body:
            last_top_level_statement = tree.body[-1]

        if isinstance(last_top_level_statement, (ast.FunctionDef, ast.ClassDef)):
            return 'tool'
    except SyntaxError:
        pass # Ignore syntax errors during inference

    # Compute (default)
    return 'compute'

def _format_node_name(node_id: str) -> str:
    """Formats node_id into a human-readable name."""
    return node_id.replace('_', ' ').title()

def _generate_header_comments(node_metadata: NodeMetadata) -> str:
    """Generates the # @... metadata header block for a code cell."""
    lines = []
    lines.append("# ===== System-managed metadata (auto-generated, understand to edit) =====")
    lines.append(f"# @node_type: {node_metadata.node_type}")
    lines.append(f"# @node_id: {node_metadata.node_id}")

    if node_metadata.name:
        lines.append(f"# @name: {node_metadata.name}")

    # depends_on, execution_status, result_format, result_path are not generated by annotate/create initially
    # and are handled by deploy or runtime.
    # The prompt explicitly states depends_on is empty, status is not_executed, result_format/path are None.
    # So, we don't include them in the initial header comments.

    lines.append("# ===== End of system-managed metadata =====")
    return '\n'.join(lines) + '\n' # Ensure a newline after the header

# Regex patterns to detect node declarations in comments
_NODE_TYPE_PATTERN = re.compile(r'#\s*@node_type:\s*(\w+)')
_NODE_ID_PATTERN = re.compile(r'#\s*@node_id:\s*([\w_]+)')
_NODE_NAME_PATTERN = re.compile(r'#\s*@name:\s*(.+)')
_DEPENDS_PATTERN = re.compile(r'#\s*@depends_on:\s*\[(.*?)\]') # Not used for inference, but for parsing existing comments
_OUTPUT_TYPE_PATTERN = re.compile(r'#\s*@output_type:\s*([\w_]+)') # Not used for inference, but for parsing existing comments
_EXECUTION_STATUS_PATTERN = re.compile(r'#\s*@execution_status:\s*(\w+)') # Not used for inference, but for parsing existing comments

def _parse_header_comments(code: str) -> Optional[NodeMetadata]:
    """
    Parses the # @... metadata header block from a code cell.
    Returns NodeMetadata if a valid header is found, otherwise None.
    """
    source_lines = code.split('\n')
    header_lines = []
    in_header = False
    for line in source_lines:
        if '# ===== System-managed metadata' in line:
            in_header = True
            header_lines.append(line)
        elif '# ===== End of system-managed metadata' in line:
            in_header = False
            header_lines.append(line)
            break # Stop after end marker
        elif in_header:
            header_lines.append(line)

    header_text = '\n'.join(header_lines)

    node_type_match = _NODE_TYPE_PATTERN.search(header_text)
    node_id_match = _NODE_ID_PATTERN.search(header_text)

    if not (node_type_match and node_id_match):
        return None # No valid header found

    node_id = node_id_match.group(1)
    node_type = node_type_match.group(1)

    name_match = _NODE_NAME_PATTERN.search(header_text)
    name = name_match.group(1).strip() if name_match else None

    depends_on = []
    depends_match = _DEPENDS_PATTERN.search(header_text)
    if depends_match:
        deps_str = depends_match.group(1)
        depends_on = [d.strip().strip("'\"") for d in deps_str.split(',')]
        depends_on = [d for d in depends_on if d] # Filter out empty strings

    declared_output_type = None
    output_type_match = _OUTPUT_TYPE_PATTERN.search(header_text)
    if output_type_match:
        declared_output_type = output_type_match.group(1)

    return NodeMetadata(
        node_id=node_id,
        node_type=node_type,
        name=name,
        depends_on=depends_on,
        declared_output_type=declared_output_type
    )

def _extract_code_after_header(source_text: str) -> str:
    """
    Extracts the actual code after the system-managed metadata section.
    Preserves leading empty lines of the actual code.
    """
    # Find the end marker and capture everything after it
    pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
    match = re.search(pattern, source_text, re.DOTALL)
    if match:
        return match.group(1)
    return source_text # If no header, return original text

class ProjectBuilder:
    """
    Manages the creation, annotation, and deployment of projects from Jupyter notebooks.
    """
    def __init__(self, input_path: str, output_dir: Optional[str] = None, project_name: Optional[str] = None):
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input notebook not found: {input_path}")

        self.original_notebook_name = self.input_path.stem
        # project_name is only relevant for deploy and create modes
        self.project_name = project_name if project_name else self.original_notebook_name
        self.project_id = self.project_name.lower().replace(' ', '_').replace('-', '_')

        # Determine output_base_dir: if provided, use it; otherwise, use current working directory.
        self.output_base_dir = Path(output_dir) if output_dir else Path.cwd()

        # These will be set more precisely in each mode's method
        self.project_root_dir: Path = Path()
        self.output_notebook_path: Path = Path()

    def _setup_paths_for_mode(self, mode: str) -> None:
        """Sets up self.project_root_dir and self.output_notebook_path based on mode and args."""
        if mode == 'deploy' and self.input_path.name == 'project.ipynb' and not self.output_base_dir.is_absolute():
            # In-place deploy: output_base_dir is not provided, or is relative, and input is project.ipynb
            # This means output_base_dir is effectively the current directory or input_path's parent.
            # We need to ensure project_root_dir is the parent of the input_path.
            self.project_root_dir = self.input_path.parent
            self.output_notebook_path = self.input_path
            print(f"  [Path Setup] In-place deployment detected. Project root: {self.project_root_dir}")
        else:
            # Standard behavior: create a new project directory
            # For annotate mode, project_name is not used for directory naming, it's just original_notebook_name
            dir_name_for_output = self.original_notebook_name if mode == 'annotate' else self.project_name

            # If output_base_dir is a file path, use its parent as the base for the new project dir
            if self.output_base_dir.suffix: # It's a file path
                base_for_new_dir = self.output_base_dir.parent
            else: # It's a directory path
                base_for_new_dir = self.output_base_dir
            
            self.project_root_dir = base_for_new_dir / dir_name_for_output
            self.output_notebook_path = self.project_root_dir / 'project.ipynb'
            print(f"  [Path Setup] Standard deployment/creation. Project root: {self.project_root_dir}")

        self.project_root_dir.mkdir(parents=True, exist_ok=True)
        print(f"  [Path Setup] Output notebook path: {self.output_notebook_path}")


    def _load_notebook(self, path: Path) -> Dict[str, Any]:
        """Loads a Jupyter notebook from the given path."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_notebook(self, notebook: Dict[str, Any], path: Path) -> None:
        """Saves a Jupyter notebook to the given path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, ensure_ascii=False, indent=1) # Use indent=1 for smaller diffs

    def _save_project_json(self, nodes: Dict[str, NodeMetadata], path: Path) -> None:
        """Generates and saves project.json."""
        now = datetime.now(timezone.utc).isoformat()

        project_nodes = []
        for node_id, node in nodes.items():
            # Map node types to result formats for project.json
            result_format_map = {
                'data_source': 'parquet',
                'compute': 'parquet',
                'chart': 'json',
                'image': 'image',
                'tool': 'pkl',
            }
            result_format = result_format_map.get(node.node_type, 'parquet') # Default to parquet

            node_entry = {
                'node_id': node_id,
                'node_type': node.node_type,
                'name': node.name or _format_node_name(node_id),
                'type': node.node_type, # Redundant but present in existing project.json
                'depends_on': [], # Always empty for initial creation/deployment
                'execution_status': 'not_executed',
                'result_format': result_format,
                'result_path': None,
                'error_message': None,
                'last_execution_time': None,
                'position': None # Position is not inferred here
            }
            project_nodes.append(node_entry)

        project_json_content = {
            'project_id': self.project_id,
            'name': self.project_name,
            'description': f"Auto-generated project from {self.input_path.name}",
            'version': '1.0.0',
            'created_at': now,
            'updated_at': now,
            'nodes': project_nodes
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(project_json_content, f, ensure_ascii=False, indent=2)

    def annotate_mode(self) -> None:
        """
        Annotates an input notebook with metadata comments.
        Does not modify cell metadata or create project.json.
        """
        print(f"Running ANNOTATE mode for {self.input_path}")
        # project_name is not used in annotate mode for output directory naming
        # The output directory will be named after the original notebook's stem.
        self._setup_paths_for_mode('annotate')

        original_notebook = self._load_notebook(self.input_path)
        annotated_notebook = original_notebook.copy()
        annotated_notebook['cells'] = [] # Start with empty cells to rebuild

        for i, cell in enumerate(original_notebook.get('cells', [])):
            if cell.get('cell_type') == 'code':
                code = ''.join(cell.get('source', []))
                node_id = _infer_node_id(code)

                if node_id:
                    node_type = _infer_node_type(code)
                    name = _format_node_name(node_id)
                    node_metadata = NodeMetadata(node_id=node_id, node_type=node_type, name=name)
                    header_comments = _generate_header_comments(node_metadata)
                    
                    # Remove existing header comments if any, before adding new ones
                    cleaned_code = _extract_code_after_header(code)
                    new_source = header_comments + cleaned_code
                    
                    new_cell = cell.copy()
                    new_cell['source'] = [line + '\n' for line in new_source.split('\n')[:-1]]
                    if new_source.split('\n')[-1]:
                        new_cell['source'].append(new_source.split('\n')[-1])
                    annotated_notebook['cells'].append(new_cell)
                    print(f"  Annotated code cell {i}: ID='{node_id}', Type='{node_type}', Name='{name}'")
                else:
                    # If node_id cannot be inferred, keep the cell as is without comments
                    annotated_notebook['cells'].append(cell.copy())
                    print(f"  Skipped code cell {i}: No assignable variable found.")
            else:
                # Markdown cells are copied as is, without any metadata generation
                annotated_notebook['cells'].append(cell.copy())
                print(f"  Copied markdown cell {i}")

        self._save_notebook(annotated_notebook, self.output_notebook_path)
        print(f"ANNOTATE mode complete. Annotated notebook saved to: {self.output_notebook_path}")

    def deploy_mode(self) -> None:
        """
        Deploys a project from an annotated notebook.
        Generates project.json and updates cell metadata.
        """
        print(f"Running DEPLOY mode for {self.input_path}")
        self._setup_paths_for_mode('deploy')
        
        project_json_path = self.project_root_dir / 'project.json'
        
        # If not in-place deploy, copy the input notebook to the new project directory
        if self.input_path != self.output_notebook_path:
            print(f"  Copying input notebook from {self.input_path} to {self.output_notebook_path}")
            shutil.copy(self.input_path, self.output_notebook_path)

        notebook = self._load_notebook(self.output_notebook_path)
        deployed_nodes: Dict[str, NodeMetadata] = {}
        
        has_any_node_comments = False

        for i, cell in enumerate(notebook.get('cells', [])):
            if cell.get('cell_type') == 'code':
                code = ''.join(cell.get('source', []))
                node_metadata = _parse_header_comments(code)

                if node_metadata:
                    has_any_node_comments = True
                    deployed_nodes[node_metadata.node_id] = node_metadata
                    # Update cell metadata
                    cell['metadata']['node_type'] = node_metadata.node_type
                    cell['metadata']['node_id'] = node_metadata.node_id
                    if node_metadata.name:
                        cell['metadata']['name'] = node_metadata.name
                    # Other fields like depends_on, execution_status are set by runtime or deploy
                    cell['metadata']['depends_on'] = [] # Initialize as empty
                    cell['metadata']['execution_status'] = 'not_executed'
                    print(f"  Deployed code cell {i}: ID='{node_metadata.node_id}', Type='{node_metadata.node_type}'")
                else:
                    # Ensure non-node code cells don't have node metadata
                    if 'node_id' in cell['metadata']: del cell['metadata']['node_id']
                    if 'node_type' in cell['metadata']: del cell['metadata']['node_type']
                    if 'name' in cell['metadata']: del cell['metadata']['name']
                    if 'depends_on' in cell['metadata']: del cell['metadata']['depends_on']
                    if 'execution_status' in cell['metadata']: del cell['metadata']['execution_status']
                    print(f"  Skipped non-annotated code cell {i}")
            else:
                # Markdown cells are copied as is, ensure no node metadata
                if 'node_id' in cell['metadata']: del cell['metadata']['node_id']
                if 'node_type' in cell['metadata']: del cell['metadata']['node_type']
                print(f"  Copied markdown cell {i}")

        if not has_any_node_comments:
            print("DEPLOY mode skipped: No node metadata comments found in the input notebook.")
            return

        # Save the notebook with updated cell metadata
        self._save_notebook(notebook, self.output_notebook_path)
        print(f"  Notebook with updated cell metadata saved to: {self.output_notebook_path}")

        # Generate and save project.json
        self._save_project_json(deployed_nodes, project_json_path)
        print(f"  Project.json generated and saved to: {project_json_path}")
        
        print(f"DEPLOY mode complete. Project deployed to: {self.project_root_dir}")

    def create_mode(self) -> None:
        """
        Combines annotate and deploy steps into a single operation.
        """
        print(f"Running CREATE mode for {self.input_path}")
        self._setup_paths_for_mode('create')
        
        project_json_path = self.project_root_dir / 'project.json'

        original_notebook = self._load_notebook(self.input_path)
        created_notebook = original_notebook.copy()
        created_notebook['cells'] = [] # Start with empty cells to rebuild

        inferred_nodes: Dict[str, NodeMetadata] = {}

        for i, cell in enumerate(original_notebook.get('cells', [])):
            if cell.get('cell_type') == 'code':
                code = ''.join(cell.get('source', []))
                node_id = _infer_node_id(code)

                if node_id:
                    node_type = _infer_node_type(code)
                    name = _format_node_name(node_id)
                    node_metadata = NodeMetadata(node_id=node_id, node_type=node_type, name=name)
                    inferred_nodes[node_id] = node_metadata

                    # Add header comments
                    header_comments = _generate_header_comments(node_metadata)
                    cleaned_code = _extract_code_after_header(code)
                    new_source = header_comments + cleaned_code
                    
                    new_cell = cell.copy()
                    new_cell['source'] = [line + '\n' for line in new_source.split('\n')[:-1]]
                    if new_source.split('\n')[-1]:
                        new_cell['source'].append(new_source.split('\n')[-1])

                    # Update cell metadata directly
                    new_cell['metadata']['node_type'] = node_metadata.node_type
                    new_cell['metadata']['node_id'] = node_metadata.node_id
                    if node_metadata.name:
                        new_cell['metadata']['name'] = node_metadata.name
                    new_cell['metadata']['depends_on'] = []
                    new_cell['metadata']['execution_status'] = 'not_executed'

                    created_notebook['cells'].append(new_cell)
                    print(f"  Created code cell {i}: ID='{node_id}', Type='{node_type}', Name='{name}'")
                else:
                    # If node_id cannot be inferred, keep the cell as is without comments or metadata
                    if 'node_id' in cell['metadata']: del cell['metadata']['node_id']
                    if 'node_type' in cell['metadata']: del cell['metadata']['node_type']
                    if 'name' in cell['metadata']: del cell['metadata']['name']
                    if 'depends_on' in cell['metadata']: del cell['metadata']['depends_on']
                    if 'execution_status' in cell['metadata']: del cell['metadata']['execution_status']
                    created_notebook['cells'].append(cell.copy())
                    print(f"  Skipped code cell {i}: No assignable variable found.")
            else:
                # Markdown cells are copied as is, ensure no node metadata
                if 'node_id' in cell['metadata']: del cell['metadata']['node_id']
                if 'node_type' in cell['metadata']: del cell['metadata']['node_type']
                created_notebook['cells'].append(cell.copy())
                print(f"  Copied markdown cell {i}")

        # Save the notebook
        self._save_notebook(created_notebook, self.output_notebook_path)
        print(f"  Notebook with annotations and metadata saved to: {self.output_notebook_path}")

        # Generate and save project.json
        self._save_project_json(inferred_nodes, project_json_path)
        print(f"  Project.json generated and saved to: {project_json_path}")

        print(f"CREATE mode complete. Project created at: {self.project_root_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Jupyter Notebook to Project Generator. Modes: annotate, deploy, create."
    )
    parser.add_argument(
        "mode",
        choices=["annotate", "deploy", "create"],
        help="Operation mode: 'annotate' (add comments), 'deploy' (build from comments), 'create' (do both)."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input Jupyter notebook (.ipynb) file."
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Optional: Directory for the output project. Defaults to current directory. "
             "For 'annotate' and 'create', if not provided, a new directory named after the project will be created. "
             "For 'deploy', if input is 'project.ipynb' and output-dir is not provided, it will modify in-place."
    )
    parser.add_argument(
        "--project-name",
        "-n",
        help="Optional: Name of the new project. Defaults to the input notebook's filename (without extension). "
             "Note: This parameter is ignored in 'annotate' mode as it only generates comments, not a full project."
    )

    args = parser.parse_args()

    try:
        builder = ProjectBuilder(
            input_path=args.input,
            output_dir=args.output_dir,
            project_name=args.project_name if args.mode != 'annotate' else None # Pass project_name only if not annotate mode
        )

        if args.mode == "annotate":
            builder.annotate_mode()
        elif args.mode == "deploy":
            builder.deploy_mode()
        elif args.mode == "create":
            builder.create_mode()

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()