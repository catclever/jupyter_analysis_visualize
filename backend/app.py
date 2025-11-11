"""
FastAPI Backend for Jupyter Analysis Visualize

Serves project data to frontend including:
- Project metadata and DAG structure
- Node data (parquet/JSON files)
- Pagination support for large datasets
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi.responses import FileResponse

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from project_manager import ProjectManager

# Initialize FastAPI app
app = FastAPI(
    title="Jupyter Analysis Visualize API",
    description="Backend API for notebook-based data analysis visualization",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get projects root directory
PROJECTS_ROOT = Path(__file__).parent.parent / "projects"


def get_project_manager(project_id: str) -> ProjectManager:
    """Get and load a project manager instance"""
    pm = ProjectManager(str(PROJECTS_ROOT), project_id)
    if not pm.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    pm.load()
    return pm


@app.get("/api/projects")
def list_projects() -> Dict[str, Any]:
    """List all available projects (including test projects)"""
    if not PROJECTS_ROOT.exists():
        return {"projects": []}

    projects = []
    for project_dir in PROJECTS_ROOT.iterdir():
        if not project_dir.is_dir():
            continue

        project_id = project_dir.name
        metadata_path = project_dir / "project.json"

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                projects.append({
                    "id": project_id,
                    "name": metadata.get("name", project_id),
                    "description": metadata.get("description", ""),
                    "version": metadata.get("version", "1.0.0"),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                })
            except Exception as e:
                print(f"Error loading project {project_id}: {e}")
                continue

    return {"projects": projects}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> Dict[str, Any]:
    """
    Get project metadata including:
    - Project info
    - Nodes list
    - DAG structure (nodes and edges)
    - Node execution status
    """
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        project_data = pm.metadata.to_dict()

        # Transform nodes format for frontend
        nodes = []
        edges = []

        for node_info in project_data["nodes"]:
            # Map backend node types directly to frontend
            # Backend supports: data_source, compute, chart, image, tool
            # Frontend now supports: data_source, compute, chart, image, tool (via config)
            node_type = node_info.get("type", "compute")  # default to compute

            # For backward compatibility, map old "data" type to "data_source"
            if node_type == "data":
                node_type = "data_source"

            nodes.append({
                "id": node_info["node_id"],
                "label": node_info["name"],
                "type": node_type,  # Pass through backend type directly
                "execution_status": node_info.get("execution_status", "not_executed"),
                "result_format": node_info.get("result_format"),
                "result_path": node_info.get("result_path"),
                "output": node_info.get("output"),  # Include output metadata for frontend display rules
            })

            # Build edges from dependencies
            for dep in node_info.get("depends_on", []):
                edges.append({
                    "id": f"e_{dep}_{node_info['node_id']}",
                    "source": dep,
                    "target": node_info["node_id"],
                    "animated": True
                })

        return {
            "id": project_data["project_id"],
            "name": project_data["name"],
            "description": project_data["description"],
            "version": project_data["version"],
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "nodes": nodes,
            "edges": edges,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/data")
def get_node_data(
    project_id: str,
    node_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=1000, description="Records per page")
) -> Dict[str, Any]:
    """
    Get node result data with pagination support.

    Supports:
    - Parquet files (DataFrames)
    - JSON files (already serialized data)

    Returns paginated data with metadata
    """
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Find node info
        node_info = None
        for node in pm.metadata.nodes.values():
            if node["node_id"] == node_id:
                node_info = node
                break

        if node_info is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        if node_info.get("execution_status") == "not_executed":
            raise HTTPException(
                status_code=400,
                detail=f"Node {node_id} has not been executed"
            )

        result_format = node_info.get("result_format")
        result_path = node_info.get("result_path")

        if not result_path:
            raise HTTPException(
                status_code=400,
                detail=f"No result path found for node {node_id}"
            )

        # Construct full file path
        # result_path might be absolute or relative, handle both cases
        result_path_obj = Path(result_path)
        if result_path_obj.is_absolute():
            file_path = result_path_obj
        else:
            # Try to resolve as relative path from project root
            file_path = pm.project_path / result_path
            if not file_path.exists():
                # If not found, try using just the filename from the path
                filename = result_path.split('/')[-1]
                # Try parquets directory first
                file_path = pm.parquets_path / filename
                if not file_path.exists():
                    # Try visualizations directory
                    file_path = pm.visualizations_path / filename

        if not file_path.exists():
            # Final fallback: try constructing from node_id and format
            if result_format == "parquet":
                file_path = pm.parquets_path / f"{node_id}.parquet"
            elif result_format == "json":
                file_path = pm.parquets_path / f"{node_id}.json"
            elif result_format in ("image", "visualization"):
                file_path = pm.visualizations_path / f"{node_id}.png"

            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Result file not found: {result_path}"
                )

        # Load data based on format
        if result_format == "parquet":
            # Handle absolute path returned from save_node_result
            try:
                df = pd.read_parquet(str(file_path))
            except FileNotFoundError:
                # Try alternative path construction
                alt_path = pm.parquets_path / f"{node_id}.parquet"
                if alt_path.exists():
                    df = pd.read_parquet(str(alt_path))
                    file_path = alt_path
                else:
                    raise
            total_records = len(df)

            # Calculate pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_data = df.iloc[start_idx:end_idx]

            return {
                "node_id": node_id,
                "format": "parquet",
                "total_records": total_records,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size,
                "columns": list(df.columns),
                "data": page_data.to_dict(orient="records"),
            }

        elif result_format == "json":
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                # Try alternative path construction
                alt_path = pm.parquets_path / f"{node_id}.json"
                if alt_path.exists():
                    with open(alt_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    file_path = alt_path
                else:
                    raise

            # Handle pagination for JSON data (if it's a list)
            if isinstance(data, list):
                total_records = len(data)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                page_data = data[start_idx:end_idx]

                return {
                    "node_id": node_id,
                    "format": "json",
                    "total_records": total_records,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_records + page_size - 1) // page_size,
                    "data": page_data,
                }
            else:
                # If JSON is not a list, return as single record
                return {
                    "node_id": node_id,
                    "format": "json",
                    "total_records": 1,
                    "page": 1,
                    "page_size": page_size,
                    "total_pages": 1,
                    "data": [data] if not isinstance(data, dict) else data,
                }

        elif result_format == "image":
            # For images, return file metadata and path
            return {
                "node_id": node_id,
                "format": "image",
                "file_path": str(file_path.relative_to(pm.project_path)),
                "url": f"/api/projects/{project_id}/nodes/{node_id}/image",
            }

        elif result_format == "visualization":
            # For visualizations, return file metadata and path
            return {
                "node_id": node_id,
                "format": "visualization",
                "file_path": str(file_path.relative_to(pm.project_path)),
                "url": f"/api/projects/{project_id}/nodes/{node_id}/visualization",
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported result format: {result_format}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/image")
def get_node_image(project_id: str, node_id: str):
    """Stream image file for a node"""
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Find node info
        node_info = None
        for node in pm.metadata.nodes.values():
            if node["node_id"] == node_id:
                node_info = node
                break

        if node_info is None or node_info.get("result_format") != "image":
            raise HTTPException(status_code=404, detail="Image not found")

        result_path = node_info.get("result_path")
        file_path = pm.project_path / result_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Return file with appropriate MIME type
        from fastapi.responses import FileResponse
        return FileResponse(str(file_path), media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/visualization")
def get_node_visualization(project_id: str, node_id: str):
    """Stream visualization file (usually PNG chart) for a node"""
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Find node info
        node_info = None
        for node in pm.metadata.nodes.values():
            if node["node_id"] == node_id:
                node_info = node
                break

        if node_info is None or node_info.get("result_format") != "visualization":
            raise HTTPException(status_code=404, detail="Visualization not found")

        result_path = node_info.get("result_path")
        file_path = pm.project_path / result_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Return file with appropriate MIME type
        from fastapi.responses import FileResponse
        return FileResponse(str(file_path), media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/code")
def get_node_code(project_id: str, node_id: str) -> Dict[str, Any]:
    """
    Get the source code of a node from the notebook

    Returns the code cell content associated with the node
    """
    try:
        pm = get_project_manager(project_id)

        if pm.notebook_manager is None or pm.notebook_manager.notebook is None:
            raise HTTPException(status_code=500, detail="Failed to load notebook")

        # Get notebook dict
        notebook = pm.notebook_manager.notebook
        cells = notebook.get('cells', [])

        # Find code cell with matching node_id
        for cell in cells:
            if cell.get('cell_type') == 'code':
                metadata = cell.get('metadata', {})
                if metadata.get('node_id') == node_id:
                    # Skip result cells
                    if not metadata.get('result_cell'):
                        source = cell.get('source', '')
                        if isinstance(source, list):
                            source = ''.join(source)
                        return {
                            "node_id": node_id,
                            "code": source,
                            "language": "python"
                        }

        raise HTTPException(status_code=404, detail=f"Code not found for node {node_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/markdown")
def get_node_markdown(project_id: str, node_id: str) -> Dict[str, Any]:
    """
    Get the markdown summary/documentation of a node from the notebook

    Returns the markdown cell linked to the node
    """
    try:
        pm = get_project_manager(project_id)

        if pm.notebook_manager is None or pm.notebook_manager.notebook is None:
            raise HTTPException(status_code=500, detail="Failed to load notebook")

        # Get notebook dict
        notebook = pm.notebook_manager.notebook
        cells = notebook.get('cells', [])

        # Find markdown cell with matching linked_node_id
        for cell in cells:
            if cell.get('cell_type') == 'markdown':
                metadata = cell.get('metadata', {})
                if metadata.get('linked_node_id') == node_id:
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        source = ''.join(source)
                    return {
                        "node_id": node_id,
                        "markdown": source,
                        "format": "markdown"
                    }

        raise HTTPException(status_code=404, detail=f"Markdown not found for node {node_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}/nodes/{node_id}/markdown")
def update_node_markdown(project_id: str, node_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the markdown summary/documentation of a node in the notebook

    Updates the markdown cell linked to the node
    """
    try:
        pm = get_project_manager(project_id)

        if pm.notebook_manager is None or pm.notebook_manager.notebook is None:
            raise HTTPException(status_code=500, detail="Failed to load notebook")

        markdown_content = body.get('markdown', '')

        # Get notebook dict
        notebook = pm.notebook_manager.notebook
        cells = notebook.get('cells', [])

        # Find markdown cell with matching linked_node_id and update it
        for cell in cells:
            if cell.get('cell_type') == 'markdown':
                metadata = cell.get('metadata', {})
                if metadata.get('linked_node_id') == node_id:
                    # Update the cell source
                    # Convert to list format (Jupyter format)
                    lines = markdown_content.split('\n')
                    source = []
                    for i, line in enumerate(lines):
                        if i < len(lines) - 1:
                            source.append(line + '\n')
                        elif line:  # Only add last line if not empty
                            source.append(line)

                    cell['source'] = source

                    # Save notebook
                    pm.notebook_manager.save()

                    return {
                        "node_id": node_id,
                        "markdown": markdown_content,
                        "format": "markdown"
                    }

        raise HTTPException(status_code=404, detail=f"Markdown not found for node {node_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
