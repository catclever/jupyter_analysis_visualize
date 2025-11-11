"""
Chart Node Type

Represents a visualization node that creates charts and visualizations.
Output: Plotly Figure or ECharts configuration
"""

from typing import Any, Dict
import plotly.graph_objects as go
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat, OUTPUT_TO_RESULT_FORMAT


class ChartNode(BaseNode):
    """
    Chart/visualization node that creates interactive visualizations.

    Constraints:
    - Can have dependencies on any node type
    - Outputs either Plotly Figure or ECharts configuration
    - Typically a leaf node (not depended on by other nodes)
    """

    node_type = "chart"

    def __init__(self, metadata: NodeMetadata):
        """Initialize a chart node"""
        if metadata.node_type != self.node_type:
            raise ValueError(f"Expected node_type '{self.node_type}', got '{metadata.node_type}'")
        super().__init__(metadata)

    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """
        Chart nodes accept any type of input.

        Args:
            input_data: Dictionary of input values

        Returns:
            Always True (charts are flexible in what they accept)
        """
        return True

    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer output type from the result.

        Args:
            result: The result from executing this node

        Returns:
            NodeOutput describing the visualization

        Raises:
            TypeError: If result is not a supported visualization type
        """
        # Check for Plotly Figure
        if isinstance(result, go.Figure):
            return NodeOutput(
                output_type=OutputType.PLOTLY,
                display_type=DisplayType.PLOTLY_CHART,
                result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.PLOTLY],
                description="Plotly interactive visualization"
            )

        # Check for ECharts configuration (dict with specific structure)
        if isinstance(result, dict):
            # ECharts configs typically have xAxis/yAxis or series
            if any(key in result for key in ['xAxis', 'yAxis', 'series', 'legend']):
                return NodeOutput(
                    output_type=OutputType.ECHARTS,
                    display_type=DisplayType.ECHARTS_CHART,
                    result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.ECHARTS],
                    description="ECharts visualization configuration"
                )

        raise TypeError(
            f"Chart node '{self.node_id}' must output either a Plotly Figure "
            f"or ECharts configuration dict, got {type(result).__name__}"
        )
