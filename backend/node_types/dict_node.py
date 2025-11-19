"""
Dictionary Node Type

Represents a node that outputs a dictionary (dict of DataFrames, dict of values, etc).
Output: dict (required)
"""

from typing import Any, Dict
import pandas as pd
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat


class DictNode(BaseNode):
    """
    Dictionary node that outputs a dictionary of values or DataFrames.

    Constraints:
    - Can have dependencies or no dependencies
    - Output: Must be a dict
    - Values can be DataFrames, scalars, lists, or any serializable objects

    Output Types: DICT_LIST (dict of DataFrames) or JSON (plain dict)
    Storage: PARQUET (multiple files in directory) or JSON format
    """

    node_type = "dict"

    # What output types this node can produce
    supported_output_types = [OutputType.DICT_LIST]

    # How to store each output type
    output_storage_config = {
        OutputType.DICT_LIST: {
            'save_format': ResultFormat.PARQUET.value,
            'result_path_pattern': 'parquets/{node_id}',
        }
    }

    def __init__(self, metadata: NodeMetadata):
        """Initialize a dict node"""
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
        if not isinstance(result, dict):
            raise TypeError(
                f"Dict node '{self.node_id}' must output a dict, "
                f"got {type(result).__name__}"
            )

        # Check if this is a dict of DataFrames or a plain dict
        has_dataframes = any(isinstance(v, pd.DataFrame) for v in result.values())

        # Result matches supported output types, build output metadata
        if has_dataframes:
            output_type = OutputType.DICT_LIST
            display_type = DisplayType.TABLE  # Display as dict of tables
        else:
            output_type = OutputType.DICT_LIST
            display_type = DisplayType.TABLE  # Display as dict/JSON

        storage_config = self.get_storage_config(output_type)

        return NodeOutput(
            output_type=output_type,
            display_type=display_type,
            result_format=ResultFormat(storage_config['save_format']),
            description=f"Dict with keys {list(result.keys())}"
        )
