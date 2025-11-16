"""
Kernel Manager

Manages Jupyter kernel lifecycle and per-project kernel instances.
Handles:
- Kernel creation and cleanup
- Per-project kernel instances (one kernel per project)
- Code execution and result retrieval
- Variable inspection
- Timeout management
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

from jupyter_client import KernelManager as JupyterKernelManager
from jupyter_client.kernelspec import KernelSpecManager


class KernelInstance:
    """Represents a single Jupyter kernel instance"""

    def __init__(self, kernel_id: str, project_id: str, kernel_manager: JupyterKernelManager):
        """
        Initialize a kernel instance

        Args:
            kernel_id: Unique kernel identifier
            project_id: Associated project ID
            kernel_manager: Jupyter KernelManager instance
        """
        self.kernel_id = kernel_id
        self.project_id = project_id
        self.kernel_manager = kernel_manager
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_alive = True

    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def is_idle(self, timeout_seconds: int = 300) -> bool:
        """
        Check if kernel has been idle for specified duration

        Args:
            timeout_seconds: Timeout duration in seconds

        Returns:
            True if kernel has been idle longer than timeout
        """
        return (datetime.now() - self.last_activity).total_seconds() > timeout_seconds

    def cleanup(self) -> None:
        """Clean up and terminate kernel"""
        try:
            if self.kernel_manager.is_alive():
                self.kernel_manager.shutdown_kernel()
            self.is_alive = False
        except Exception as e:
            print(f"Error shutting down kernel {self.kernel_id}: {e}")
            self.is_alive = False


class KernelManager:
    """Manages Jupyter kernel instances for projects"""

    def __init__(self, max_idle_time: int = 300, max_kernels: int = 10):
        """
        Initialize KernelManager

        Args:
            max_idle_time: Maximum idle time in seconds before kernel is terminated
            max_kernels: Maximum number of concurrent kernels
        """
        self.max_idle_time = max_idle_time
        self.max_kernels = max_kernels
        self.kernels: Dict[str, KernelInstance] = {}  # kernel_id -> KernelInstance
        self.project_kernels: Dict[str, str] = {}  # project_id -> kernel_id
        self.project_cwd: Dict[str, str] = {}  # project_id -> working directory (新增)
        self.kernel_spec_manager = KernelSpecManager()

    def get_or_create_kernel(self, project_id: str, project_cwd: str = None) -> KernelInstance:
        """
        Get existing kernel for project or create a new one

        Args:
            project_id: Project identifier
            project_cwd: Project working directory (where to run the kernel)

        Returns:
            KernelInstance for the project
        """
        # Return existing kernel if available
        if project_id in self.project_kernels:
            kernel_id = self.project_kernels[project_id]
            if kernel_id in self.kernels:
                kernel = self.kernels[kernel_id]
                if kernel.is_alive:
                    kernel.update_activity()
                    return kernel

        # Create new kernel if limit not reached
        if len(self.kernels) >= self.max_kernels:
            self._cleanup_idle_kernels()

        if len(self.kernels) >= self.max_kernels:
            raise RuntimeError(f"Maximum kernel limit ({self.max_kernels}) reached")

        # Create and register new kernel
        # Use uv-managed kernel instead of system python3 for better dependency management
        kernel_id = f"kernel_{uuid.uuid4().hex[:8]}"
        try:
            # Try to use uv-managed kernel first
            jupyter_km = JupyterKernelManager(kernel_name="uv-python")
            # 问题修复: 设置工作目录到项目目录
            if project_cwd:
                jupyter_km.start_kernel(cwd=project_cwd)
            else:
                jupyter_km.start_kernel()
        except Exception as e:
            # Fall back to system python3 if uv-python kernel not available
            print(f"[Warning] uv-python kernel not available, falling back to python3: {e}")
            jupyter_km = JupyterKernelManager(kernel_name="python3")
            # 问题修复: 设置工作目录到项目目录
            if project_cwd:
                jupyter_km.start_kernel(cwd=project_cwd)
            else:
                jupyter_km.start_kernel()

        kernel = KernelInstance(kernel_id, project_id, jupyter_km)
        self.kernels[kernel_id] = kernel
        self.project_kernels[project_id] = kernel_id
        # 存储项目的工作目录
        if project_cwd:
            self.project_cwd[project_id] = project_cwd

        return kernel

    def get_kernel(self, project_id: str) -> Optional[KernelInstance]:
        """
        Get existing kernel for project without creating new one

        Args:
            project_id: Project identifier

        Returns:
            KernelInstance or None if not found
        """
        if project_id not in self.project_kernels:
            return None

        kernel_id = self.project_kernels[project_id]
        if kernel_id not in self.kernels:
            return None

        kernel = self.kernels[kernel_id]
        if kernel.is_alive:
            kernel.update_activity()
            return kernel

        # Clean up dead kernel
        del self.kernels[kernel_id]
        del self.project_kernels[project_id]
        return None

    def execute_code(
        self,
        project_id: str,
        code: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute code in project's kernel

        Args:
            project_id: Project identifier
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            Dict with execution results:
            {
                "status": "success" | "error" | "timeout",
                "output": str,
                "error": str or None,
                "result": Any or None
            }
        """
        kernel = self.get_or_create_kernel(project_id)

        try:
            client = kernel.kernel_manager.client()
            client.start_channels()

            # Execute code
            msg_id = client.execute(code)
            kernel.update_activity()

            # Collect output
            output = ""
            error = None
            start_time = datetime.now()
            execution_complete = False

            while not execution_complete:
                # Check timeout
                if (datetime.now() - start_time).total_seconds() > timeout:
                    client.stop_channels()
                    return {
                        "status": "timeout",
                        "output": output,
                        "error": f"Execution timeout ({timeout}s)",
                        "result": None
                    }

                try:
                    msg = client.get_iopub_msg(timeout=0.1)
                except:
                    # Check for shell reply
                    try:
                        reply = client.get_shell_msg(timeout=0.1)
                        if reply.get("parent_header", {}).get("msg_id") == msg_id:
                            execution_complete = True
                    except:
                        pass
                    continue

                msg_type = msg.get("msg_type", "")
                content = msg.get("content", {})
                msg_parent_id = msg.get("parent_header", {}).get("msg_id", "")

                # Only process messages related to our execution
                if msg_parent_id != msg_id:
                    continue

                # Collect output
                if msg_type == "stream":
                    output += content.get("text", "")
                elif msg_type == "display_data":
                    # Store display data
                    data = content.get("data", {})
                    if "text/plain" in data:
                        output += data["text/plain"] + "\n"
                elif msg_type == "execute_result":
                    data = content.get("data", {})
                    if "text/plain" in data:
                        output += data["text/plain"] + "\n"
                elif msg_type == "error":
                    error = "\n".join(content.get("traceback", []))
                elif msg_type == "status":
                    if content.get("execution_state") == "idle":
                        execution_complete = True

            client.stop_channels()
            kernel.update_activity()

            return {
                "status": "error" if error else "success",
                "output": output,
                "error": error,
                "result": None
            }

        except Exception as e:
            kernel.update_activity()
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "result": None
            }

    def get_variable(self, project_id: str, var_name: str) -> Any:
        """
        Get variable value from kernel

        Args:
            project_id: Project identifier
            var_name: Variable name

        Returns:
            Variable value or None if not found

        Raises:
            RuntimeError: If kernel not found or variable doesn't exist
        """
        kernel = self.get_kernel(project_id)
        if kernel is None:
            raise RuntimeError(f"No kernel found for project {project_id}")

        try:
            client = kernel.kernel_manager.client()
            client.start_channels()

            # Request variable value
            code = f"__var_value = {var_name}; __var_type = type({var_name}).__name__"
            msg_id = client.execute(code)

            # Wait for execution
            while True:
                try:
                    msg = client.get_iopub_msg(timeout=1)
                    if msg.get("msg_type") == "status":
                        if msg.get("content", {}).get("execution_state") == "idle":
                            break
                except:
                    continue

            # Get variable value
            code_get = "__var_value"
            msg_id = client.execute(code_get)
            output = ""

            while True:
                try:
                    msg = client.get_iopub_msg(timeout=1)
                    msg_type = msg.get("msg_type", "")

                    if msg_type == "stream":
                        output += msg.get("content", {}).get("text", "")
                    elif msg_type == "display_data":
                        data = msg.get("content", {}).get("data", {})
                        if "text/plain" in data:
                            output += data["text/plain"]
                    elif msg_type == "status":
                        if msg.get("content", {}).get("execution_state") == "idle":
                            break
                except:
                    continue

            client.stop_channels()
            kernel.update_activity()

            # Try to parse JSON value
            try:
                return json.loads(output.strip())
            except:
                return output.strip()

        except Exception as e:
            raise RuntimeError(f"Error getting variable {var_name}: {e}")

    def list_variables(self, project_id: str) -> List[str]:
        """
        List all variables in kernel namespace

        Args:
            project_id: Project identifier

        Returns:
            List of variable names

        Raises:
            RuntimeError: If kernel not found
        """
        kernel = self.get_kernel(project_id)
        if kernel is None:
            raise RuntimeError(f"No kernel found for project {project_id}")

        try:
            result = self.execute_code(project_id, "dir()")

            if result["status"] == "error":
                return []

            # Parse output to get variable names
            output = result["output"].strip()
            # Simple parsing of Python list output
            output = output.replace("[", "").replace("]", "").replace("'", "")
            variables = [v.strip() for v in output.split(",") if v.strip()]

            return variables

        except Exception as e:
            raise RuntimeError(f"Error listing variables: {e}")

    def shutdown_kernel(self, project_id: str) -> None:
        """
        Shutdown kernel for a project

        Args:
            project_id: Project identifier
        """
        if project_id not in self.project_kernels:
            return

        kernel_id = self.project_kernels[project_id]
        if kernel_id in self.kernels:
            kernel = self.kernels[kernel_id]
            kernel.cleanup()
            del self.kernels[kernel_id]

        del self.project_kernels[project_id]

    def shutdown_all(self) -> None:
        """Shutdown all kernels"""
        for kernel in list(self.kernels.values()):
            kernel.cleanup()

        self.kernels.clear()
        self.project_kernels.clear()

    def _cleanup_idle_kernels(self) -> None:
        """Remove idle kernels to free up resources"""
        dead_kernel_ids = []

        for kernel_id, kernel in self.kernels.items():
            if kernel.is_idle(self.max_idle_time):
                kernel.cleanup()
                dead_kernel_ids.append(kernel_id)

        # Clean up references
        for kernel_id in dead_kernel_ids:
            del self.kernels[kernel_id]
            # Find and remove from project_kernels
            for project_id, kid in list(self.project_kernels.items()):
                if kid == kernel_id:
                    del self.project_kernels[project_id]

    def get_kernel_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about kernel for a project

        Args:
            project_id: Project identifier

        Returns:
            Dict with kernel info or None if not found
        """
        if project_id not in self.project_kernels:
            return None

        kernel_id = self.project_kernels[project_id]
        if kernel_id not in self.kernels:
            return None

        kernel = self.kernels[kernel_id]
        return {
            "kernel_id": kernel.kernel_id,
            "project_id": kernel.project_id,
            "created_at": kernel.created_at.isoformat(),
            "last_activity": kernel.last_activity.isoformat(),
            "is_alive": kernel.is_alive,
            "idle_seconds": (datetime.now() - kernel.last_activity).total_seconds()
        }

    def get_all_kernels_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all active kernels

        Returns:
            List of kernel info dicts
        """
        return [
            {
                "kernel_id": kernel.kernel_id,
                "project_id": kernel.project_id,
                "created_at": kernel.created_at.isoformat(),
                "last_activity": kernel.last_activity.isoformat(),
                "is_alive": kernel.is_alive,
                "idle_seconds": (datetime.now() - kernel.last_activity).total_seconds()
            }
            for kernel in self.kernels.values()
        ]
