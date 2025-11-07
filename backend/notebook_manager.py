"""
Jupyter Notebook Manager

Handles incremental operations on .ipynb files:
- Create new notebook
- Append cells with proper formatting
- Parse existing cells
- Maintain notebook structure
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pathlib import Path


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
        """
        self.cell_type = cell_type
        self.content = content
        self.node_type = node_type
        self.node_id = node_id
        self.depends_on = depends_on or []
        self.name = name
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Jupyter notebook cell format"""
        cell_dict = {
            "cell_type": self.cell_type,
            "metadata": self.metadata.copy(),
            "source": self._format_source(self.content),
            "execution_count": None,
            "outputs": []
        }

        # Add node metadata to markdown in cell for parsing
        if self.cell_type == "code" and self.node_type:
            cell_dict["metadata"]["node_type"] = self.node_type
            cell_dict["metadata"]["node_id"] = self.node_id
            if self.depends_on:
                cell_dict["metadata"]["depends_on"] = self.depends_on

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

    def append_markdown_cell(self, content: str) -> int:
        """
        Append a markdown cell

        Args:
            content: Markdown content

        Returns:
            Index of the new cell
        """
        cell = NotebookCell(cell_type='markdown', content=content)
        return self._append_cell(cell)

    def append_code_cell(
        self,
        code: str,
        node_type: Optional[str] = None,
        node_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        name: Optional[str] = None,
        add_header_comment: bool = True
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

        Returns:
            Index of the new cell
        """
        # Format code with header comments if it's a node
        if node_type and add_header_comment:
            code = self._add_node_header_comment(code, node_type, node_id, depends_on, name)

        cell = NotebookCell(
            cell_type='code',
            content=code,
            node_type=node_type,
            node_id=node_id,
            depends_on=depends_on,
            name=name
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
        name: Optional[str]
    ) -> str:
        """
        Add header comments to code for node metadata

        This allows the code to be parsed later to extract node information

        Args:
            code: Original code
            node_type: Node type
            node_id: Node ID
            depends_on: Upstream dependencies
            name: Node name

        Returns:
            Code with header comments
        """
        lines = []
        lines.append(f"# @node_type: {node_type}")
        lines.append(f"# @node_id: {node_id}")

        if depends_on:
            depends_str = ', '.join(depends_on)
            lines.append(f"# @depends_on: [{depends_str}]")

        if name:
            lines.append(f"# @name: {name}")

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
        add_header_comment: bool = True
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
        """
        if not self.loaded or self.notebook is None:
            raise RuntimeError("Notebook not loaded")

        if node_type and add_header_comment:
            code = self._add_node_header_comment(code, node_type, node_id, depends_on, name)

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
