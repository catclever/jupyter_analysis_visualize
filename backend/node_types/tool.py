"""
Tool Node Type

Represents a node that produces callable function objects.
Output: Function (Python callable) - can be invoked by other nodes
"""

from typing import Any
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat


class ToolNode(BaseNode):
    """
    Tool node that produces callable function objects.

    Constraints:
    - Must have at least one dependency (or can be standalone if no dependencies)
    - Input: Can be any type (no input type restriction)
    - Output: Must be a callable (function, class, or any callable object)

    Output Types: FUNCTION
    Storage: PKL format (pickle), saved to functions/ directory

    Use Case:
    - Define reusable tool functions
    - Create function factories
    - Implement higher-order functions
    - Build transformation pipelines

    Best Practice:
    - Define all dependent functions in the same cell as a closure
    - Return the main entry function as the output
    - Pickle will capture the entire closure
    """

    node_type = "tool"

    # What output types this node can produce
    supported_output_types = [OutputType.FUNCTION]

    # How to store each output type
    output_storage_config = {
        OutputType.FUNCTION: {
            'save_format': ResultFormat.PKL.value,
            'result_path_pattern': 'functions/{node_id}.pkl',
        }
    }

    def __init__(self, metadata: NodeMetadata):
        """Initialize a tool node"""
        if metadata.node_type != self.node_type:
            raise ValueError(f"Expected node_type '{self.node_type}', got '{metadata.node_type}'")
        super().__init__(metadata)

    def infer_output(self, result: Any) -> NodeOutput:
        """
        Validate result matches declared output and return NodeOutput.

        Args:
            result: The result from executing this node

        Returns:
            NodeOutput with metadata for the result

        Raises:
            TypeError: If result is not callable
        """
        if not callable(result):
            raise TypeError(
                f"Tool node '{self.node_id}' must output a callable, "
                f"got {type(result).__name__}"
            )

        # Result matches supported output types, build output metadata
        output_type = OutputType.FUNCTION
        storage_config = self.get_storage_config(output_type)

        # Get function name for description
        func_name = getattr(result, '__name__', 'anonymous')

        return NodeOutput(
            output_type=output_type,
            display_type=DisplayType.NONE,  # Functions are not displayed, only called
            result_format=ResultFormat(storage_config['save_format']),
            description=f"Callable: {func_name}"
        )
