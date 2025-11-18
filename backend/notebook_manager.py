"""
Jupyter Notebook Manager

Handles incremental operations on .ipynb files:
- Create new notebook
- Append cells with proper formatting
- Parse existing cells
- Maintain notebook structure
- Track cell execution status
- Link markdown descriptions to code nodes
- Generate result cells from parquet files
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pathlib import Path
from enum import Enum


class ExecutionStatus(Enum):
    """Cell execution status enumeration"""
    NOT_EXECUTED = "not_executed"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"


class NotebookCell:
    """Represents a single cell in a Jupyter notebook"""

    def __init__(
        self,
        cell_type: Literal['code', 'markdown'],
        content: str,
        node_type: Optional[str] = None,
        node_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_status: Optional[str] = None,
        linked_node_id: Optional[str] = None,
    ):
        """
        Create a notebook cell

        Args:
            cell_type: 'code' or 'markdown'
            content: Cell source code/text
            node_type: For code cells - 'data_source', 'compute', 'chart', 'tool', or None
            node_id: For code cells - unique identifier within project
            depends_on: For code cells - list of upstream node_ids
            name: For code cells - human-readable name
            metadata: Additional cell metadata
            execution_status: For code cells - 'not_executed', 'pending_validation', 'validated'
            linked_node_id: For markdown cells - ID of associated node
        """
        self.cell_type = cell_type
        self.content = content
        self.node_type = node_type
        self.node_id = node_id
        self.depends_on = depends_on or []
        self.name = name
        self.metadata = metadata or {}
        self.execution_status = execution_status or ExecutionStatus.NOT_EXECUTED.value
        self.linked_node_id = linked_node_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Jupyter notebook cell format"""
        cell_dict = {
            "cell_type": self.cell_type,
            "metadata": self.metadata.copy(),
            "source": self._format_source(self.content),
            "execution_count": None,
            "outputs": []
        }

        # Add node metadata to cell for parsing
        if self.cell_type == "code" and self.node_type:
            cell_dict["metadata"]["node_type"] = self.node_type
            cell_dict["metadata"]["node_id"] = self.node_id
            cell_dict["metadata"]["execution_status"] = self.execution_status
            if self.depends_on:
                cell_dict["metadata"]["depends_on"] = self.depends_on
            if self.name:
                cell_dict["metadata"]["name"] = self.name

        # Add linked node metadata to markdown cells
        if self.cell_type == "markdown" and self.linked_node_id:
            cell_dict["metadata"]["linked_node_id"] = self.linked_node_id

        return cell_dict

    @staticmethod
    def _format_source(content: str) -> List[str]:
        """Convert content string to Jupyter source format (list of lines)"""
        lines = content.split('\n')
        # Add newline character to each line except the last (unless it's empty)
        result = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                result.append(line + '\n')
            elif line:  # Only add last line if not empty
                result.append(line)
        return result


