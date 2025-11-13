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
        result_path: Optional[str] = None
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
            "last_execution_time": None  # ISO format timestamp of last execution
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
        for node in data.get("nodes", []):
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
        result_path: Optional[str] = None
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
            result_path=result_path
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

    def save_node_result(
        self,
        node_id: str,
        result: Any,
        result_type: str = "parquet",
        is_visualization: bool = False
    ) -> str:
        """
        Save node execution result to file

        Args:
            node_id: Node ID
            result: Result object (DataFrame, dict, list, etc.)
            result_type: Type of result (parquet, json, pickle, image, visualization)
            is_visualization: Whether to save to visualizations/ instead of parquets/

        Returns:
            Path to saved file
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        import pandas as pd

        # Determine target directory
        target_dir = self.visualizations_path if is_visualization else self.parquets_path

        # Auto-detect format and save
        if isinstance(result, pd.DataFrame):
            result_path = target_dir / f"{node_id}.parquet"
            result.to_parquet(result_path)

        elif isinstance(result, dict):
            result_path = target_dir / f"{node_id}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        elif isinstance(result, (list, tuple)):
            result_path = target_dir / f"{node_id}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(list(result), f, ensure_ascii=False, indent=2)

        else:
            # Fallback to pickle for other types
            import pickle
            result_path = target_dir / f"{node_id}.pkl"
            with open(result_path, 'wb') as f:
                pickle.dump(result, f)

        return str(result_path)

    def load_node_result(self, node_id: str) -> Any:
        """
        Load node result from file

        Args:
            node_id: Node ID

        Returns:
            Loaded result object
        """
        if not self.loaded:
            raise RuntimeError("Project not loaded")

        import pandas as pd

        # Try to find file in both parquets and visualizations directories
        for target_dir in [self.parquets_path, self.visualizations_path]:
            for ext in ['parquet', 'json', 'pkl']:
                result_path = target_dir / f"{node_id}.{ext}"
                if result_path.exists():
                    if ext == 'parquet':
                        return pd.read_parquet(result_path)
                    elif ext == 'json':
                        with open(result_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    elif ext == 'pkl':
                        import pickle
                        with open(result_path, 'rb') as f:
                            return pickle.load(f)

        raise FileNotFoundError(f"No result found for node {node_id}")

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

    def export_metadata_json(self, filepath: str) -> None:
        """Export project metadata to JSON file"""
        if self.metadata is None:
            raise RuntimeError("Metadata not loaded")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata.to_dict(), f, indent=2, ensure_ascii=False)
