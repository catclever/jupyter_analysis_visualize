#!/usr/bin/env python3
"""
Jupyter Notebook to Project Generator

This script parses a Jupyter notebook and creates a complete project structure
with three distinct functional components:

═══════════════════════════════════════════════════════════════════════════

ENTRY POINT 1: NotebookMetadataExtractor
  Purpose: Extract node metadata from notebook cells
  Input: Path to .ipynb file
  Output: Dict[str, NodeMetadata]

  Extracts these annotations from code cells:
    - @node_type: (data_source | compute | chart | tool)
    - @node_id: identifier
    - @name: Human-readable name
    - @depends_on: [dep1, dep2]
    - @output_type: (dict_of_dataframes | etc)

  Usage:
    from project_builder import NotebookMetadataExtractor
    extractor = NotebookMetadataExtractor('notebook.ipynb')
    nodes = extractor.extract_nodes()

═══════════════════════════════════════════════════════════════════════════

ENTRY POINT 2: HeaderCommentGenerator
  Purpose: Generate standardized metadata headers for notebook cells
  Input: Notebook dict + Dict[str, NodeMetadata]
  Output: Enhanced notebook with metadata headers

  Generates properly formatted system-managed metadata sections:
    # ===== System-managed metadata (auto-generated, understand to edit) =====
    # @node_type: compute
    # @node_id: my_node
    # @depends_on: [node1, node2]
    # @name: My Node
    # @output_type: dict_of_dataframes (if declared)
    # ===== End of system-managed metadata =====

  Usage:
    from project_builder import HeaderCommentGenerator
    enhanced_nb = HeaderCommentGenerator.add_headers_to_notebook(notebook, nodes)

═══════════════════════════════════════════════════════════════════════════

ENTRY POINT 3: ProjectJsonGenerator
  Purpose: Generate project.json configuration from node metadata
  Input: project_id, Dict[str, NodeMetadata], optional name/description
  Output: Dict representing complete project.json structure

  Creates project configuration with:
    - Node definitions with types and dependencies
    - Result format mapping (data_source→parquet, chart→json, tool→pkl)
    - Execution status tracking (all start as 'not_executed')
    - Declared output types (for dict results, etc)

  Usage:
    from project_builder import ProjectJsonGenerator
    project_json = ProjectJsonGenerator.generate_project_json(
        project_id='my_project',
        nodes=nodes,
        name='My Project',
        description='Project description'
    )

═══════════════════════════════════════════════════════════════════════════

MAIN ORCHESTRATOR: ProjectCreator
  Purpose: Coordinate all three components into a complete workflow
  Entry point for command-line usage

  Workflow:
    1. Extract nodes from notebook (NotebookMetadataExtractor)
    2. Generate headers and enhance notebook (HeaderCommentGenerator)
    3. Generate project.json (ProjectJsonGenerator)
    4. Create project directory and write files

  CLI Usage:
    python3 project_builder.py <path_to_notebook.ipynb>

  Example:
    python3 project_builder.py /path/to/sales_analysis.ipynb

  Output:
    ./sales_analysis/
      ├── project.ipynb   (enhanced notebook with metadata headers)
      └── project.json    (project configuration with DAG structure)

═══════════════════════════════════════════════════════════════════════════
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class NodeMetadata:
    """Represents extracted node metadata"""
    node_id: str
    node_type: str  # 'data_source', 'compute', 'chart', 'tool'
    name: Optional[str] = None
    depends_on: List[str] = None
    declared_output_type: Optional[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class NotebookMetadataExtractor:
    """Step 1: Extract node information from notebook cells"""

    # Regex patterns to detect node declarations
    NODE_TYPE_PATTERN = re.compile(r'#\s*@node_type:\s*(\w+)')
    NODE_ID_PATTERN = re.compile(r'#\s*@node_id:\s*([\w_]+)')
    NODE_NAME_PATTERN = re.compile(r'#\s*@name:\s*(.+)')
    DEPENDS_PATTERN = re.compile(r'#\s*@depends_on:\s*\[(.*?)\]')
    OUTPUT_TYPE_PATTERN = re.compile(r'#\s*@output_type:\s*([\w_]+)')

    def __init__(self, notebook_path: str):
        """Initialize extractor with notebook path"""
        self.notebook_path = Path(notebook_path)
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

        with open(self.notebook_path, 'r', encoding='utf-8') as f:
            self.notebook = json.load(f)

    def extract_nodes(self) -> Dict[str, NodeMetadata]:
        """Extract all node metadata from notebook cells"""
        nodes = {}

        for cell in self.notebook.get('cells', []):
            if cell.get('cell_type') != 'code':
                continue

            source = ''.join(cell.get('source', []))

            # Try to extract node metadata from comments
            node_type_match = self.NODE_TYPE_PATTERN.search(source)
            node_id_match = self.NODE_ID_PATTERN.search(source)

            if not (node_type_match and node_id_match):
                continue

            node_id = node_id_match.group(1)
            node_type = node_type_match.group(1)

            # Extract optional metadata
            name_match = self.NODE_NAME_PATTERN.search(source)
            name = name_match.group(1).strip() if name_match else None

            depends_match = self.DEPENDS_PATTERN.search(source)
            depends_on = []
            if depends_match:
                deps_str = depends_match.group(1)
                depends_on = [d.strip().strip("'\"") for d in deps_str.split(',')]
                depends_on = [d for d in depends_on if d]

            output_type_match = self.OUTPUT_TYPE_PATTERN.search(source)
            declared_output_type = output_type_match.group(1) if output_type_match else None

            nodes[node_id] = NodeMetadata(
                node_id=node_id,
                node_type=node_type,
                name=name,
                depends_on=depends_on,
                declared_output_type=declared_output_type
            )

        return nodes


class HeaderCommentGenerator:
    """Step 2: Generate header comments for cells with node metadata"""

    @staticmethod
    def generate_header(
        node_type: str,
        node_id: str,
        execution_status: str = 'not_executed',
        depends_on: List[str] = None,
        name: Optional[str] = None,
        declared_output_type: Optional[str] = None
    ) -> str:
        """Generate metadata header comment for a code cell"""
        if depends_on is None:
            depends_on = []

        lines = []
        lines.append("# ===== System-managed metadata (auto-generated, understand to edit) =====")
        lines.append(f"# @node_type: {node_type}")
        lines.append(f"# @node_id: {node_id}")

        if execution_status and execution_status != 'not_executed':
            lines.append(f"# @execution_status: {execution_status}")

        if declared_output_type:
            lines.append(f"# @output_type: {declared_output_type}")

        if depends_on:
            depends_str = ', '.join(depends_on)
            lines.append(f"# @depends_on: [{depends_str}]")

        if name:
            lines.append(f"# @name: {name}")

        lines.append("# ===== End of system-managed metadata =====")

        return '\n'.join(lines)

    @staticmethod
    def add_headers_to_notebook(
        notebook: Dict[str, Any],
        nodes: Dict[str, NodeMetadata]
    ) -> Dict[str, Any]:
        """Add header comments to notebook cells"""
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') != 'code':
                continue

            source = ''.join(cell.get('source', []))
            metadata = cell.get('metadata', {})

            # Check if this cell has node metadata
            node_id = metadata.get('node_id')
            if not node_id or node_id not in nodes:
                continue

            node = nodes[node_id]

            # Remove existing header(s) if present
            # This handles both old and new style headers
            code_lines = []
            in_header = False
            for line in source.split('\n'):
                if '# ===== System-managed metadata' in line:
                    in_header = True
                    continue
                elif '# ===== End of system-managed metadata' in line:
                    in_header = False
                    continue
                elif not in_header:
                    code_lines.append(line)

            # Clean code (remove leading empty lines)
            code = '\n'.join(code_lines).lstrip('\n')

            # Generate new header
            header = HeaderCommentGenerator.generate_header(
                node_type=node.node_type,
                node_id=node.node_id,
                depends_on=node.depends_on,
                name=node.name,
                declared_output_type=node.declared_output_type
            )

            # Combine header with code
            new_source = header + '\n' + code

            # Update cell source (format as list of lines with newlines)
            source_lines = new_source.split('\n')
            cell['source'] = [line + '\n' for line in source_lines[:-1]]
            if source_lines[-1]:  # Add last line if non-empty
                cell['source'].append(source_lines[-1])

            # Update metadata
            cell['metadata']['node_type'] = node.node_type
            cell['metadata']['node_id'] = node.node_id
            if node.declared_output_type:
                cell['metadata']['declared_output_type'] = node.declared_output_type
            if node.depends_on:
                cell['metadata']['depends_on'] = node.depends_on
            if node.name:
                cell['metadata']['name'] = node.name

        return notebook


class ProjectJsonGenerator:
    """Step 3: Generate project.json from notebook metadata"""

    @staticmethod
    def generate_project_json(
        project_id: str,
        nodes: Dict[str, NodeMetadata],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate project.json structure"""

        # Map node types to result formats
        result_format_map = {
            'data_source': 'parquet',
            'compute': 'parquet',
            'chart': 'json',
            'tool': 'pkl',
        }

        now = datetime.now(timezone.utc).isoformat()

        project_nodes = []
        for node_id, node in nodes.items():
            result_format = result_format_map.get(node.node_type, 'parquet')

            node_entry = {
                'node_id': node_id,
                'node_type': node.node_type,
                'name': node.name or f"{node.node_type.title()}: {node_id}",
                'type': node.node_type,
                'depends_on': node.depends_on,
                'execution_status': 'not_executed',
                'result_format': result_format,
                'result_path': None,
            }

            # Add declared_output_type if present
            if node.declared_output_type:
                node_entry['declared_output_type'] = node.declared_output_type

            project_nodes.append(node_entry)

        project_json = {
            'project_id': project_id,
            'name': name or f"Project: {project_id}",
            'description': description or "Auto-generated project from notebook",
            'version': '1.0.0',
            'created_at': now,
            'updated_at': now,
            'nodes': project_nodes
        }

        return project_json


