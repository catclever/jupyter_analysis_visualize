"""
Chart Node Type

Represents a visualization node that creates interactive charts.
Output: Plotly Figure or ECharts configuration (JSON)

Note: For static image outputs (PNG, JPG, etc.), use ImageNode instead.
"""

from typing import Any
import plotly.graph_objects as go
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat, OUTPUT_TO_RESULT_FORMAT


class ChartNode(BaseNode):
    """
    Interactive chart/visualization node that creates interactive visualizations.

    Constraints:
    - Can have dependencies on any node type
    - Outputs either Plotly Figure or ECharts configuration (stored as JSON)
    - Typically a leaf node (not depended on by other nodes)

    Supported formats:
    - Plotly Figure objects (rendered as interactive HTML charts)
    - ECharts configuration dicts (with xAxis, yAxis, series, etc.)

    Output Types: PLOTLY, ECHARTS
    Storage: JSON format, saved to visualizations/ directory
    """

    node_type = "chart"

    # What output types this node can produce
    supported_output_types = [OutputType.PLOTLY, OutputType.ECHARTS]

    # How to store each output type
    output_storage_config = {
        OutputType.PLOTLY: {
            'save_format': ResultFormat.JSON.value,
            'result_path_pattern': 'visualizations/{node_id}.json',
        },
        OutputType.ECHARTS: {
            'save_format': ResultFormat.JSON.value,
            'result_path_pattern': 'visualizations/{node_id}.json',
        },
    }

    def __init__(self, metadata: NodeMetadata):
        """Initialize a chart node"""
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
        # Check for Plotly Figure
        if isinstance(result, go.Figure):
            output_type = OutputType.PLOTLY
            storage_config = self.get_storage_config(output_type)
            return NodeOutput(
                output_type=output_type,
                display_type=DisplayType.PLOTLY_CHART,
                result_format=ResultFormat(storage_config['save_format']),
                description="Plotly interactive visualization"
            )

        # Check for ECharts configuration (dict with specific structure)
        if isinstance(result, dict):
            # ECharts configs typically have xAxis/yAxis or series
            if any(key in result for key in ['xAxis', 'yAxis', 'series', 'legend']):
                output_type = OutputType.ECHARTS
                storage_config = self.get_storage_config(output_type)
                return NodeOutput(
                    output_type=output_type,
                    display_type=DisplayType.ECHARTS_CHART,
                    result_format=ResultFormat(storage_config['save_format']),
                    description="ECharts visualization configuration"
                )

        raise TypeError(
            f"Chart node '{self.node_id}' must output either a Plotly Figure "
            f"or ECharts configuration dict, got {type(result).__name__}"
        )
