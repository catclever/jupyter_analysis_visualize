"""
Project Metadata Parser

Parses Jupyter notebook structure and extracts node metadata.
Handles:
- Cell parsing and node metadata extraction
- DAG construction from dependencies
- Notebook structure validation
- Node information collection
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from dependency_inferencer import DependencyInferencer


class MetadataParseError(Exception):
    """Raised when metadata parsing fails"""
    pass


class CellMetadata:
    """Extracted metadata from a single cell"""

    def __init__(self, cell_index: int, cell_type: str):
        """
        Initialize cell metadata

        Args:
            cell_index: Index of cell in notebook
            cell_type: Type of cell (code or markdown)
        """
        self.cell_index = cell_index
        self.cell_type = cell_type
        self.node_id: Optional[str] = None
        self.node_type: Optional[str] = None
        self.node_name: Optional[str] = None
        self.depends_on: List[str] = []
        self.content = ""
        self.is_node = False
        # New fields for optimization
        self.execution_status: Optional[str] = None  # 'not_executed', 'pending_validation', 'validated'
        self.is_result_cell = False
        self.result_format: Optional[str] = None  # 'parquet', 'json', 'image', 'visualization'
        self.parquet_path: Optional[str] = None
        self.linked_node_id: Optional[str] = None  # For markdown cells linked to code nodes
        self.declared_output_type: Optional[str] = None  # 'dataframe', 'dict_of_dataframes', 'chart', etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "cell_index": self.cell_index,
            "cell_type": self.cell_type,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "node_name": self.node_name,
            "depends_on": self.depends_on,
            "is_node": self.is_node,
            "content_length": len(self.content)
        }

        # Add optimization-related fields if present
        if self.execution_status:
            result["execution_status"] = self.execution_status
        if self.is_result_cell:
            result["is_result_cell"] = True
            result["result_format"] = self.result_format
            result["parquet_path"] = self.parquet_path
        if self.linked_node_id:
            result["linked_node_id"] = self.linked_node_id

        return result


class NotebookMetadata:
    """Extracted metadata from entire notebook"""

    def __init__(self, notebook_path: str):
        """
        Initialize notebook metadata

        Args:
            notebook_path: Path to .ipynb file
        """
        self.notebook_path = Path(notebook_path)
        self.cells: List[CellMetadata] = []
        self.node_cells: List[CellMetadata] = []
        self.dag_nodes: List[str] = []
        self.dag_edges: List[Tuple[str, str]] = []
        self.errors: List[str] = []

    @property
    def total_cells(self) -> int:
        """Get total number of cells"""
        return len(self.cells)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "notebook_path": str(self.notebook_path),
            "total_cells": len(self.cells),
            "node_cells": len(self.node_cells),
            "nodes": [cell.to_dict() for cell in self.node_cells],
            "dag_nodes": self.dag_nodes,
            "dag_edges": self.dag_edges,
            "errors": self.errors
        }


class ProjectMetadataParser:
    """Parses notebook and extracts project structure"""

    # Regex patterns for extracting metadata from comments
    NODE_TYPE_PATTERN = re.compile(r'#\s*@node_type:\s*(\w+)')
    NODE_ID_PATTERN = re.compile(r'#\s*@node_id:\s*([\w_]+)')
    NODE_NAME_PATTERN = re.compile(r'#\s*@name:\s*(.+)')
    DEPENDS_PATTERN = re.compile(r'#\s*@depends_on:\s*\[(.*?)\]')
    # New patterns for optimization
    EXECUTION_STATUS_PATTERN = re.compile(r'#\s*@execution_status:\s*(\w+)')
    RESULT_FORMAT_PATTERN = re.compile(r'#\s*@result_format:\s*(\w+)')
    # Pattern for declared output type (e.g., @output_type: dict_of_dataframes)
    OUTPUT_TYPE_PATTERN = re.compile(r'#\s*@output_type:\s*([\w_]+)')

    def __init__(self, notebook_path: str):
        """
        Initialize parser

        Args:
            notebook_path: Path to .ipynb file
        """
        self.notebook_path = Path(notebook_path)
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    def parse(self) -> NotebookMetadata:
        """
        Parse notebook and extract metadata

        Returns:
            NotebookMetadata with extracted information

        Raises:
            MetadataParseError: If notebook is invalid
        """
        import json

        metadata = NotebookMetadata(str(self.notebook_path))

        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
        except json.JSONDecodeError as e:
            raise MetadataParseError(f"Invalid notebook JSON: {e}")
        except Exception as e:
            raise MetadataParseError(f"Error reading notebook: {e}")

        # Parse cells
        cells = notebook.get('cells', [])
        for cell_index, cell in enumerate(cells):
            cell_meta = self._parse_cell(cell_index, cell)
            metadata.cells.append(cell_meta)

            if cell_meta.is_node:
                metadata.node_cells.append(cell_meta)
                metadata.dag_nodes.append(cell_meta.node_id)

        # After parsing all cells, infer dependencies from code
        # This allows us to use actual code references instead of maintaining explicit lists
        all_node_ids = metadata.dag_nodes

        for cell_meta in metadata.node_cells:
            # Get the code for this node (only from non-result cells)
            if not cell_meta.is_result_cell:
                # Infer dependencies from code
                inferred_deps = DependencyInferencer.infer_dependencies(
                    node_id=cell_meta.node_id,
                    code=cell_meta.content,
                    all_node_ids=all_node_ids,
                    explicit_dependencies=cell_meta.depends_on if cell_meta.depends_on else None
                )

                # Use inferred dependencies
                cell_meta.depends_on = inferred_deps

                # Build DAG edges
                for dep in cell_meta.depends_on:
                    metadata.dag_edges.append((dep, cell_meta.node_id))

        # Validate DAG
        validation_errors = self._validate_dag(metadata)
        metadata.errors.extend(validation_errors)

        return metadata

    def _parse_cell(self, cell_index: int, cell: Dict[str, Any]) -> CellMetadata:
        """
        Parse single cell and extract metadata

        Args:
            cell_index: Index of cell
            cell: Cell dict from notebook

        Returns:
            CellMetadata with extracted information
        """
        cell_type = cell.get('cell_type', 'unknown')
        cell_meta = CellMetadata(cell_index, cell_type)
        cell_notebook_meta = cell.get('metadata', {})

        # Get cell source
        source = cell.get('source', [])
        if isinstance(source, list):
            cell_meta.content = ''.join(source)
        else:
            cell_meta.content = str(source)

        # Handle markdown cells
        if cell_type == 'markdown':
            # Check for linked_node_id in metadata (markdown cell linked to code node)
            if 'linked_node_id' in cell_notebook_meta:
                cell_meta.linked_node_id = cell_notebook_meta['linked_node_id']
            return cell_meta

        # Handle code cells
        if cell_type != 'code':
            return cell_meta

        # Check if this is a result cell
        if cell_notebook_meta.get('result_cell', False):
            cell_meta.is_result_cell = True
            cell_meta.node_id = cell_notebook_meta.get('node_id')
            cell_meta.result_format = cell_notebook_meta.get('result_format')
            cell_meta.parquet_path = cell_notebook_meta.get('parquet_path')
            return cell_meta

        # Extract metadata from comments
        node_type_match = self.NODE_TYPE_PATTERN.search(cell_meta.content)
        node_id_match = self.NODE_ID_PATTERN.search(cell_meta.content)

        if node_type_match and node_id_match:
            cell_meta.is_node = True
            cell_meta.node_type = node_type_match.group(1)
            cell_meta.node_id = node_id_match.group(1)

            # Optional: node name
            name_match = self.NODE_NAME_PATTERN.search(cell_meta.content)
            if name_match:
                cell_meta.node_name = name_match.group(1).strip()

            # Optional: execution status
            exec_status_match = self.EXECUTION_STATUS_PATTERN.search(cell_meta.content)
            if exec_status_match:
                cell_meta.execution_status = exec_status_match.group(1)

            # Optional: declared output type
            output_type_match = self.OUTPUT_TYPE_PATTERN.search(cell_meta.content)
            if output_type_match:
                cell_meta.declared_output_type = output_type_match.group(1)

            # Optional: dependencies
            depends_match = self.DEPENDS_PATTERN.search(cell_meta.content)
            if depends_match:
                deps_str = depends_match.group(1)
                # Parse comma-separated list of node IDs
                deps = [d.strip().strip("'\"") for d in deps_str.split(',')]
                cell_meta.depends_on = [d for d in deps if d]

            # Override with cell metadata if present
            if 'node_type' in cell_notebook_meta:
                cell_meta.node_type = cell_notebook_meta['node_type']
            if 'node_id' in cell_notebook_meta:
                cell_meta.node_id = cell_notebook_meta['node_id']
            if 'depends_on' in cell_notebook_meta:
                cell_meta.depends_on = cell_notebook_meta['depends_on']
            if 'execution_status' in cell_notebook_meta:
                cell_meta.execution_status = cell_notebook_meta['execution_status']
            if 'declared_output_type' in cell_notebook_meta:
                cell_meta.declared_output_type = cell_notebook_meta['declared_output_type']

        return cell_meta

    def _validate_dag(self, metadata: NotebookMetadata) -> List[str]:
        """
        Validate DAG structure

        Args:
            metadata: NotebookMetadata to validate

        Returns:
            List of validation error messages
        """
        errors = []
        nodes = set(metadata.dag_nodes)

        # Check for undefined dependencies
        for cell in metadata.node_cells:
            for dep in cell.depends_on:
                if dep not in nodes:
                    errors.append(f"Node {cell.node_id} depends on undefined node {dep}")

        # Check for cycles (DFS)
        if self._has_cycle(metadata.dag_edges, nodes):
            errors.append("Circular dependency detected in DAG")

        # Check for duplicate node IDs
        node_ids = [cell.node_id for cell in metadata.node_cells]
        duplicates = [nid for nid in set(node_ids) if node_ids.count(nid) > 1]
        for dup in duplicates:
            errors.append(f"Duplicate node ID: {dup}")

        return errors

    def _has_cycle(self, edges: List[Tuple[str, str]], nodes: set) -> bool:
        """
        Check if DAG has cycle using DFS

        Args:
            edges: List of (source, target) edges
            nodes: Set of node IDs

        Returns:
            True if cycle detected
        """
        # Build adjacency list
        graph = {node: [] for node in nodes}
        for source, target in edges:
            if source in graph:
                graph[source].append(target)

        # DFS for cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle_dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in nodes:
            if node not in visited:
                if has_cycle_dfs(node):
                    return True

        return False

    def get_node_execution_order(self, metadata: NotebookMetadata) -> List[str]:
        """
        Get topological order of nodes

        Args:
            metadata: NotebookMetadata

        Returns:
            List of node IDs in execution order

        Raises:
            MetadataParseError: If DAG has cycles
        """
        if metadata.errors:
            raise MetadataParseError(f"Cannot compute order due to errors: {metadata.errors}")

        # Build adjacency list
        nodes = set(metadata.dag_nodes)
        graph = {node: [] for node in nodes}
        in_degree = {node: 0 for node in nodes}

        for source, target in metadata.dag_edges:
            graph[source].append(target)
            in_degree[target] += 1

        # Topological sort (Kahn's algorithm)
        queue = [node for node in nodes if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            raise MetadataParseError("Circular dependency detected")

        return result

    def get_node_info(self, metadata: NotebookMetadata, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about specific node

        Args:
            metadata: NotebookMetadata
            node_id: Node identifier

        Returns:
            Node info dict or None if not found
        """
        for cell in metadata.node_cells:
            if cell.node_id == node_id:
                return {
                    "node_id": cell.node_id,
                    "node_type": cell.node_type,
                    "node_name": cell.node_name,
                    "cell_index": cell.cell_index,
                    "depends_on": cell.depends_on,
                    "code_length": len(cell.content)
                }
        return None

    def get_nodes_by_type(self, metadata: NotebookMetadata, node_type: str) -> List[Dict[str, Any]]:
        """
        Get all nodes of specific type

        Args:
            metadata: NotebookMetadata
            node_type: Type to filter by

        Returns:
            List of node info dicts
        """
        return [
            {
                "node_id": cell.node_id,
                "node_type": cell.node_type,
                "node_name": cell.node_name,
                "cell_index": cell.cell_index,
                "depends_on": cell.depends_on,
                "execution_status": cell.execution_status
            }
            for cell in metadata.node_cells
            if cell.node_type == node_type
        ]

    def get_nodes_by_execution_status(self, metadata: NotebookMetadata, status: str) -> List[Dict[str, Any]]:
        """
        Get all nodes with specific execution status

        Args:
            metadata: NotebookMetadata
            status: Execution status ('not_executed', 'pending_validation', 'validated')

        Returns:
            List of node info dicts
        """
        return [
            {
                "node_id": cell.node_id,
                "node_type": cell.node_type,
                "node_name": cell.node_name,
                "cell_index": cell.cell_index,
                "execution_status": cell.execution_status
            }
            for cell in metadata.node_cells
            if cell.execution_status == status
        ]

    def get_result_cells(self, metadata: NotebookMetadata) -> List[Dict[str, Any]]:
        """
        Get all result cells

        Args:
            metadata: NotebookMetadata

        Returns:
            List of result cell info dicts
        """
        result_cells = [cell for cell in metadata.cells if cell.is_result_cell]
        return [
            {
                "cell_index": cell.cell_index,
                "node_id": cell.node_id,
                "result_format": cell.result_format,
                "parquet_path": cell.parquet_path
            }
            for cell in result_cells
        ]

    def get_markdown_links(self, metadata: NotebookMetadata) -> Dict[str, int]:
        """
        Get mapping of linked node IDs to their markdown cell indices

        Args:
            metadata: NotebookMetadata

        Returns:
            Dict mapping node_id to markdown cell index
        """
        links = {}
        for cell in metadata.cells:
            if cell.linked_node_id:
                links[cell.linked_node_id] = cell.cell_index
        return links

    def get_node_with_metadata(self, metadata: NotebookMetadata, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive node information including execution status and result cell

        Args:
            metadata: NotebookMetadata
            node_id: Node identifier

        Returns:
            Comprehensive node info dict or None if not found
        """
        node_info = self.get_node_info(metadata, node_id)
        if not node_info:
            return None

        # Find result cell for this node
        result_cell = None
        for cell in metadata.cells:
            if cell.is_result_cell and cell.node_id == node_id:
                result_cell = {
                    "cell_index": cell.cell_index,
                    "result_format": cell.result_format,
                    "parquet_path": cell.parquet_path
                }
                break

        # Find markdown link for this node
        markdown_index = None
        for cell in metadata.cells:
            if cell.linked_node_id == node_id:
                markdown_index = cell.cell_index
                break

        return {
            **node_info,
            "result_cell": result_cell,
            "markdown_cell_index": markdown_index
        }
