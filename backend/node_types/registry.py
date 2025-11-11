"""
Node Type Registry and Factory

Provides a central registry for all node types with automatic discovery
and instantiation capabilities.

Usage:
    # Automatic registration on import
    from node_types import get_node_type

    # Create a node instance
    node = get_node_type('data_source')(metadata)

    # Register a custom node type
    @register_node_type
    class CustomNode(BaseNode):
        node_type = "custom"
        ...
"""

from typing import Dict, Type, Optional, Callable
from .base import BaseNode


class NodeTypeRegistry:
    """
    Central registry for node types.

    Manages node type registration and provides factory methods for creating nodes.
    """

    _registry: Dict[str, Type[BaseNode]] = {}

    @classmethod
    def register(cls, node_type: str, node_class: Type[BaseNode]) -> None:
        """
        Register a node type.

        Args:
            node_type: The node type identifier (e.g., 'data_source', 'compute')
            node_class: The node class that implements this type
        """
        if node_type in cls._registry:
            raise ValueError(f"Node type '{node_type}' is already registered")
        cls._registry[node_type] = node_class

    @classmethod
    def get(cls, node_type: str) -> Optional[Type[BaseNode]]:
        """
        Get a registered node type class.

        Args:
            node_type: The node type identifier

        Returns:
            The node class, or None if not found
        """
        return cls._registry.get(node_type)

    @classmethod
    def list_types(cls) -> list:
        """
        List all registered node types.

        Returns:
            List of registered node type identifiers
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, node_type: str) -> bool:
        """
        Check if a node type is registered.

        Args:
            node_type: The node type identifier

        Returns:
            True if registered, False otherwise
        """
        return node_type in cls._registry

    @classmethod
    def clear(cls) -> None:
        """Clear all registered types (useful for testing)"""
        cls._registry.clear()


def register_node_type(cls: Type[BaseNode]) -> Type[BaseNode]:
    """
    Decorator to automatically register a node type.

    Usage:
        @register_node_type
        class CustomNode(BaseNode):
            node_type = "custom"
            ...

    Args:
        cls: The node class to register

    Returns:
        The node class (unchanged)
    """
    if not hasattr(cls, 'node_type'):
        raise ValueError(f"Node class {cls.__name__} must define 'node_type' attribute")

    NodeTypeRegistry.register(cls.node_type, cls)
    return cls


def get_node_type(node_type: str) -> Type[BaseNode]:
    """
    Get a node type class by name.

    Args:
        node_type: The node type identifier

    Returns:
        The node class

    Raises:
        ValueError: If the node type is not registered
    """
    cls = NodeTypeRegistry.get(node_type)
    if cls is None:
        available = NodeTypeRegistry.list_types()
        raise ValueError(
            f"Unknown node type '{node_type}'. "
            f"Available types: {available}"
        )
    return cls


# Auto-register built-in node types on import
def _register_builtin_types():
    """Register built-in node types"""
    from .data_source import DataSourceNode
    from .compute import ComputeNode
    from .chart import ChartNode
    from .image import ImageNode

    for node_class in [DataSourceNode, ComputeNode, ChartNode, ImageNode]:
        NodeTypeRegistry.register(node_class.node_type, node_class)


# Execute registration on module import
_register_builtin_types()
