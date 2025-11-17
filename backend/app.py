"""
FastAPI Backend for Jupyter Analysis Visualize

Serves project data to frontend including:
- Project metadata and DAG structure
- Node data (parquet/JSON files)
- Pagination support for large datasets
"""

import json
import os
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from fastapi.responses import FileResponse

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from project_manager import ProjectManager
from notebook_manager import NotebookManager
from dependency_analyzer import DependencyAnalyzer

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

# Get projects root directory (with fallback for different execution contexts)
# First try relative path from current working directory (for root directory execution)
if Path("./projects").exists():
    PROJECTS_ROOT = Path("./projects").resolve()
# Fallback to path relative to this file (for module execution)
else:
    PROJECTS_ROOT = (Path(__file__).parent.parent / "projects").resolve()

# Mount frontend static files for serving the built React app
# Similarly try relative path first, then fallback
if Path("./frontend/dist").exists():
    FRONTEND_DIST = Path("./frontend/dist").resolve()
else:
    FRONTEND_DIST = (Path(__file__).parent.parent / "frontend" / "dist").resolve()
if FRONTEND_DIST.exists():
    # Mount static files at root path, with index.html as fallback for SPA routing
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
else:
    print(f"⚠️  Warning: Frontend dist directory not found at {FRONTEND_DIST}")
    print("   Make sure to build the frontend: cd frontend && npm run build")


def get_project_manager(project_id: str) -> ProjectManager:
    """Get and load a project manager instance"""
    pm = ProjectManager(str(PROJECTS_ROOT), project_id)
    if not pm.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    pm.load()
    return pm


