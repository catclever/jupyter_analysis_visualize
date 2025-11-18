"""
Project Manager

Manages project structure, configuration, and file operations.
Handles:
- Project initialization and directory structure
- Project metadata (project.json)
- Parquet/JSON result file management
- Notebook file management
"""

import json
import os
import pandas as pd
import cloudpickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from notebook_manager import NotebookManager


class ProjectMetadata:
    """Project metadata configuration with execution tracking"""

    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0"
    ):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.version = version
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        depends_on: Optional[List[str]] = None,
        execution_status: str = "not_executed",
        result_format: Optional[str] = None,
        result_path: Optional[str] = None,
        position: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Add a node to project metadata

        Args:
            node_id: Unique node identifier
            node_type: Type of node (data_source, compute, chart, tool)
            name: Human-readable node name
            depends_on: List of upstream node IDs
            execution_status: Execution state (not_executed, pending_validation, validated)
            result_format: Result format (parquet, json, image, visualization)
            result_path: Path to saved result file
            position: Node position in flow diagram {x: float, y: float}
        """
        self.nodes[node_id] = {
            "node_id": node_id,
            "type": node_type,
            "name": name,
            "depends_on": depends_on or [],
            "execution_status": execution_status,  # not_executed | pending_validation | validated
            "result_format": result_format,
            "result_path": result_path,
            "error_message": None,  # Error message if execution failed
            "last_execution_time": None,  # ISO format timestamp of last execution
            "position": position  # Node position {x: float, y: float}
        }
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "nodes": list(self.nodes.values())
            # DAG is no longer stored - it's inferred from code on every load
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProjectMetadata":
        """Create ProjectMetadata from dictionary"""
        meta = ProjectMetadata(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0")
        )
        meta.created_at = data.get("created_at", meta.created_at)
        meta.updated_at = data.get("updated_at", meta.updated_at)

        # Restore nodes
        nodes_data = data.get("nodes", {})
        # Handle both dict and list formats for backward compatibility
        if isinstance(nodes_data, dict):
            for node_id, node_info in nodes_data.items():
                meta.nodes[node_id] = node_info
        else:
            for node in nodes_data:
                meta.nodes[node["node_id"]] = node

        return meta


class ProjectManager:
    """Manages a single project - its structure, config, and files"""

    def __init__(self, projects_root: str, project_id: str):
        """
        Initialize ProjectManager for a specific project

        Args:
            projects_root: Root directory containing all projects
            project_id: Unique project identifier (directory name)
        """
        self.projects_root = Path(projects_root)
        self.project_id = project_id
        self.project_path = self.projects_root / project_id
        self.notebook_path = self.project_path / "project.ipynb"
        self.metadata_path = self.project_path / "project.json"
        self.parquets_path = self.project_path / "parquets"
        self.visualizations_path = self.project_path / "visualizations"
        self.nodes_path = self.project_path / "nodes"
        self.functions_path = self.project_path / "functions"

        self.metadata: Optional[ProjectMetadata] = None
        self.notebook_manager: Optional[NotebookManager] = None
        self.loaded = False

    def exists(self) -> bool:
        """Check if project exists"""
        return self.project_path.exists()

    def create(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0"
    ) -> None:
        """
        Create a new project with directory structure

        Args:
            name: Project display name
            description: Project description
            version: Project version
        """
        if self.exists():
            raise FileExistsError(f"Project {self.project_id} already exists")

        # Create directories
        self.project_path.mkdir(parents=True, exist_ok=True)
        self.parquets_path.mkdir(parents=True, exist_ok=True)
        self.visualizations_path.mkdir(parents=True, exist_ok=True)
        self.nodes_path.mkdir(parents=True, exist_ok=True)
        self.functions_path.mkdir(parents=True, exist_ok=True)

        # Create metadata
        self.metadata = ProjectMetadata(
            project_id=self.project_id,
            name=name,
            description=description,
            version=version
        )

        # Create empty notebook
        self.notebook_manager = NotebookManager(str(self.notebook_path))
        self.notebook_manager.append_markdown_cell(f"# {name}\n\n{description}")
        self.notebook_manager.save()

        # Save metadata
        self._save_metadata()

        self.loaded = True

    def load(self) -> None:
        """Load existing project"""
        if not self.exists():
            raise FileNotFoundError(f"Project {self.project_id} does not exist")

        # Load metadata
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                meta_dict = json.load(f)
            self.metadata = ProjectMetadata.from_dict(meta_dict)
        else:
            raise FileNotFoundError(f"Project metadata not found: {self.metadata_path}")

        # Load notebook
        self.notebook_manager = NotebookManager(str(self.notebook_path))

        self.loaded = True

    def _save_metadata(self) -> None:
        """Save project metadata to JSON file"""
        if self.metadata is None:
            raise RuntimeError("Metadata not initialized")

        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata.to_dict(), f, indent=2, ensure_ascii=False)

    def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        depends_on: Optional[List[str]] = None,
        code: str = "",
        node_description: str = "",
        execution_status: str = "not_executed",
        result_format: Optional[str] = None,
        result_path: Optional[str] = None,
        position: Optional[Dict[str, float]] = None
    ) -> int:
        """
        Add a node to the project with support for execution status and results

        Args:
            node_id: Unique node identifier
            node_type: Type of node (data_source, compute, chart, tool)
            name: Human-readable node name
            depends_on: List of upstream node IDs
            code: Python code for the node
            node_description: Markdown description for the node
            execution_status: Execution state (not_executed, pending_validation, validated)
            result_format: Result format (parquet, json, image, visualization)
            result_path: Path to saved result file
            position: Node position in flow diagram {x: float, y: float}

        Returns:
            Index of the last added cell in notebook
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        if self.metadata is None or self.notebook_manager is None:
            raise RuntimeError("Project not properly initialized")

        # Add to metadata
        self.metadata.add_node(
            node_id, node_type, name, depends_on,
            execution_status=execution_status,
            result_format=result_format,
            result_path=result_path,
            position=position
        )

        # Add description markdown if provided
        if node_description:
            self.notebook_manager.append_markdown_cell(
                node_description,
                linked_node_id=node_id
            )

        # Add code cell
        cell_index = self.notebook_manager.append_code_cell(
            code=code,
            node_type=node_type,
            node_id=node_id,
            depends_on=depends_on,
            name=name,
            execution_status=execution_status,
            add_header_comment=True
        )

        # Add result cell if execution status is not "not_executed"
        if execution_status != "not_executed" and result_format and result_path:
            cell_index = self.notebook_manager.append_result_cell(
                node_id=node_id,
                parquet_path=result_path,
                result_format=result_format,
                description=f"Result for {name}"
            )

        # Save changes
        self.notebook_manager.save()
        self._save_metadata()

        return cell_index

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node metadata"""
        if self.metadata is None:
            return None
        return self.metadata.nodes.get(node_id)

    def list_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes in project"""
        if self.metadata is None:
            return []
        return list(self.metadata.nodes.values())

    def list_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """Get nodes of specific type"""
        if self.metadata is None:
            return []
        return [
            node for node in self.metadata.nodes.values()
            if node.get("type") == node_type
        ]

    def update_node_position(self, node_id: str, position: Dict[str, float]) -> None:
        """
        Update node position in the flow diagram

        Args:
            node_id: Node ID
            position: Position dict with x and y coordinates {x: float, y: float}
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        if self.metadata is None:
            raise RuntimeError("Metadata not initialized")

        if node_id not in self.metadata.nodes:
            raise ValueError(f"Node {node_id} not found in project metadata")

        # Update position
        self.metadata.nodes[node_id]["position"] = position
        self.metadata.updated_at = datetime.now().isoformat()

        # Save to disk
        self._save_metadata()

    def save_node_result(
        self,
        project_id: str,
        node_id: str,
        result: Any,
        node_type: str,
        is_visualization: bool = False
    ) -> str:
        """
        Save node execution result to file, respecting the node type.

        Args:
            project_id: The ID of the project.
            node_id: Node ID.
            result: Result object (DataFrame, dict, list, function, etc.).
            node_type: The type of the node ('data_source', 'compute', 'tool', etc.).
            is_visualization: Whether to save to visualizations/ directory.

        Returns:
            Path to saved file.
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        # Determine target directory based on node type
        if node_type == 'tool':
            target_dir = self.functions_path
        else:
            target_dir = self.visualizations_path if is_visualization else self.parquets_path
        
        target_dir.mkdir(parents=True, exist_ok=True)

        # Tool nodes are always saved as pickle files
        if node_type == 'tool':
            result_path = target_dir / f"{node_id}.pkl"
            with open(result_path, 'wb') as f:
                cloudpickle.dump(result, f)
            return str(result_path.relative_to(self.project_path))

        # For other nodes, auto-detect format
        if isinstance(result, pd.DataFrame):
            result_path = target_dir / f"{node_id}.parquet"
            try:
                result.to_parquet(result_path, engine='pyarrow')
            except Exception as e:
                print(f"Warning: Parquet save failed for {node_id}, falling back to JSON: {e}")
                result_path = target_dir / f"{node_id}.json"
                result.to_json(str(result_path), orient='records', force_ascii=False)
        elif isinstance(result, (dict, list, tuple)):
            result_path = target_dir / f"{node_id}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            # Fallback to pickle for any other type in non-tool nodes
            result_path = target_dir / f"{node_id}.pkl"
            with open(result_path, 'wb') as f:
                pickle.dump(result, f)

        return str(result_path.relative_to(self.project_path))

    def load_node_result(self, project_id: str, node_id: str) -> Any:
        """
        Load node result from file, prioritizing the path from project.json.

        Args:
            project_id: The ID of the project.
            node_id: Node ID.

        Returns:
            Loaded result object.
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        node = self.get_node(node_id)
        if not node:
            raise FileNotFoundError(f"Metadata for node {node_id} not found in project.json")

        import pandas as pd
        import cloudpickle

        # Tool nodes are always stored as pickle files in the functions/ directory
        if node_type == 'tool':
            # Prioritize result_path from project.json
            if node.get('result_path'):
                result_file = self.project_path / node['result_path']
                if result_file.exists() and result_file.suffix == '.pkl':
                    with open(result_file, 'rb') as f:
                        return cloudpickle.load(f)
            
            # Fallback to convention-based search in functions/ dir
            result_path = self.functions_path / f"{node_id}.pkl"
            if result_path.exists():
                with open(result_path, 'rb') as f:
                    return cloudpickle.load(f)
            
            raise FileNotFoundError(f"No .pkl result found for tool node {node_id} in functions/ directory or at specified result_path.")

        # For other nodes, try parquet and json using the primary/fallback strategy
        if node.get('result_path'):
            result_file = self.project_path / node['result_path']
            if result_file.exists():
                ext = result_file.suffix
                if ext == '.parquet':
                    return pd.read_parquet(result_file)
                elif ext == '.json':
                    with open(result_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                elif ext == '.pkl':
                     with open(result_file, 'rb') as f:
                        return cloudpickle.load(f)
                else:
                    raise NotImplementedError(f"Unsupported file extension '{ext}' for result loading.")
        
        # Fallback for other nodes if result_path is missing
        for target_dir in [self.parquets_path, self.visualizations_path]:
            for ext in ['parquet', 'json']:
                result_path = target_dir / f"{node_id}.{ext}"
                if result_path.exists():
                    if ext == 'parquet':
                        return pd.read_parquet(result_path)
                    elif ext == 'json':
                        with open(result_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
        
        raise FileNotFoundError(f"No result found for node {node_id} (and no result_path in project.json)")

    def list_results(self) -> List[Dict[str, str]]:
        """List all saved results from both parquets and visualizations directories"""
        if not self.loaded:
            return []

        results = []

        # List results from parquets directory
        if self.parquets_path.exists():
            for file_path in self.parquets_path.glob('*'):
                if file_path.is_file():
                    results.append({
                        "node_id": file_path.stem,
                        "format": file_path.suffix[1:],  # Remove leading dot
                        "path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "directory": "parquets"
                    })

        # List results from visualizations directory
        if self.visualizations_path.exists():
            for file_path in self.visualizations_path.glob('*'):
                if file_path.is_file():
                    results.append({
                        "node_id": file_path.stem,
                        "format": file_path.suffix[1:],  # Remove leading dot
                        "path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "directory": "visualizations"
                    })

        return sorted(results, key=lambda x: (x["node_id"], x["directory"]))

    def get_project_info(self) -> Dict[str, Any]:
        """Get complete project information"""
        if not self.loaded or self.metadata is None:
            raise RuntimeError("Project not loaded")

        return {
            "project_id": self.project_id,
            "path": str(self.project_path),
            "metadata": self.metadata.to_dict(),
            "notebook_cells": len(self.notebook_manager.get_cells()) if self.notebook_manager else 0,
            "node_cells": len(self.notebook_manager.list_node_cells()) if self.notebook_manager else 0,
            "results": self.list_results()
        }

    def update_node_status(self, node_id: str, status: str, result_path: Optional[str] = None, error: Optional[str] = None) -> None:
        """
        Update the execution status and result path of a node in project.json.

        Args:
            node_id: The ID of the node to update.
            status: The new execution status (e.g., 'validated', 'error').
            result_path: The path to the saved result file, if successful.
            error: The error message, if execution failed.
        """
        if not self.loaded or self.metadata is None:
            raise RuntimeError("Project not loaded")

        if node_id in self.metadata.nodes:
            node = self.metadata.nodes[node_id]
            node['execution_status'] = status
            node['last_execution_time'] = datetime.now().isoformat()
            if status == 'validated':
                node['result_path'] = result_path
                node['error_message'] = None
            elif status == 'error':
                node['error_message'] = error
            
            self.metadata.updated_at = datetime.now().isoformat()
            self._save_metadata()
        else:
            # This should ideally not happen in a normal flow
            print(f"Warning: Attempted to update status for non-existent node {node_id}")

    def export_metadata_json(self, filepath: str) -> None:
        """Export project metadata to JSON file"""
        if self.metadata is None:
            raise RuntimeError("Metadata not loaded")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata.to_dict(), f, indent=2, ensure_ascii=False)