class NotebookManager:
    """Manager for Jupyter notebook files - handles incremental cell additions"""

    def __init__(self, notebook_path: str):
        """
        Initialize notebook manager

        Args:
            notebook_path: Path to .ipynb file
        """
        self.notebook_path = Path(notebook_path)
        self.notebook = None
        self.loaded = False

        # Load or create notebook
        if self.notebook_path.exists():
            self._load_notebook()
        else:
            self._create_notebook()

    def _create_notebook(self) -> None:
        """Create a new blank Jupyter notebook"""
        self.notebook = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.9.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
        self.loaded = True

    def _load_notebook(self) -> None:
        """Load existing notebook from file"""
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                self.notebook = json.load(f)
            self.loaded = True
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load notebook: {e}")

    def save(self) -> None:
        """Save notebook to file"""
        if not self.loaded or self.notebook is None:
            raise RuntimeError("Notebook not loaded")

        # Ensure parent directory exists
        self.notebook_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.notebook_path, 'w', encoding='utf-8') as f:
            json.dump(self.notebook, f, indent=1, ensure_ascii=False)

    def append_markdown_cell(self, content: str, linked_node_id: Optional[str] = None) -> int:
        """
        Append a markdown cell

        Args:
            content: Markdown content
            linked_node_id: Optional node ID to associate with this markdown cell

        Returns:
            Index of the new cell
        """
        cell = NotebookCell(
            cell_type='markdown',
            content=content,
            linked_node_id=linked_node_id
        )
        return self._append_cell(cell)

    def append_code_cell(
        self,
        code: str,
        node_type: Optional[str] = None,
        node_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        name: Optional[str] = None,
        add_header_comment: bool = True,
        execution_status: Optional[str] = None
    ) -> int:
        """
        Append a code cell with optional node metadata

        Args:
            code: Python code to execute
            node_type: 'data_source', 'compute', 'chart', 'tool', or None
            node_id: Unique node identifier (required if node_type is set)
            depends_on: List of upstream node IDs this depends on
            name: Human-readable name for this node
            add_header_comment: If True, add metadata comments to code
            execution_status: 'not_executed', 'pending_validation', 'validated'

        Returns:
            Index of the new cell
        """
        # Format code with header comments if it's a node
        if node_type and add_header_comment:
            code = self._add_node_header_comment(code, node_type, node_id, depends_on, name, execution_status)

        cell = NotebookCell(
            cell_type='code',
            content=code,
            node_type=node_type,
            node_id=node_id,
            depends_on=depends_on,
            name=name,
            execution_status=execution_status
        )
        return self._append_cell(cell)

    def _append_cell(self, cell: NotebookCell) -> int:
        """
        Append a cell to the notebook

        Args:
            cell: NotebookCell instance

        Returns:
            Index of the new cell
        """
        if not self.loaded or self.notebook is None:
            raise RuntimeError("Notebook not loaded")

        cell_dict = cell.to_dict()
        self.notebook["cells"].append(cell_dict)
        return len(self.notebook["cells"]) - 1

    @staticmethod
    def _add_node_header_comment(
        code: str,
        node_type: str,
        node_id: str,
        depends_on: Optional[List[str]],
        name: Optional[str],
        execution_status: Optional[str] = None
    ) -> str:
        """
        Add header comments to code for node metadata

        System-managed metadata comments are automatically generated and synced with Cell metadata.
        These comments show important node information. Understand them before editing the code.
        The system will automatically sync these with Cell metadata to keep them in sync.

        Args:
            code: Original code
            node_type: Node type
            node_id: Node ID
            depends_on: Upstream dependencies
            name: Node name
            execution_status: Node execution status

        Returns:
            Code with header comments
        """
        lines = []
        lines.append("# ===== System-managed metadata (auto-generated, understand to edit) =====")
        lines.append(f"# @node_type: {node_type}")
        lines.append(f"# @node_id: {node_id}")

        if execution_status:
            lines.append(f"# @execution_status: {execution_status}")

        if depends_on:
            depends_str = ', '.join(depends_on)
            lines.append(f"# @depends_on: [{depends_str}]")

        if name:
            lines.append(f"# @name: {name}")

        lines.append("# ===== End of system-managed metadata =====")
        lines.append("")  # Empty line after metadata
        lines.append(code)

        return '\n'.join(lines)

    def insert_code_cell(
        self,
        index: int,
        code: str,
        node_type: Optional[str] = None,
        node_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        name: Optional[str] = None,
        add_header_comment: bool = True,
        execution_status: Optional[str] = None
    ) -> None:
        """
        Insert a code cell at specific index

        Args:
            index: Position to insert (0-indexed)
            code: Python code
            node_type: Node type (optional)
            node_id: Node ID (optional)
            depends_on: Dependencies (optional)
            name: Node name (optional)
            add_header_comment: Whether to add metadata comments
            execution_status: Execution status (optional)
        """
        if not self.loaded or self.notebook is None:
            raise RuntimeError("Notebook not loaded")

        if node_type and add_header_comment:
            code = self._add_node_header_comment(code, node_type, node_id, depends_on, name, execution_status)

        cell = NotebookCell(
            cell_type='code',
            content=code,
            node_type=node_type,
            node_id=node_id,
            depends_on=depends_on,
            name=name
        )
        self.notebook["cells"].insert(index, cell.to_dict())

    def insert_markdown_cell(self, index: int, content: str) -> None:
        """
        Insert a markdown cell at specific index

        Args:
            index: Position to insert (0-indexed)
            content: Markdown content
        """
        if not self.loaded or self.notebook is None:
            raise RuntimeError("Notebook not loaded")

        cell = NotebookCell(cell_type='markdown', content=content)
        self.notebook["cells"].insert(index, cell.to_dict())

    def get_cell_count(self) -> int:
        """Get total number of cells"""
        if not self.loaded or self.notebook is None:
            return 0
        return len(self.notebook["cells"])

    def get_cell(self, index: int) -> Optional[Dict[str, Any]]:
        """Get cell at specific index"""
        if not self.loaded or self.notebook is None:
            return None

        if 0 <= index < len(self.notebook["cells"]):
            return self.notebook["cells"][index]
        return None

    def get_cells(self) -> List[Dict[str, Any]]:
        """Get all cells"""
        if not self.loaded or self.notebook is None:
            return []
        return self.notebook["cells"]

    def list_code_cells(self) -> List[Dict[str, Any]]:
        """Get all code cells"""
        if not self.loaded or self.notebook is None:
            return []
        return [cell for cell in self.notebook["cells"] if cell["cell_type"] == "code"]

    def list_node_cells(self) -> List[Dict[str, Any]]:
        """Get all cells with node metadata"""
        if not self.loaded or self.notebook is None:
            return []

        node_cells = []
        for cell in self.notebook["cells"]:
            if cell["cell_type"] == "code" and "node_type" in cell["metadata"]:
                node_cells.append(cell)
        return node_cells

    def find_cells_by_node_id(self, node_id: str) -> List[Dict[str, Any]]:
        """Find all cells with specific node_id"""
        if not self.loaded or self.notebook is None:
            return []

        return [
            cell for cell in self.notebook["cells"]
            if cell["cell_type"] == "code" and cell["metadata"].get("node_id") == node_id
        ]

    def find_markdown_cells_by_linked_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Find all markdown cells linked to specific node_id"""
        if not self.loaded or self.notebook is None:
            return []

        return [
            cell for cell in self.notebook["cells"]
            if cell["cell_type"] == "markdown" and cell["metadata"].get("linked_node_id") == node_id
        ]

    def append_result_cell(
        self,
        node_id: str,
        parquet_path: str,
        result_format: str = "parquet",
        description: Optional[str] = None
    ) -> int:
        """
        Append a result cell that displays execution results from file

        The result is stored in a variable with the same name as node_id for clear reference

        Args:
            node_id: ID of the node this result belongs to
            parquet_path: Path to the result file (parquet, json, or image)
            result_format: 'parquet', 'json', 'image', or 'visualization'
            description: Optional description of the result

        Returns:
            Index of the new cell
        """
        # Generate code to load and display results
        # Variable name matches node_id for clarity and downstream usage
        if result_format == "parquet":
            code = f"""# @node_id: {node_id}
