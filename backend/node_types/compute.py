"""
Compute Node Type

Represents a computation node that processes data.
Output: DataFrame (required) - data for further computation or visualization
"""

from typing import Any, Dict
import pandas as pd
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat, OUTPUT_TO_RESULT_FORMAT


class ComputeNode(BaseNode):
    """
    Compute node that transforms and processes data.

    Constraints:
    - Must have at least one dependency
    - Must input DataFrames
    - Must output a DataFrame (for chaining with other compute or visualization nodes)
    - Cannot output dict/list (those are for analysis nodes)
    """

    node_type = "compute"

    def __init__(self, metadata: NodeMetadata):
        """Initialize a compute node"""
        if not metadata.depends_on:
            raise ValueError("Compute nodes must have at least one dependency")
        if metadata.node_type != self.node_type:
            raise ValueError(f"Expected node_type '{self.node_type}', got '{metadata.node_type}'")
        super().__init__(metadata)

    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate that all input data are DataFrames.

        Args:
            input_data: Dictionary mapping input names to data values

        Returns:
            True if all inputs are DataFrames, False otherwise
        """
        for key, value in input_data.items():
            if not isinstance(value, pd.DataFrame):
                return False
        return True

    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer output type. Compute nodes must output DataFrames.

        Args:
            result: The result from executing this node

        Returns:
            NodeOutput with output_type=DATAFRAME and display_type=TABLE

        Raises:
            TypeError: If result is not a DataFrame
        """
        if not isinstance(result, pd.DataFrame):
            raise TypeError(
                f"Compute node '{self.node_id}' must output a DataFrame, "
                f"got {type(result).__name__}. "
                f"For statistical/analytical results, use an 'analysis' node type instead."
            )

        return NodeOutput(
            output_type=OutputType.DATAFRAME,
            display_type=DisplayType.TABLE,
            result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.DATAFRAME],
            description=f"DataFrame with shape {result.shape}"
        )
