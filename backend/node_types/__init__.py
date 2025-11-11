"""
Node Types System for Jupyter Analysis Visualize

This module provides a standardized node type system with automatic extensibility.
Each node type defines:
- Input specification
- Output type inference
- Display configuration

Architecture:
- base.py: Abstract BaseNode class
- {node_type}.py: Concrete node type implementations
- registry.py: Node type registry and factory
"""

from .registry import NodeTypeRegistry, get_node_type, register_node_type
from .base import BaseNode, NodeMetadata, NodeOutput, OutputType, DisplayType

__all__ = [
    'NodeTypeRegistry',
    'get_node_type',
    'register_node_type',
    'BaseNode',
    'NodeMetadata',
    'NodeOutput',
    'OutputType',
    'DisplayType',
]