# @result_format: parquet
import pandas as pd
import os

# Load result from parquet
result_path = r'{parquet_path}'
if os.path.exists(result_path):
    {node_id} = pd.read_parquet(result_path)
    display({node_id})
else:
    print(f"Result file not found: {{result_path}}")"""
        elif result_format == "json":
            code = f"""# @node_id: {node_id}
# @result_format: json
import json
import os

# Load result from json
result_path = r'{parquet_path}'
if os.path.exists(result_path):
    with open(result_path, 'r') as f:
        {node_id} = json.load(f)
    print(json.dumps({node_id}, indent=2))
else:
    print(f"Result file not found: {{result_path}}")"""
        elif result_format == "image":
            code = f"""# @node_id: {node_id}
# @result_format: image
from IPython.display import Image, display
import os

# Load and display image
image_path = r'{parquet_path}'
if os.path.exists(image_path):
    display(Image(filename=image_path))
else:
    print(f"Image file not found: {{image_path}}")"""
        elif result_format == "visualization":
            code = f"""# @node_id: {node_id}
# @result_format: visualization
import json
import os
from IPython.display import Image, display

# Load visualization (both JSON config and image)
json_path = r'{parquet_path}'
image_path = r'{parquet_path}'.replace('.json', '.png')

# Display image if available
if os.path.exists(image_path):
    display(Image(filename=image_path))
    print(f"Visualization saved at: {{image_path}}")

# Load JSON config if available
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        {node_id} = json.load(f)
    print(f"Visualization config saved at: {{json_path}}")
else:
    print(f"Visualization files not found")"""
        else:
            code = f"""# @node_id: {node_id}
# @result_format: {result_format}
import os

