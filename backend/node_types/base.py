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
    PLOTLY = "plotly"              # Interactive chart (Plotly)
    ECHARTS = "echarts"            # Interactive chart (ECharts)
    IMAGE = "image"                # Static image (PNG, JPG, etc.)
    FUNCTION = "function"
    UNKNOWN = "unknown"


class DisplayType(Enum):
    """Enumeration of display types for frontend rendering"""
    TABLE = "table"
    JSON_VIEWER = "json_viewer"
    PLOTLY_CHART = "plotly_chart"
    ECHARTS_CHART = "echarts_chart"
    IMAGE_VIEWER = "image_viewer"  # For static images
    NONE = "none"


class ResultFormat(Enum):
    """Enumeration of result file storage formats"""
    PARQUET = "parquet"  # For DataFrames
    JSON = "json"        # For dict/list and interactive chart configs
    IMAGE = "image"      # For PNG, JPG, etc.
    PKL = "pkl"          # For general Python objects (functions, custom objects)
    NONE = "none"        # For functions (no file storage)


# Mapping from OutputType to ResultFormat
OUTPUT_TO_RESULT_FORMAT = {
    OutputType.DATAFRAME: ResultFormat.PARQUET,
    OutputType.DICT_LIST: ResultFormat.JSON,
    OutputType.PLOTLY: ResultFormat.JSON,
    OutputType.ECHARTS: ResultFormat.JSON,
    OutputType.IMAGE: ResultFormat.IMAGE,
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

    Class-level attributes that subclasses should define:
        node_type: Unique identifier for the node type (e.g., 'data_source')
        supported_output_types: List of OutputType this node can produce
        output_storage_config: Dict mapping OutputType to storage format and path
    """

    # Should be overridden by subclasses
    node_type: str = None

    # Supported output types: what this node type can produce
    # Used during infer_output() to validate the result
    # Subclasses should override this
    supported_output_types: List[OutputType] = []

    # Output storage configuration: how to save and load results
    # Maps OutputType to storage format and path pattern
    # Used when saving/loading node results
    # Subclasses should override this
    output_storage_config: Dict[OutputType, Dict[str, str]] = {}

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
    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer the output type and display type from the execution result.

        At runtime, this method:
        1. Detects the actual output type from the result
        2. Looks up the ResultFormat from output_declarations
        3. Returns a NodeOutput with the appropriate format

        Args:
            result: The actual output from executing this node

        Returns:
            NodeOutput instance describing the output, with result_format from declarations
        """
        pass

    def get_storage_config(self, output_type: OutputType) -> Dict[str, str]:
        """
        Get the storage configuration for a specific output type.

        This includes the save format and result path pattern.

        Args:
            output_type: The type of output

        Returns:
            Dict with 'save_format' and 'result_path_pattern' keys

        Raises:
            ValueError: If this output_type is not in storage config
        """
        if output_type not in self.output_storage_config:
            raise ValueError(
                f"{self.__class__.__name__} has no storage config for output type {output_type.value}. "
                f"Configured types: {list(self.output_storage_config.keys())}"
            )
        return self.output_storage_config[output_type]

    def is_output_type_supported(self, output_type: OutputType) -> bool:
        """
        Check if this node type supports producing the given output type.

        Args:
            output_type: The type of output to check

        Returns:
            True if supported, False otherwise
        """
        return output_type in self.supported_output_types

    def get_metadata_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary for storage"""
        return self.metadata.to_dict()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.node_id}, type={self.node_type})"
