"""
Execution Manager

Manages node execution with dependency resolution, result persistence, and error handling.
Handles:
- DAG-based execution with dependency resolution
- Node execution with proper variable management
- Result auto-saving (parquet/JSON)
- Error handling and recovery
- Breakpoint support and recovery
- Execution progress tracking
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from kernel_manager import KernelManager
from project_manager import ProjectManager
from node_types import get_node_type, NodeMetadata, NodeOutput


class ExecutionStatus(Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class NodeExecution:
    """Represents execution state of a single node"""

    def __init__(self, node_id: str, node_type: str):
        """
        Initialize node execution tracker

        Args:
            node_id: Node identifier
            node_type: Type of node (data_source, compute, chart, tool)
        """
        self.node_id = node_id
        self.node_type = node_type
        self.status = ExecutionStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.output = ""
        self.error: Optional[str] = None
        self.result: Optional[Any] = None
        self.duration_seconds = 0.0

    def start(self) -> None:
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()

    def complete(self, result: Optional[Any] = None, error: Optional[str] = None) -> None:
        """
        Mark execution as completed

        Args:
            result: Execution result
            error: Error message if any
        """
        self.end_time = datetime.now()
        self.result = result
        self.error = error

        if error:
            self.status = ExecutionStatus.ERROR
        else:
            self.status = ExecutionStatus.SUCCESS

        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def skip(self) -> None:
        """Mark execution as skipped (e.g., result already exists)"""
        self.status = ExecutionStatus.SKIPPED
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds
        }


class ExecutionManager:
    """Manages node execution with dependency resolution"""

    def __init__(self, kernel_manager: KernelManager, project_manager: ProjectManager):
        """
        Initialize ExecutionManager

        Args:
            kernel_manager: KernelManager instance
            project_manager: ProjectManager instance
        """
        self.kernel_manager = kernel_manager
        self.project_manager = project_manager

    def get_dependency_order(self, project_id: str) -> List[str]:
        """
        Get topological order of nodes based on dependencies (DAG traversal)

        Args:
            project_id: Project identifier

        Returns:
            List of node IDs in execution order

        Raises:
            RuntimeError: If circular dependency detected
        """
        nodes = self.project_manager.list_nodes()
        node_dict = {node['node_id']: node for node in nodes}

        # Build adjacency list
        graph = {node_id: [] for node_id in node_dict}
        in_degree = {node_id: 0 for node_id in node_dict}

        for node_id, node in node_dict.items():
            depends_on = node.get('depends_on', [])
            for dep in depends_on:
                if dep in graph:
                    graph[dep].append(node_id)
                    in_degree[node_id] += 1

        # Topological sort using Kahn's algorithm
        queue = [node_id for node_id in node_dict if in_degree[node_id] == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(node_dict):
            raise RuntimeError("Circular dependency detected in project DAG")

        return result

    def execute_node(
        self,
        project_id: str,
        node_id: str,
        skip_existing: bool = True,
        timeout: int = 30
    ) -> NodeExecution:
        """
        Execute a single node

        Args:
            project_id: Project identifier
            node_id: Node identifier
            skip_existing: Skip execution if result already exists (for data/compute nodes)
            timeout: Execution timeout in seconds

        Returns:
            NodeExecution with results
        """
        node = self.project_manager.get_node(node_id)
        if not node:
            raise RuntimeError(f"Node {node_id} not found")

        execution = NodeExecution(node_id, node['type'])
        execution.start()

        # Tool nodes always execute (to load functions)
        # Data nodes skip if results exist
        if skip_existing and node['type'] in ["data_source", "compute"]:
            try:
                result = self.project_manager.load_node_result(node_id)
                execution.skip()
                execution.result = result
                execution.end_time = datetime.now()
                return execution
            except FileNotFoundError:
                pass  # Proceed with execution

        # Get node code from notebook
        notebook_cells = self.project_manager.notebook_manager.get_cells()
        node_cell = None

        for cell in notebook_cells:
            metadata = cell.get('metadata', {})
            if metadata.get('node_id') == node_id:
                node_cell = cell
                break

        if not node_cell:
            execution.complete(error=f"Node code not found for {node_id}")
            return execution

        code = node_cell.get('source', '')
        if isinstance(code, list):
            code = ''.join(code)

        # Execute code
        result = self.kernel_manager.execute_code(project_id, code, timeout=timeout)
        execution.output = result['output']

        if result['status'] == 'error':
            execution.complete(error=result['error'])
        elif result['status'] == 'timeout':
            execution.complete(error=f"Timeout after {timeout}s")
        else:
            # For tool nodes, no result to save
            if node['type'] == 'tool':
                execution.complete(result=None)
            else:
                # For data/compute/chart nodes, try to retrieve result from kernel
                # Try to get variable with node_id
                try:
                    var_value = self.kernel_manager.get_variable(project_id, node_id)
                    # Auto-save result
                    saved_path = self.project_manager.save_node_result(node_id, var_value)
                    execution.complete(result=var_value)
                except Exception as e:
                    # If variable retrieval fails, save output instead
                    execution.complete(result=result['output'])

        return execution

    def infer_output_type(self, node_id: str, result: Any) -> NodeOutput:
        """
        Infer the output type of a node's result using the node type system.

        Args:
            node_id: Node identifier
            result: The execution result

        Returns:
            NodeOutput instance with output_type and display_type

        Raises:
            ValueError: If node type is unknown
            TypeError: If result doesn't match node's output constraints
        """
        node = self.project_manager.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        node_type_str = node.get('type')
        if not node_type_str:
            raise ValueError(f"Node {node_id} has no type")

        # Get node class and instantiate it
        try:
            NodeClass = get_node_type(node_type_str)
        except ValueError as e:
            raise ValueError(f"Unknown node type '{node_type_str}' for node {node_id}: {e}")

        # Create minimal metadata for the node
        metadata = NodeMetadata(
            node_id=node_id,
            node_type=node_type_str,
            name=node.get('name', node_id),
            depends_on=node.get('depends_on', [])
        )

        # Instantiate the node
        try:
            node_instance = NodeClass(metadata)
        except ValueError as e:
            raise ValueError(f"Failed to create node instance: {e}")

        # Use the node to infer output type
        return node_instance.infer_output(result)

    def execute_project(
        self,
        project_id: str,
        node_ids: Optional[List[str]] = None,
        skip_existing: bool = True,
        timeout: int = 30
    ) -> Dict[str, NodeExecution]:
        """
        Execute project nodes with dependency resolution

        Args:
            project_id: Project identifier
            node_ids: Specific nodes to execute (all if None)
            skip_existing: Skip execution if result exists
            timeout: Execution timeout per node

        Returns:
            Dict of node_id -> NodeExecution results
        """
        # Get execution order
        try:
            execution_order = self.get_dependency_order(project_id)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to plan execution: {e}")

        # Filter to requested nodes if specified
        if node_ids:
            requested_set = set(node_ids)
            execution_order = [n for n in execution_order if n in requested_set]

        results = {}

        for node_id in execution_order:
            try:
                execution = self.execute_node(
                    project_id,
                    node_id,
                    skip_existing=skip_existing,
                    timeout=timeout
                )
                results[node_id] = execution

                # Stop on error unless it's a tool node
                node = self.project_manager.get_node(node_id)
                if execution.status == ExecutionStatus.ERROR and node['type'] != 'tool':
                    break

            except Exception as e:
                execution = NodeExecution(node_id, "unknown")
                execution.status = ExecutionStatus.ERROR
                execution.error = str(e)
                results[node_id] = execution
                break

        return results

    def execute_with_breakpoint(
        self,
        project_id: str,
        breakpoint_node_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, NodeExecution]:
        """
        Execute project with breakpoint recovery

        Strategy:
        1. Always execute all TOOL nodes first (to restore functions)
        2. Execute other nodes until breakpoint or error
        3. Load results from parquet on demand

        Args:
            project_id: Project identifier
            breakpoint_node_id: Node ID to stop at (None = execute all)
            timeout: Execution timeout per node

        Returns:
            Dict of node_id -> NodeExecution results
        """
        results = {}

        # Step 1: Execute all tool nodes first
        tool_nodes = self.project_manager.list_nodes_by_type('tool')
        for node in tool_nodes:
            execution = self.execute_node(
                project_id,
                node['node_id'],
                skip_existing=False,  # Always re-execute tools
                timeout=timeout
            )
            results[node['node_id']] = execution

            if execution.status == ExecutionStatus.ERROR:
                return results  # Stop on tool error

        # Step 2: Get execution order
        try:
            execution_order = self.get_dependency_order(project_id)
        except RuntimeError as e:
            return results

        # Filter to non-tool nodes
        execution_order = [
            n for n in execution_order
            if self.project_manager.get_node(n)['type'] != 'tool'
        ]

        # Step 3: Execute nodes with breakpoint
        for node_id in execution_order:
            if breakpoint_node_id and node_id == breakpoint_node_id:
                # Reached breakpoint
                break

            if node_id in results:
                continue  # Already executed

            execution = self.execute_node(
                project_id,
                node_id,
                skip_existing=True,  # Skip if result exists
                timeout=timeout
            )
            results[node_id] = execution

            if execution.status == ExecutionStatus.ERROR:
                break

        return results

    def get_execution_summary(self, executions: Dict[str, NodeExecution]) -> Dict[str, Any]:
        """
        Get summary of execution results

        Args:
            executions: Dict of node_id -> NodeExecution

        Returns:
            Summary dict with stats and results
        """
        total = len(executions)
        success = sum(1 for e in executions.values() if e.status == ExecutionStatus.SUCCESS)
        error = sum(1 for e in executions.values() if e.status == ExecutionStatus.ERROR)
        skipped = sum(1 for e in executions.values() if e.status == ExecutionStatus.SKIPPED)
        total_duration = sum(e.duration_seconds for e in executions.values())

        return {
            "total_nodes": total,
            "success": success,
            "error": error,
            "skipped": skipped,
            "total_duration_seconds": total_duration,
            "executions": {node_id: execution.to_dict() for node_id, execution in executions.items()}
        }