# Load result file
result_path = r'{parquet_path}'
if os.path.exists(result_path):
    print(f"Result file loaded: {{result_path}}")
else:
    print(f"Result file not found: {{result_path}}")"""

        # Create result cell with metadata indicating it's a result display cell
        cell = NotebookCell(
            cell_type='code',
            content=code,
            metadata={
                "result_cell": True,
                "node_id": node_id,
                "parquet_path": parquet_path,
                "result_format": result_format,
                "description": description or f"Result display for {node_id}"
            }
        )
        return self._append_cell(cell)

    def update_execution_status(self, node_id: str, status: str) -> bool:
        """
        Update execution status for a node cell

        Args:
            node_id: Node identifier
            status: 'not_executed', 'pending_validation', 'validated'

        Returns:
            True if updated, False if node not found
        """
        if status not in [ExecutionStatus.NOT_EXECUTED.value,
                         ExecutionStatus.PENDING_VALIDATION.value,
                         ExecutionStatus.VALIDATED.value]:
            raise ValueError(f"Invalid status: {status}")

        for cell in self.notebook["cells"]:
            if (cell["cell_type"] == "code" and
                cell["metadata"].get("node_id") == node_id):
                cell["metadata"]["execution_status"] = status
                return True
        return False

    def list_cells_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all cells with specific execution status

        Args:
            status: 'not_executed', 'pending_validation', 'validated'

        Returns:
            List of cell dicts
        """
        return [
            cell for cell in self.notebook["cells"]
            if (cell["cell_type"] == "code" and
                cell["metadata"].get("execution_status") == status and
                cell["metadata"].get("node_type"))
        ]

    def get_node_with_results(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get node cell and its associated result cells

        Args:
            node_id: Node identifier

        Returns:
            Dict with node and result cells, or None if not found
        """
        node_cells = self.find_cells_by_node_id(node_id)
        if not node_cells:
            return None

        node_cell = node_cells[0]
        result_cells = [
            cell for cell in self.notebook["cells"]
            if (cell["cell_type"] == "code" and
                cell["metadata"].get("result_cell") and
                cell["metadata"].get("node_id") == node_id)
        ]

        return {
            "node": node_cell,
            "results": result_cells,
            "has_results": len(result_cells) > 0
        }

    def validate_metadata_consistency(self) -> Dict[str, Any]:
        """
        Validate that Cell metadata and code comments are in sync

        Checks:
        - Code cells with node_type have proper system-managed comments
        - Metadata in Cell matches metadata in code comments
        - All required metadata fields are present

        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "checked_cells": int,
                "inconsistent_cells": List[Dict]
            }
        """
        if not self.loaded or self.notebook is None:
            return {"valid": False, "errors": ["Notebook not loaded"]}

        errors = []
        warnings = []
        inconsistent_cells = []
        checked_cells = 0

        for idx, cell in enumerate(self.notebook["cells"]):
            if cell["cell_type"] != "code":
                continue

            metadata = cell.get("metadata", {})
            node_type = metadata.get("node_type")

            # Skip non-node cells
            if not node_type:
                continue

            checked_cells += 1
            source_text = "".join(cell.get("source", []))

            # Check for system-managed metadata markers
            has_start_marker = "System-managed metadata (auto-generated, understand to edit)" in source_text
            has_end_marker = "End of system-managed metadata" in source_text

            if not (has_start_marker and has_end_marker):
                warnings.append(
                    f"Cell {idx}: Missing system-managed metadata markers"
                )
                inconsistent_cells.append({
                    "cell_index": idx,
                    "node_id": metadata.get("node_id"),
                    "issue": "missing_markers"
                })

            # Extract metadata from comments
            node_id_from_comment = self._extract_field_from_comments(source_text, "node_id")
            node_type_from_comment = self._extract_field_from_comments(source_text, "node_type")
            status_from_comment = self._extract_field_from_comments(source_text, "execution_status")
            depends_from_comment = self._extract_field_from_comments(source_text, "depends_on")
            name_from_comment = self._extract_field_from_comments(source_text, "name")

            # Validate consistency
            if node_id_from_comment != metadata.get("node_id"):
                errors.append(
                    f"Cell {idx}: node_id mismatch - "
                    f"Comment: {node_id_from_comment}, Metadata: {metadata.get('node_id')}"
                )
                inconsistent_cells.append({
                    "cell_index": idx,
                    "node_id": metadata.get("node_id"),
                    "issue": "node_id_mismatch"
                })

            if node_type_from_comment != node_type:
                errors.append(
                    f"Cell {idx}: node_type mismatch - "
                    f"Comment: {node_type_from_comment}, Metadata: {node_type}"
                )
                inconsistent_cells.append({
                    "cell_index": idx,
                    "node_id": metadata.get("node_id"),
                    "issue": "node_type_mismatch"
                })

            # Check execution_status if present
            if metadata.get("execution_status"):
                if status_from_comment != metadata.get("execution_status"):
                    errors.append(
                        f"Cell {idx}: execution_status mismatch - "
                        f"Comment: {status_from_comment}, Metadata: {metadata.get('execution_status')}"
                    )
                    inconsistent_cells.append({
                        "cell_index": idx,
                        "node_id": metadata.get("node_id"),
                        "issue": "status_mismatch"
                    })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "checked_cells": checked_cells,
            "inconsistent_cells": inconsistent_cells
        }

    @staticmethod
    def _extract_field_from_comments(source_text: str, field_name: str) -> Optional[str]:
        """
        Extract metadata field value from code comments

        Args:
            source_text: Full source code text
            field_name: Field name to extract (e.g., 'node_id', 'node_type')

        Returns:
            Field value or None if not found
        """
        # Match pattern: # @field_name: value
        pattern = rf"#\s*@{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, source_text)
        if match:
            value = match.group(1).strip()
            return value
        return None

    def sync_metadata_comments(self) -> Dict[str, Any]:
        """
        Automatically sync Cell metadata with code comments

        For each node cell:
        1. Check if code comments exist and match Cell metadata
        2. If mismatch or missing, regenerate comments to match Cell metadata
        3. Keep Cell metadata as the source of truth

        Returns:
            Dict with sync results:
            {
                "synced": bool,
                "cells_checked": int,
                "cells_updated": int,
                "updated_cells": List[Dict],
                "errors": List[str]
            }
        """
        if not self.loaded or self.notebook is None:
            return {"synced": False, "cells_checked": 0, "cells_updated": 0, "errors": ["Notebook not loaded"]}

        cells_checked = 0
        cells_updated = 0
        updated_cells = []
        errors = []

        for idx, cell in enumerate(self.notebook["cells"]):
            if cell["cell_type"] != "code":
                continue

            metadata = cell.get("metadata", {})
            node_type = metadata.get("node_type")

            # Skip non-node cells and result cells
            if not node_type or metadata.get("result_cell"):
                continue

            cells_checked += 1
            source_text = "".join(cell.get("source", []))

            # Extract the actual code (after metadata comments)
            actual_code = self._extract_code_after_metadata(source_text)

            # Regenerate header comments from Cell metadata
            new_header = self._generate_header_from_metadata(
                node_type=node_type,
                node_id=metadata.get("node_id"),
                execution_status=metadata.get("execution_status"),
                depends_on=metadata.get("depends_on"),
                name=metadata.get("name")
            )

            # Combine new header with actual code ensuring exactly one newline after header
            new_source = new_header + '\n' + actual_code.lstrip('\n')

            # Check if header needs to be updated (only compare header, ignore code changes)
            current_header_match = re.match(
                r"(#.*?===== End of system-managed metadata =====)",
                source_text,
                re.DOTALL
            )
            current_header = current_header_match.group(1) if current_header_match else ""

            needs_update = current_header != new_header.rstrip('\n')

            if needs_update:
                cells_updated += 1
                # Update cell source using NotebookCell's formatter
                cell["source"] = NotebookCell._format_source(new_source)

                updated_cells.append({
                    "cell_index": idx,
                    "node_id": metadata.get("node_id"),
                    "reason": "metadata_sync"
                })

        return {
            "synced": True,
            "cells_checked": cells_checked,
            "cells_updated": cells_updated,
            "updated_cells": updated_cells,
            "errors": errors
        }

    @staticmethod
    def _extract_code_after_metadata(source_text: str) -> str:
        """
        Extract actual code after system-managed metadata section

        Args:
            source_text: Full source code text

        Returns:
            Code without metadata comments (preserves empty lines)
        """
        # Find the end marker - must include the newline after it
        # Pattern explanation:
        # - #\s*===== End of system-managed metadata ===== : matches the end marker with optional whitespace
        # - \n : matches the newline after the marker
        # - (.*) : captures everything after, including the first newline
        pattern = r"#\s*===== End of system-managed metadata =====\n(.*)"
        match = re.search(pattern, source_text, re.DOTALL)
        if match:
            extracted = match.group(1)
            # Ensure we preserve the code, even if it starts with whitespace
            return extracted
        # If no metadata section, return original text
        return source_text

    @staticmethod
    def _generate_header_from_metadata(
        node_type: str,
        node_id: Optional[str],
        execution_status: Optional[str],
        depends_on: Optional[List[str]],
        name: Optional[str]
    ) -> str:
        """
        Generate header comments from Cell metadata

        Args:
            node_type: Node type
            node_id: Node ID
            execution_status: Execution status
            depends_on: Dependencies
            name: Node name

        Returns:
            Header comment string
        """
        lines = []
        lines.append("# ===== System-managed metadata (auto-generated, understand to edit) =====")
        lines.append(f"# @node_type: {node_type}")
        lines.append(f"# @node_id: {node_id}")

        if execution_status:
            lines.append(f"# @execution_status: {execution_status}")

        if depends_on:
            depends_str = ', '.join(depends_on)
            lines.append(f"# @depends_on: [{depends_str}]")

        if name:
            lines.append(f"# @name: {name}")

        lines.append("# ===== End of system-managed metadata =====")

        return '\n'.join(lines) + '\n'


# Example usage (for testing)
if __name__ == "__main__":
    # Create a new notebook
    manager = NotebookManager("example.ipynb")

    # Add header markdown
    manager.append_markdown_cell("# Data Analysis Project\n\nThis is a test project.")

    # Add data source node
    manager.append_code_cell(
        code="""import pandas as pd

