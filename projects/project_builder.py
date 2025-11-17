import json
import os
import re
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple

class ProjectBuilder:
    """
    A tool to convert a standard Jupyter Notebook into a structured data analysis project.
    """

    def _infer_node_type(self, source_code: str) -> str:
        """
        Infers the node type based on the cell's source code.
        Priority: chart > tool > data_source > compute
        """
        if re.search(r"import\s+plotly|import\s+matplotlib|px\.|go\.", source_code):
            return "chart"
        if re.search(r"^\s*def\s+", source_code, re.MULTILINE):
            return "tool"
        if re.search(r"pd\.read_csv|pd\.read_excel|pd\.read_sql", source_code):
            return "data_source"
        return "compute"

    def _get_result_format(self, node_type: str) -> str | None:
        """
        Gets the result format based on the node type.
        """
        if node_type == "chart":
            return "json"
        if node_type in ["data_source", "compute"]:
            return "parquet"
        return None

    def _slugify(self, text: str) -> str:
        """
        Creates a simple, safe slug from a string.
        """
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'[^\w-]', '', text)
        return text.lower().strip('_')

    def annotate_notebook(self, notebook_path: Path):
        """
        Reads a notebook, adds metadata comments to each code cell, and saves it in place.
        This method ONLY adds comments to the source code, it does NOT update cell metadata.

        Args:
            notebook_path: Path to the project.ipynb file to be annotated.
        """
        print(f"Annotating notebook: {notebook_path}")
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
        except FileNotFoundError:
            print(f"Error: Input file not found at {notebook_path}")
            return

        cell_count = 0
        modified = False
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code" and cell.get("source"):
                cell_count += 1
                source_str = "".join(cell["source"])

                # Check if metadata block is already present
                if "# ===== System-managed metadata" in source_str:
                    print(f"  - Skipping already annotated cell {cell_count}")
                    continue

                modified = True
                node_type = self._infer_node_type(source_str)
                
                first_line = source_str.splitlines()[0].strip() if source_str.splitlines() else ""
                if first_line.startswith("#"):
                    name = first_line.lstrip('# ').strip()
                else:
                    name = f"Cell {cell_count}: {node_type.capitalize()}"

                node_id = self._slugify(name) or f"node_{cell_count}"

                metadata_comment = (
                    "# ===== System-managed metadata (auto-generated, understand to edit) =====\n"
                    f"# @node_type: {node_type}\n"
                    f"# @node_id: {node_id}\n"
                    "# @execution_status: not_executed\n"
                    "# @depends_on: []\n"
                    f"# @name: {name}\n"
                    "# ===== End of system-managed metadata =====\n"
                )
                
                original_source = cell["source"]
                cell["source"] = [metadata_comment] + ["\n"] + original_source
                
                print(f"  - Added annotation to cell {cell_count} as node '{node_id}' (type: {node_type})")

        if modified:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=2)
            print(f"Successfully saved annotated notebook: {notebook_path}")
        else:
            print("No new annotations added.")

    def generate_project_json(self, notebook_path: Path, project_json_path: Path):
        """
        Generates a project.json file and updates notebook metadata in place.
        This method reads annotations from source, updates cell metadata, and then generates project.json.

        Args:
            notebook_path: Path to the annotated project.ipynb file.
            project_json_path: Path to save the project.json file.
        """
        print(f"Generating project.json from: {notebook_path}")
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
        except FileNotFoundError:
            print(f"Error: Annotated notebook not found at {notebook_path}")
            return

        project_id = project_json_path.parent.name
        current_time = datetime.now().isoformat()

        project_data = {
            "project_id": project_id,
            "name": f"{project_id.replace('_', ' ').title()} Project",
            "description": "Auto-generated project from notebook.",
            "version": "1.0.0",
            "created_at": current_time,
            "updated_at": current_time,
            "notebook_path": notebook_path.name,
            "nodes": [], 
            "dag_metadata": {},
            "analysis_paths": []
        }

        nodes_list = []
        node_types_count = {}
        notebook_modified_for_metadata = False

        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code" and cell.get("source"):
                source_str = "".join(cell["source"])
                
                node_id_match = re.search(r"# @node_id: (\S+)", source_str)
                node_type_match = re.search(r"# @node_type: (\S+)", source_str)
                name_match = re.search(r"# @name: (.+)", source_str)

                if node_id_match and node_type_match and name_match:
                    node_id = node_id_match.group(1)
                    node_type = node_type_match.group(1)
                    name = name_match.group(1).strip()
                    
                    node_obj = {
                        "node_id": node_id,
                        "node_type": node_type,
                        "name": name,
                        "depends_on": [], 
                        "execution_status": "not_executed",
                        "result_format": self._get_result_format(node_type),
                        "result_path": None
                    }
                    nodes_list.append(node_obj)
                    node_types_count[node_type] = node_types_count.get(node_type, 0) + 1
                    print(f"  - Processed node '{node_id}' (type: {node_type}) for project.json")

                    # Update cell metadata in the notebook object if it's different or missing
                    current_metadata = cell.get("metadata", {})
                    expected_metadata = {
                        "node_id": node_id,
                        "node_type": node_type,
                        "name": name,
                        "depends_on": [],
                        "execution_status": "not_executed"
                    }
                    if not all(current_metadata.get(k) == v for k, v in expected_metadata.items()):
                        cell["metadata"].update(expected_metadata)
                        notebook_modified_for_metadata = True
                        print(f"  - Updated metadata for cell '{node_id}' in notebook.")

        project_data["nodes"] = nodes_list
        project_data["dag_metadata"] = {
            "total_nodes": len(nodes_list),
            "node_types": node_types_count,
            "max_depth": 0,
            "has_cycles": False
        }

        if notebook_modified_for_metadata:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=2)
            print(f"Successfully updated notebook metadata in: {notebook_path}")
        else:
            print(f"Notebook metadata already up-to-date for: {notebook_path}")

        with open(project_json_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2)
        print(f"Successfully generated project.json at: {project_json_path}")

