"""
Image Node Type

Represents a visualization node that creates static images.
Output: PNG, JPG, or other image file formats
"""

from typing import Any
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType, ResultFormat, OUTPUT_TO_RESULT_FORMAT


class ImageNode(BaseNode):
    """
    Image/visualization node that creates static image outputs.

    Constraints:
    - Can have dependencies on any node type
    - Outputs image file paths or image objects
    - Typically a leaf node (not depended on by other nodes)

    Supported formats:
    - PIL.Image objects
    - File paths to image files (PNG, JPG, GIF, etc.)
    - Matplotlib figure objects (converted to image)

    Output Types: IMAGE
    Storage: IMAGE format (PNG, JPG, etc.), saved to visualizations/ directory
    """

    node_type = "image"

    # What output types this node can produce
    supported_output_types = [OutputType.IMAGE]

    # How to store each output type
    output_storage_config = {
        OutputType.IMAGE: {
            'save_format': ResultFormat.IMAGE.value,
            'result_path_pattern': 'visualizations/{node_id}.png',
        }
    }

    def __init__(self, metadata: NodeMetadata):
        """Initialize an image node"""
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
        output_type = OutputType.IMAGE
        storage_config = self.get_storage_config(output_type)

        # Check for PIL Image
        try:
            from PIL import Image as PILImage
            if isinstance(result, PILImage.Image):
                return NodeOutput(
                    output_type=output_type,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=ResultFormat(storage_config['save_format']),
                    description="PIL Image object"
                )
        except ImportError:
            pass

        # Check for matplotlib Figure
        try:
            import matplotlib.figure
            if isinstance(result, matplotlib.figure.Figure):
                return NodeOutput(
                    output_type=output_type,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=ResultFormat(storage_config['save_format']),
                    description="Matplotlib Figure object"
                )
        except ImportError:
            pass

        # Check for file path string (image file)
        if isinstance(result, str):
            # Check if it's an image file path
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
            if any(result.lower().endswith(ext) for ext in image_extensions):
                return NodeOutput(
                    output_type=output_type,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=ResultFormat(storage_config['save_format']),
                    description=f"Image file: {result}"
                )

        raise TypeError(
            f"Image node '{self.node_id}' must output either a PIL Image, "
            f"Matplotlib Figure, or image file path (PNG/JPG/GIF/etc.), "
            f"got {type(result).__name__}"
        )
