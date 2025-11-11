"""
Base Node Type Class

Defines the interface and common functionality for all node types.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class OutputType(Enum):
    """Enumeration of possible output types"""
    DATAFRAME = "dataframe"
    DICT_LIST = "dict_list"
    PLOTLY = "plotly"
    ECHARTS = "echarts"
    FUNCTION = "function"
    UNKNOWN = "unknown"


class DisplayType(Enum):
    """Enumeration of display types for frontend rendering"""
    TABLE = "table"
    JSON_VIEWER = "json_viewer"
    PLOTLY_CHART = "plotly_chart"
    ECHARTS_CHART = "echarts_chart"
    NONE = "none"


class ResultFormat(Enum):
    """Enumeration of result file storage formats"""
    PARQUET = "parquet"  # For DataFrames
    JSON = "json"        # For dict/list and chart configs
    NONE = "none"        # For functions (no file storage)


# Mapping from OutputType to ResultFormat
OUTPUT_TO_RESULT_FORMAT = {
    OutputType.DATAFRAME: ResultFormat.PARQUET,
    OutputType.DICT_LIST: ResultFormat.JSON,
    OutputType.PLOTLY: ResultFormat.JSON,
    OutputType.ECHARTS: ResultFormat.JSON,
    OutputType.FUNCTION: ResultFormat.NONE,
    OutputType.UNKNOWN: ResultFormat.JSON,
}


@dataclass
class NodeOutput:
    """
    Standardized output description for a node.

    Attributes:
        output_type: Type of the output (dataframe, dict_list, plotly, echarts, function)
        display_type: How to display the output on frontend (table, json_viewer, chart, none)
        result_format: How to store the result (parquet, json, none)
        description: Human-readable description of the output
    """
    output_type: OutputType
    display_type: DisplayType
    result_format: ResultFormat
    description: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            'output_type': self.output_type.value,
            'display_type': self.display_type.value,
            'result_format': self.result_format.value,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'NodeOutput':
        """Create from dictionary"""
        return cls(
            output_type=OutputType(data['output_type']),
            display_type=DisplayType(data['display_type']),
            result_format=ResultFormat(data['result_format']),
            description=data.get('description', '')
        )


@dataclass
class NodeMetadata:
    """
    Metadata for a node instance.

    Attributes:
        node_id: Unique identifier for the node
        node_type: Type of the node (data_source, compute, chart, etc.)
        name: Human-readable name
        description: Long description of what the node does
        depends_on: List of node IDs this node depends on
        output: Output specification
    """
    node_id: str
    node_type: str
    name: str
    description: str = ""
    depends_on: List[str] = None
    output: Optional[NodeOutput] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'name': self.name,
            'description': self.description,
            'depends_on': self.depends_on,
            'output': self.output.to_dict() if self.output else None
        }


class BaseNode(ABC):
    """
    Abstract base class for all node types.

    Each concrete node type (DataSourceNode, ComputeNode, ChartNode, etc.)
    should inherit from this class and implement the required methods.
    """

    def __init__(self, metadata: NodeMetadata):
        """
        Initialize a node with metadata.

        Args:
            metadata: NodeMetadata instance containing node information
        """
        self.metadata = metadata

    @property
    def node_id(self) -> str:
        """Get node ID"""
        return self.metadata.node_id

    @property
    def node_type(self) -> str:
        """Get node type"""
        return self.metadata.node_type

    @abstractmethod
    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate if the provided input data matches this node's requirements.

        Args:
            input_data: Dictionary of input values

        Returns:
            True if inputs are valid, False otherwise
        """
        pass

    @abstractmethod
    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer the output type and display type from the execution result.

        Args:
            result: The actual output from executing this node

        Returns:
            NodeOutput instance describing the output
        """
        pass

    def get_metadata_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary for storage"""
        return self.metadata.to_dict()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.node_id}, type={self.node_type})"
