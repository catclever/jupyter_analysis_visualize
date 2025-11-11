"""
Data Source Node Type

Represents a node that loads data from external sources.
Output: DataFrame (required)
"""

from typing import Any, Dict
import pandas as pd
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType


class DataSourceNode(BaseNode):
    """
    Data source node that loads data from external files or databases.

    Constraints:
    - No dependencies (depends_on must be empty)
    - Always outputs a DataFrame
    - Can be depended on by any other node type
    """

    node_type = "data_source"

    def __init__(self, metadata: NodeMetadata):
        """Initialize a data source node"""
        if metadata.depends_on:
            raise ValueError("Data source nodes cannot have dependencies")
        if metadata.node_type != self.node_type:
            raise ValueError(f"Expected node_type '{self.node_type}', got '{metadata.node_type}'")
        super().__init__(metadata)

    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """
        Data source nodes have no input validation (they load their own data).

        Returns:
            Always True
        """
        return True

    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer output type. Data source nodes must output DataFrames.

        Args:
            result: The result from executing this node

        Returns:
            NodeOutput with output_type=DATAFRAME and display_type=TABLE

        Raises:
            TypeError: If result is not a DataFrame
        """
        if not isinstance(result, pd.DataFrame):
            raise TypeError(
                f"Data source node '{self.node_id}' must output a DataFrame, "
                f"got {type(result).__name__}"
            )

        return NodeOutput(
            output_type=OutputType.DATAFRAME,
            display_type=DisplayType.TABLE,
            description=f"DataFrame with shape {result.shape}"
        )