def extract_variable_names(code: str) -> Set[str]:
    """
    Extract variable names used in code
    Returns a set of variable names that are referenced (not assigned)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If code has syntax errors, try to extract names using regex
        # Look for variable names that are not being assigned
        names = set()
        # Match identifiers that are not preceded by = or def or class
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

        def visit_Attribute(self, node):
            # For obj.attr, we're interested in obj being loaded
            self.generic_visit(node)

    visitor = NameVisitor()
    visitor.visit(tree)

    # Filter out built-in names and common pandas/numpy names
    builtins = {'print', 'len', 'range', 'sum', 'min', 'max', 'str', 'int', 'float',
                 'list', 'dict', 'set', 'tuple', 'enumerate', 'zip', 'map', 'filter',
                 'open', 'read', 'write', 'True', 'False', 'None', 'Exception',
                 'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
                 'os', 'sys', 'json', 'pd', 'np', 'plt', 'sns', 'datetime', 'time',
                 'pandas', 'numpy', 'matplotlib', 'seaborn', 'display', 'sqrt', 'math',
                 'mean', 'std', 'var', 'pow', 'abs', 'round', 'sorted', 'reversed',
                 'any', 'all', 'iter', 'next', 'callable', 'hasattr', 'getattr',
                 'setattr', 'isinstance', 'issubclass', 'type', 'super', 'property',
                 'staticmethod', 'classmethod', 'object'}

    return loaded_names - builtins



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
            node_type = node_info.get("node_type", "compute")  # default to compute

            # For backward compatibility, map old "data" type to "data_source"
            if node_type == "data":
                node_type = "data_source"

            # Check if result is dict of DataFrames (directory) or single DataFrame (file)
            result_path = node_info.get("result_path")
            # Use is_dict_result from metadata if available, otherwise detect from path
            result_is_dict = node_info.get("is_dict_result", False)
            if not result_is_dict and result_path and node_info.get("execution_status") == "validated":
                from pathlib import Path
                full_result_path = Path(pm.project_path) / result_path
                if full_result_path.is_dir():
                    result_is_dict = True

            nodes.append({
                "id": node_info["node_id"],
                "label": node_info["name"],
                "type": node_type,  # Pass through backend type directly
                "execution_status": node_info.get("execution_status", "not_executed"),
                "result_format": node_info.get("result_format"),
                "result_path": result_path,
                "result_is_dict": result_is_dict,  # NEW: Indicates if result is dict of DataFrames
                "output": node_info.get("output"),  # Include output metadata for frontend display rules
                "error_message": node_info.get("error_message"),  # Error message if execution failed
                "last_execution_time": node_info.get("last_execution_time"),  # ISO timestamp of last execution
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


@app.get("/api/projects/{project_id}/nodes/{node_id}/dict-result")
def get_dict_result(project_id: str, node_id: str) -> Dict[str, Any]:
    """
    Get dict of DataFrames result for a node.

    Returns:
    {
        "keys": ["key1", "key2", "key3"],
        "tables": {
            "key1": [{"col1": val, "col2": val}, ...],
            "key2": [...],
            ...
        }
    }
    """
    try:
        pm = get_project_manager(project_id)
        import pandas as pd
        import json
        from pathlib import Path

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Find node info
        node_info = None
        for node in pm.metadata.nodes.values():
            if node["node_id"] == node_id:
                node_info = node
                break

        if node_info is None:
            raise HTTPException(status_code=404, detail="Node not found")

        result_path = node_info.get("result_path")
        if not result_path:
            raise HTTPException(status_code=404, detail="Node has no result")

        full_result_path = Path(pm.project_path) / result_path

        # Check if it's a dict result (directory)
        if not full_result_path.is_dir():
            raise HTTPException(status_code=400, detail="Result is not a dict of DataFrames")

        # Read metadata
        metadata_path = full_result_path / "_metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=400, detail="Dict result is missing metadata")

        with open(str(metadata_path), 'r') as f:
            metadata = json.load(f)

        keys = metadata.get("keys", [])

        # Load each DataFrame and convert to JSON-serializable format
        tables = {}
        for key in keys:
            parquet_path = full_result_path / f"{key}.parquet"
            if not parquet_path.exists():
                raise HTTPException(status_code=500, detail=f"DataFrame '{key}' not found")

            df = pd.read_parquet(str(parquet_path))
            # Convert to list of dicts for frontend consumption
            tables[key] = df.to_dict('records')

        return {
            "keys": keys,
            "tables": tables
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/dependencies")
def get_node_dependencies(project_id: str, node_id: str) -> Dict[str, Any]:
    """
    Get dependency information for a node

    This endpoint provides:
    - Direct dependencies (immediate parents)
    - All dependencies (transitive closure)
    - Execution order (topological sort)
    - Dependent nodes (who depends on this)

    Used for:
    - Showing execution preview before user confirms
    - Understanding dependency chains
    - Validating circular dependencies
    """
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Verify node exists
        if node_id not in pm.metadata.nodes:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        # Create dependency analyzer
        analyzer = DependencyAnalyzer(pm.metadata.nodes)

        # Get dependency info
        dep_info = analyzer.get_dependencies(node_id)

        return {
            "node_id": node_id,
            "direct_dependencies": dep_info["direct_dependencies"],
            "all_dependencies": dep_info["all_dependencies"],
            "execution_order": dep_info["execution_order"],
            "dependents": dep_info["dependents"],
            "has_circular_dependency": dep_info["has_circular_dependency"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/nodes/{node_id}/execution-plan")
def get_execution_plan(
    project_id: str,
    node_id: str,
    already_executed: Optional[str] = Query(None, description="Comma-separated list of already-executed node IDs")
) -> Dict[str, Any]:
    """
    Get execution plan for a node

    Considers already-executed nodes to avoid re-execution.

    Query parameters:
    - already_executed: Comma-separated list of node IDs that have been executed
                        (e.g., "load_orders_data,p1_category_sales")

    Returns:
    - execution_order: All nodes needed (in order)
    - nodes_to_execute: Only nodes that haven't been executed yet
    - already_executed: Nodes that will be skipped
    - will_skip: Count of nodes to skip
    - will_execute: Count of nodes to execute
    """
    try:
        pm = get_project_manager(project_id)

        if pm.metadata is None:
            raise HTTPException(status_code=500, detail="Failed to load project metadata")

        # Verify node exists
        if node_id not in pm.metadata.nodes:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        # Parse already_executed parameter
        already_executed_set = set()
        if already_executed:
            already_executed_set = set(already_executed.split(","))

        # Create dependency analyzer
        analyzer = DependencyAnalyzer(pm.metadata.nodes)

        # Get execution plan
        plan = analyzer.get_execution_plan(node_id, already_executed_set)

        return plan

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
def update_node_markdown(project_id: str, node_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
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


@app.put("/api/projects/{project_id}/nodes/{node_id}/code")
def update_node_code(project_id: str, node_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Update the code of a node in the notebook

    Updates the code cell linked to the node, and:
    1. Changes execution_status to 'not_executed'
    2. Analyzes code variables to update dependencies
    3. Updates project.json with new depends_on relationships
    4. Regenerates metadata comments with updated dependencies
    """
    print(f"DEBUG: update_node_code called with project_id={project_id}, node_id={node_id}", flush=True)
    try:
        pm = get_project_manager(project_id)
        print(f"DEBUG: Got project manager", flush=True)

        if pm.notebook_manager is None or pm.notebook_manager.notebook is None:
            raise HTTPException(status_code=500, detail="Failed to load notebook")

        code_content = body.get('code', '')

        # Step 1: Extract variable names used in the code
        used_variables = extract_variable_names(code_content)

        # Step 2: Load project.json to get node info and validate dependencies
        project_file = pm.metadata_path
        new_depends = []
        node_type = None
        node_name = None

        if project_file.exists():
            with open(project_file, 'r') as f:
                project_data = json.load(f)

            # Find the node in project.json
            for node in project_data.get('nodes', []):
                if node['node_id'] == node_id:
                    node_type = node.get('type')
                    node_name = node.get('name')

                    # Update depends_on based on variable names
                    # The variables used in code should match other node IDs
                    # Exclude the current node itself (to avoid circular dependencies)
                    for var_name in used_variables:
                        # Check if this variable name matches any node_id (but not itself)
                        if var_name != node_id and any(n['node_id'] == var_name for n in project_data.get('nodes', [])):
                            new_depends.append(var_name)

                    node['depends_on'] = new_depends
                    node['execution_status'] = 'not_executed'
                    break

            # Save updated project.json
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)

        # Step 3: Get notebook and find the code cell
        notebook = pm.notebook_manager.notebook
        cells = notebook.get('cells', [])

        # Find code cell with matching node_id and update it
        target_cell = None
        for cell in cells:
            if cell.get('cell_type') == 'code':
                metadata = cell.get('metadata', {})
                if metadata.get('node_id') == node_id:
                    target_cell = cell

                    # Step 4: Regenerate metadata comments with updated dependencies
                    # Get node type from metadata if not found in project.json
                    if not node_type:
                        node_type = metadata.get('type', 'compute')

                    # Generate new header with updated dependencies
                    header = NotebookManager._generate_header_from_metadata(
                        node_type=node_type,
                        node_id=node_id,
                        execution_status='not_executed',
                        depends_on=new_depends if new_depends else None,
                        name=node_name
                    )

                    # Combine header with code content
                    full_code = header + '\n\n' + code_content

                    # Update the cell source
                    # Convert to list format (Jupyter format)
                    lines = full_code.split('\n')
                    source = []
                    for i, line in enumerate(lines):
                        if i < len(lines) - 1:
                            source.append(line + '\n')
                        elif line:  # Only add last line if not empty
                            source.append(line)

                    cell['source'] = source

                    # Update metadata fields in cell
                    cell['metadata']['execution_status'] = 'not_executed'
                    cell['metadata']['depends_on'] = new_depends
                    break

        if target_cell is None:
            raise HTTPException(status_code=404, detail=f"Code not found for node {node_id}")

        # Save notebook
        pm.notebook_manager.save()

        return {
            "node_id": node_id,
            "code": code_content,
            "language": "python",
            "execution_status": "not_executed",
            "depends_on": new_depends
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in update_node_code: {error_msg}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/nodes/{node_id}/execute")
def execute_node(project_id: str, node_id: str) -> Dict[str, Any]:
    """
    Execute a node with intelligent dependency resolution.

    Workflow:
    1. Pre-check: does code assign same-named variable?
    2. Auto-append result-saving code if needed
    3. Build execution order (dependencies)
    4. Execute dependent nodes if needed
    5. Execute current node
    6. Post-check: verify variable exists and file saved
    7. Generate result cell to reload results
    8. Update node execution_status to 'validated'

    On error:
    - Set execution_status to 'pending_validation'
    - Store error_message in node
    - Return error details to frontend
    """
    try:
        from code_executor import CodeExecutor
        from kernel_manager import KernelManager

        pm = get_project_manager(project_id)

        if pm.notebook_manager is None:
            raise HTTPException(status_code=500, detail="Failed to load notebook")

        # Get dependency analysis before execution
        analyzer = DependencyAnalyzer(pm.metadata.nodes)
        execution_plan = analyzer.get_execution_plan(node_id)
        nodes_to_execute = execution_plan["nodes_to_execute"]
        execution_order = execution_plan["execution_order"]

        # Initialize kernel manager and code executor
        km = KernelManager(max_idle_time=300)
        executor = CodeExecutor(pm, km, pm.notebook_manager)

        # Execute the node
        result = executor.execute_node(node_id)

        # Build new edges from executed nodes
        # An edge exists between each node and its direct dependencies
        new_edges = []
        executed_nodes = [node_id]  # At minimum, the requested node was executed

        # Add edges for all executed nodes based on their dependencies
        for exec_node_id in execution_order:
            node_info = pm.metadata.nodes.get(exec_node_id, {})
            depends_on = node_info.get("depends_on", [])

            for dep in depends_on:
                edge_id = f"e_{dep}_{exec_node_id}"
                new_edges.append({
                    "id": edge_id,
                    "source": dep,
                    "target": exec_node_id,
                    "animated": False
                })

            if exec_node_id not in executed_nodes and exec_node_id in nodes_to_execute:
                executed_nodes.append(exec_node_id)

        # Return execution result with dependency information
        return {
            "node_id": node_id,
            "status": result.get("status", "error"),
            "error_message": result.get("error_message"),
            "execution_time": result.get("execution_time"),
            "result_cell_added": result.get("result_cell_added", False),
            # Dynamic dependency system additions
            "executed_nodes": execution_order,  # All nodes that were executed
            "new_edges": new_edges,  # All edges discovered during execution
            "execution_plan": {
                "execution_order": execution_order,
                "nodes_to_execute": nodes_to_execute,
                "already_executed": execution_plan["already_executed"],
                "will_execute": execution_plan["will_execute"],
                "will_skip": execution_plan["will_skip"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in execute_node: {error_msg}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