def load_user_data():
    return pd.read_csv('data/users.csv')

data_1 = load_user_data()
print(f"Loaded {len(data_1)} users")""",
        node_type="data_source",
        node_id="data_1",
        name="User Basic Information"
    )

    # Add description markdown
    manager.append_markdown_cell(
        "## Feature Analysis\n\nCross-tabulation between age and income groups"
    )

    # Add compute node
    manager.append_code_cell(
        code="""def analyze_features(data_1, data_2):
    merged = data_1.merge(data_2, on='user_id')
    return merged.groupby(['age_group', 'income_group']).agg({
        'violation': 'mean',
        'count': 'size'
    })

compute_1 = analyze_features(data_1, data_2)
print(compute_1)""",
        node_type="compute",
        node_id="compute_1",
        depends_on=["data_1", "data_2"],
        name="Feature Analysis"
    )

    # Add chart node
    manager.append_code_cell(
        code="""import plotly.graph_objects as go

def create_chart(compute_1):
    fig = go.Figure(data=[
        go.Bar(x=compute_1.index, y=compute_1['violation'])
    ])
    fig.update_layout(title='Violation Rate by Segment')
    return fig

chart_1 = create_chart(compute_1)
chart_1.show()""",
        node_type="chart",
        node_id="chart_1",
        depends_on=["compute_1"],
        name="Age-Income Chart"
    )

    # Add tool node
    manager.append_code_cell(
        code="""def polynomial_features(df):
    df_copy = df.copy()
    df_copy['age_squared'] = df_copy['age'] ** 2
    return df_copy

def create_bins(df):
    df_copy = df.copy()
    df_copy['age_group'] = pd.cut(df_copy['age'], bins=[0, 30, 50, 100])
    return df_copy

def tool_feature_eng(df, operation='polynomial_features'):
    '''Tool entry function'''
    if operation == 'polynomial_features':
        return polynomial_features(df)
    elif operation == 'create_bins':
        return create_bins(df)
    else:
        raise ValueError(f'Unknown operation: {operation}')

# Toolkit loaded in kernel
print("Feature engineering toolkit ready")""",
        node_type="tool",
        node_id="tool_feature_eng",
        name="Feature Engineering Toolkit"
    )

    # Save the notebook
    manager.save()
    print(f"Notebook saved to {manager.notebook_path}")
    print(f"Total cells: {manager.get_cell_count()}")
    print(f"Node cells: {len(manager.list_node_cells())}")
