"""
Data Source Node Type

Represents a node that loads data from external sources.
Output: DataFrame (required)
"""

from typing import Any, Dict
import pandas as pd
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat, OUTPUT_TO_RESULT_FORMAT


class DataSourceNode(BaseNode):
    """
    Data source node that loads data from external files or databases.

    Constraints:
    - No dependencies (depends_on must be empty)
    - Always outputs a DataFrame
    - Can be depended on by any other node type

    Output Types: DATAFRAME
    Storage: PARQUET format, saved to parquets/ directory
    """

    node_type = "data_source"

    # What output types this node can produce
    supported_output_types = [OutputType.DATAFRAME]

    # How to store each output type
    output_storage_config = {
        OutputType.DATAFRAME: {
            'save_format': ResultFormat.PARQUET.value,
            'result_path_pattern': 'parquets/{node_id}.parquet',
        }
    }

    def __init__(self, metadata: NodeMetadata):
        """Initialize a data source node"""
        if metadata.depends_on:
            raise ValueError("Data source nodes cannot have dependencies")
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
            TypeError: If result type doesn't match supported output types
        """
        if not isinstance(result, pd.DataFrame):
            raise TypeError(
                f"Data source node '{self.node_id}' must output a DataFrame, "
                f"got {type(result).__name__}"
            )

        # Result matches supported output types, build output metadata
        output_type = OutputType.DATAFRAME
        storage_config = self.get_storage_config(output_type)

        return NodeOutput(
            output_type=output_type,
            display_type=DisplayType.TABLE,
            result_format=ResultFormat(storage_config['save_format']),
            description=f"DataFrame with shape {result.shape}"
        )