class ProjectCreator:
    """Main orchestrator: coordinates all three steps"""

    def __init__(self, notebook_path: str):
        """Initialize with notebook path"""
        self.notebook_path = Path(notebook_path)
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

        # Project directory name (based on notebook filename without extension)
        self.project_name = self.notebook_path.stem
        self.project_dir = self.notebook_path.parent / self.project_name

        # Project ID (lowercase, replace spaces with underscores)
        self.project_id = self.project_name.lower().replace(' ', '_').replace('-', '_')

    def create_project(self) -> Path:
        """
        Execute all three steps:
        1. Extract node metadata from notebook
        2. Generate headers with annotations
        3. Create project.json

        Returns:
            Path to created project directory
        """
        print(f"📋 Starting project creation from: {self.notebook_path}")
        print(f"📁 Project directory: {self.project_dir}")
        print(f"🔑 Project ID: {self.project_id}")
        print()

        # Step 1: Extract nodes from notebook
        print("Step 1: Extracting node metadata from notebook...")
        extractor = NotebookMetadataExtractor(str(self.notebook_path))
        nodes = extractor.extract_nodes()
        print(f"  ✓ Found {len(nodes)} nodes:")
        for node_id, node in nodes.items():
            print(f"    - {node_id}: {node.node_type} ({node.name or 'unnamed'})")
        print()

        # Step 2: Generate headers and enhance notebook
        print("Step 2: Generating metadata headers for notebook cells...")
        with open(self.notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        enhanced_notebook = HeaderCommentGenerator.add_headers_to_notebook(notebook, nodes)
        print(f"  ✓ Enhanced notebook with metadata headers")
        print()

        # Step 3: Generate project.json
        print("Step 3: Generating project.json...")
        project_json = ProjectJsonGenerator.generate_project_json(
            project_id=self.project_id,
            nodes=nodes,
            name=f"Project: {self.project_name}",
            description=f"Auto-generated project from {self.notebook_path.name}"
        )
        print(f"  ✓ Generated project configuration")
        print()

        # Create project directory
        self.project_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created project directory: {self.project_dir}")

        # Write enhanced notebook
        notebook_output_path = self.project_dir / 'project.ipynb'
        with open(notebook_output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_notebook, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote enhanced notebook: {notebook_output_path}")

        # Write project.json
        json_output_path = self.project_dir / 'project.json'
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(project_json, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote project configuration: {json_output_path}")

        print()
        print("=" * 60)
        print(f"✨ Project successfully created: {self.project_dir}")
        print("=" * 60)

        return self.project_dir


def main():
    """Main entry point with support for selecting individual functions"""
    if len(sys.argv) < 2:
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║        Project Builder - Notebook to Project Converter         ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print()
        print("Usage:")
        print("  python3 project_builder.py <notebook.ipynb> [option]")
        print()
        print("Options:")
        print("  (none)        Execute all 3 steps (default)")
        print("  extract       Run only Step 1: Extract metadata")
        print("  headers       Run only Step 2: Generate headers")
        print("  json          Run only Step 3: Generate project.json")
        print("  all           Run all 3 steps (same as no option)")
        print()
        print("Examples:")
        print("  python3 project_builder.py /path/to/notebook.ipynb")
        print("    → Creates: ./notebook/")
        print("       ├── project.ipynb")
        print("       └── project.json")
        print()
        print("  python3 project_builder.py /path/to/notebook.ipynb extract")
        print("    → Only extracts node metadata and prints results")
        print()
        print("  python3 project_builder.py /path/to/notebook.ipynb headers")
        print("    → Generates enhanced notebook with headers in memory")
        print()
        print("  python3 project_builder.py /path/to/notebook.ipynb json")
        print("    → Generates project.json configuration in memory")
        sys.exit(1)

    notebook_path = sys.argv[1]
    option = sys.argv[2].lower() if len(sys.argv) > 2 else 'all'

    # Validate option
    valid_options = {'all', 'extract', 'headers', 'json'}
    if option not in valid_options:
        print(f"❌ Invalid option: '{option}'")
        print(f"   Valid options: {', '.join(sorted(valid_options))}")
        sys.exit(1)

    try:
        # Step 1: Extract metadata (always needed)
        print(f"📋 Starting project builder with option: '{option}'")
        print(f"📄 Notebook: {notebook_path}")
        print()

        print("Step 1: Extracting node metadata from notebook...")
        extractor = NotebookMetadataExtractor(notebook_path)
        nodes = extractor.extract_nodes()
        print(f"  ✓ Found {len(nodes)} nodes:")
        for node_id, node in nodes.items():
            print(f"    - {node_id}: {node.node_type} ({node.name or 'unnamed'})")
            if node.depends_on:
                print(f"      depends_on: {node.depends_on}")
            if node.declared_output_type:
                print(f"      output_type: {node.declared_output_type}")
        print()

        # If only extraction requested
        if option == 'extract':
            print("✨ Extraction complete!")
            return

        # Step 2: Generate headers (for 'headers' and 'all')
        print("Step 2: Generating metadata headers for notebook cells...")
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        enhanced_notebook = HeaderCommentGenerator.add_headers_to_notebook(notebook, nodes)
        print(f"  ✓ Generated headers for {len(nodes)} node cells")
        print()

        # If only headers requested
        if option == 'headers':
            print("✨ Header generation complete!")
            print("   (Enhanced notebook is ready but not written to disk)")
            return

        # Step 3: Generate project.json (for 'json' and 'all')
        print("Step 3: Generating project.json...")
        project_name = Path(notebook_path).stem
        project_id = project_name.lower().replace(' ', '_').replace('-', '_')

        project_json = ProjectJsonGenerator.generate_project_json(
            project_id=project_id,
            nodes=nodes,
            name=f"Project: {project_name}",
            description=f"Auto-generated project from {Path(notebook_path).name}"
        )
        print(f"  ✓ Generated project configuration with {len(project_json['nodes'])} nodes")
        print()

        # If only json requested
        if option == 'json':
            print("✨ Project.json generation complete!")
            print("   (Configuration is ready but not written to disk)")
            return

        # If 'all' - create full project structure
        if option == 'all':
            print("Step 4: Creating project structure...")
            creator = ProjectCreator(notebook_path)
            creator.create_project()
            print()
            print("=" * 60)
            print(f"✨ All steps completed successfully!")
            print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