def setup_project_paths(input_notebook: str) -> Tuple[Path, Path]:
    """
    Determines project paths based on the input notebook.
    If it's a standalone notebook, creates a project directory.
    Returns the final paths for the project notebook and project.json.
    """
    input_path = Path(input_notebook).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input notebook not found: {input_path}")

    if input_path.name == "project.ipynb":
        print("Detected existing project structure.")
        project_dir = input_path.parent
        notebook_path = input_path
    else:
        print("Detected standalone notebook. Creating new project structure...")
        project_dir = input_path.parent / input_path.stem
        project_dir.mkdir(exist_ok=True)
        notebook_path = project_dir / "project.ipynb"
        
        # Only copy if the target project.ipynb doesn't exist or is not the same file as input
        if not notebook_path.exists() or not input_path.samefile(notebook_path):
            shutil.copy2(input_path, notebook_path)
            print(f"Copied '{input_path.name}' to '{notebook_path}'")
        else:
            print(f"Using existing project.ipynb at '{notebook_path}'")

    json_path = project_dir / "project.json"
    return notebook_path, json_path

def main():
    parser = argparse.ArgumentParser(description="Build a structured project from a Jupyter Notebook.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    parser_create = subparsers.add_parser("create", help="Create a full project from a raw notebook.")
    parser_create.add_argument("input_notebook", type=str, help="Path to the raw .ipynb file.")

    parser_annotate = subparsers.add_parser("annotate", help="Annotate a notebook with metadata comments.")
    parser_annotate.add_argument("input_notebook", type=str, help="Path to the raw or project .ipynb file.")

    parser_generate = subparsers.add_parser("generate", help="Generate project.json and update notebook metadata from annotations.")
    parser_generate.add_argument("input_notebook", type=str, help="Path to the annotated .ipynb file.")

    args = parser.parse_args()
    builder = ProjectBuilder()

    try:
        notebook_path, json_path = setup_project_paths(args.input_notebook)

        if args.command == "create":
            print("\n--- Running Annotation Step ---")
            builder.annotate_notebook(notebook_path)
            print("\n--- Running Generation Step ---")
            builder.generate_project_json(notebook_path, json_path)
            print("\nProject creation complete.")

        elif args.command == "annotate":
            builder.annotate_notebook(notebook_path)
            print("\nAnnotation complete.")

        elif args.command == "generate":
            builder.generate_project_json(notebook_path, json_path)
            print("\nProject JSON generation and notebook metadata update complete.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()