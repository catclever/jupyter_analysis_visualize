"""
Image Node Type

Represents a visualization node that creates static images.
Output: PNG, JPG, or other image file formats
"""

from typing import Any, Dict
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
    """

    node_type = "image"

    def __init__(self, metadata: NodeMetadata):
        """Initialize an image node"""
        if metadata.node_type != self.node_type:
            raise ValueError(f"Expected node_type '{self.node_type}', got '{metadata.node_type}'")
        super().__init__(metadata)

    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """
        Image nodes accept any type of input.

        Args:
            input_data: Dictionary of input values

        Returns:
            Always True (image generation is flexible in what it accepts)
        """
        return True

    def infer_output(self, result: Any) -> NodeOutput:
        """
        Infer output type from the result.

        Args:
            result: The result from executing this node

        Returns:
            NodeOutput describing the image output

        Raises:
            TypeError: If result is not a supported image type
        """
        # Check for PIL Image
        try:
            from PIL import Image as PILImage
            if isinstance(result, PILImage.Image):
                return NodeOutput(
                    output_type=OutputType.IMAGE,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.IMAGE],
                    description="PIL Image object"
                )
        except ImportError:
            pass

        # Check for matplotlib Figure
        try:
            import matplotlib.figure
            if isinstance(result, matplotlib.figure.Figure):
                return NodeOutput(
                    output_type=OutputType.IMAGE,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.IMAGE],
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
                    output_type=OutputType.IMAGE,
                    display_type=DisplayType.IMAGE_VIEWER,
                    result_format=OUTPUT_TO_RESULT_FORMAT[OutputType.IMAGE],
                    description=f"Image file: {result}"
                )

        raise TypeError(
            f"Image node '{self.node_id}' must output either a PIL Image, "
            f"Matplotlib Figure, or image file path (PNG/JPG/GIF/etc.), "
            f"got {type(result).__name__}"
        )
