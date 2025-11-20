"""
DAG Layout Algorithm for Automatic Node Positioning

Implements hierarchical layout algorithm with special handling for tool nodes.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass


@dataclass
class NodeLayoutInfo:
    """Information about a node's position and layout"""
    node_id: str
    layer: int
    position_in_layer: int
    x: float
    y: float
    type: str
    last_execution_time: Optional[str] = None


class DAGLayout:
    """
    Hierarchical DAG layout algorithm with support for:
    1. Tool nodes horizontally arranged at the top
    2. Hierarchical layering for other nodes (left to right)
    3. Special positioning for single-child and single-parent nodes
    4. Left-to-right flow (arrows: left-in, right-out)
    """

    # Layout constants
    TOOL_NODE_Y = -150  # Tool nodes positioned at top
    NODE_SPACING = 150  # Vertical spacing between nodes in same layer
    TOOL_NODE_SPACING = 200  # Horizontal spacing between tool nodes
    LAYER_WIDTH = 300   # Horizontal spacing between layers
    SPECIAL_OFFSET = 60  # Offset for special positioning rules (0.2 * 300 = 60)

    def __init__(self, nodes: List[Dict[str, Any]], edges: List[Tuple[str, str]]):
        """
        Initialize layout algorithm

        Args:
            nodes: List of node dicts with at least: id, type, last_execution_time (optional)
            edges: List of (source, target) tuples representing dependencies
        """
        self.nodes = {node['id']: node for node in nodes}
        self.edges = edges
        self.adjacency_list = self._build_adjacency_list()
        self.reverse_adjacency = self._build_reverse_adjacency_list()

    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """Build adjacency list from edges (parent -> children)"""
        graph = {node_id: [] for node_id in self.nodes}
        for source, target in self.edges:
            if source in graph and target in graph:
                graph[source].append(target)
        return graph

    def _build_reverse_adjacency_list(self) -> Dict[str, List[str]]:
        """Build reverse adjacency list (child -> parents)"""
        graph = {node_id: [] for node_id in self.nodes}
        for source, target in self.edges:
            if source in graph and target in graph:
                graph[target].append(source)
        return graph

    def calculate_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        Calculate positions for all nodes

        Returns:
            Dict mapping node_id to (x, y) coordinates
        """
        positions = {}

        # Step 1: Separate tool nodes from other nodes
        tool_nodes = [n_id for n_id in self.nodes if self.nodes[n_id].get('type') == 'tool']
        non_tool_nodes = [n_id for n_id in self.nodes if self.nodes[n_id].get('type') != 'tool']

        # Step 2: Position tool nodes at the top
        positions.update(self._layout_tool_nodes(tool_nodes))

        # Step 3: Layout non-tool nodes in hierarchical layers
        positions.update(self._layout_hierarchical_nodes(non_tool_nodes))

        return positions

    def _layout_tool_nodes(self, tool_node_ids: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Layout tool nodes in a horizontal line at the top
        Sorted by execution time, with unexecuted nodes last

        Args:
            tool_node_ids: List of tool node IDs

        Returns:
            Dict mapping node_id to (x, y) coordinates
        """
        positions = {}

        # Sort tool nodes by execution time
        sorted_nodes = self._sort_by_execution_time(tool_node_ids)

        # Position them horizontally with fixed spacing
        for i, node_id in enumerate(sorted_nodes):
            x = i * self.TOOL_NODE_SPACING
            y = self.TOOL_NODE_Y
            positions[node_id] = (x, y)

        return positions

    def _layout_hierarchical_nodes(self, non_tool_ids: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Layout non-tool nodes in hierarchical layers

        Algorithm:
        1. Compute layer for each node (0 for nodes with no parents, else max(parent_layer) + 1)
        2. Group nodes by layer
        3. Position nodes within each layer
        4. Apply special positioning rules for single-child/single-parent nodes
        """
        positions = {}

        # Step 1: Calculate layers
        layers = self._calculate_layers(non_tool_ids)

        # Step 2: Group nodes by layer
        nodes_by_layer = {}
        for node_id, layer in layers.items():
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = []
            nodes_by_layer[layer].append(node_id)

        # Step 3: Position nodes within each layer
        for layer, node_ids in sorted(nodes_by_layer.items()):
            # Sort by execution time within layer
            sorted_nodes = self._sort_by_execution_time(node_ids)

            # Calculate positions
            layer_positions = {}
            for i, node_id in enumerate(sorted_nodes):
                x = layer * self.LAYER_WIDTH
                y = i * self.NODE_SPACING
                layer_positions[node_id] = (x, y)

            positions.update(layer_positions)

        # Step 4: Apply special positioning rules
        positions = self._apply_special_positioning(positions, layers)

        return positions

    def _calculate_layers(self, node_ids: List[str]) -> Dict[str, int]:
        """
        Calculate layer for each node using dynamic programming
        Layer 0: nodes with no parents (source nodes)
        Layer N: max(parent_layer) + 1
        """
        layers = {}

        # Topological sort to ensure we process nodes in correct order
        visited = set()
        in_degree = {n_id: len(self.reverse_adjacency.get(n_id, [])) for n_id in node_ids}

        def calculate_layer(node_id: str) -> int:
            """Calculate layer for a node"""
            if node_id in layers:
                return layers[node_id]

            # Get parent nodes
            parents = [p for p in self.reverse_adjacency.get(node_id, []) if p in node_ids]

            if not parents:
                # No parents = layer 0
                layers[node_id] = 0
            else:
                # Layer = max(parent layers) + 1
                parent_layers = [calculate_layer(p) for p in parents]
                layers[node_id] = max(parent_layers) + 1

            return layers[node_id]

        # Calculate layers for all nodes
        for node_id in node_ids:
            if node_id not in layers:
                calculate_layer(node_id)

        return layers

    def _sort_by_execution_time(self, node_ids: List[str]) -> List[str]:
        """
        Sort nodes by first execution time
        Executed nodes first (sorted by first execution time), unexecuted nodes last
        """
        executed = []
        unexecuted = []

        for node_id in node_ids:
            node = self.nodes.get(node_id, {})
            first_exec_time = node.get('first_execution_time')
            if first_exec_time:
                executed.append((first_exec_time, node_id))
            else:
                unexecuted.append(node_id)

        # Sort executed by first execution time, then add unexecuted
        executed.sort(key=lambda x: x[0])
        return [n_id for _, n_id in executed] + unexecuted

    def _apply_special_positioning(
        self,
        positions: Dict[str, Tuple[float, float]],
        layers: Dict[str, int]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Apply special positioning rules for single-child/single-parent nodes:
        1. Layer 0 node with single child: move to child's left-top (父节点在左上)
           - x = child_x - SPECIAL_OFFSET
           - y = child_y - SPECIAL_OFFSET
        2. Non-layer-0 node with single parent and no children: move to parent's right-bottom (子节点在右下)
           - x = parent_x + SPECIAL_OFFSET
           - y = parent_y + SPECIAL_OFFSET
        """
        new_positions = dict(positions)

        # Rule 1: Layer 0 node with single child
        # Position at child's left-top (父节点在左上)
        layer_0_nodes = [n_id for n_id, l in layers.items() if l == 0]
        for node_id in layer_0_nodes:
            # Get direct children of this node
            children = self.adjacency_list.get(node_id, [])
            children = [c for c in children if c in layers]

            if len(children) == 1:
                child_id = children[0]
                child_x, child_y = new_positions[child_id]
                # Position at child's left-top
                new_x = child_x - self.SPECIAL_OFFSET
                new_y = child_y - self.SPECIAL_OFFSET
                new_positions[node_id] = (new_x, new_y)

        # Rule 2: Non-layer-0 node with single parent and no children
        # Position at parent's right-bottom (子节点在右下)
        for node_id, layer in layers.items():
            if layer == 0:
                continue

            # Check if has single parent
            parents = [p for p in self.reverse_adjacency.get(node_id, []) if p in layers]
            if len(parents) != 1:
                continue

            # Check if has no children
            children = [c for c in self.adjacency_list.get(node_id, []) if c in layers]
            if children:
                continue

            # Check if parent has multiple children - if so, DON'T apply special positioning
            parent_id = parents[0]
            parent_children = [c for c in self.adjacency_list.get(parent_id, []) if c in layers]
            if len(parent_children) > 1:
                continue

            # Only apply if parent has single child (this node)
            # Position at parent's right-bottom
            parent_x, parent_y = new_positions[parent_id]
            new_x = parent_x + self.SPECIAL_OFFSET
            new_y = parent_y + self.SPECIAL_OFFSET
            new_positions[node_id] = (new_x, new_y)

        return new_positions


def calculate_node_positions(nodes: List[Dict[str, Any]], edges: List[Tuple[str, str]]) -> Dict[str, Dict[str, float]]:
    """
    Main function to calculate positions for all nodes

    Args:
        nodes: List of node dicts
        edges: List of (source, target) edges

    Returns:
        Dict mapping node_id to position dict with 'x' and 'y' keys
    """
    layout = DAGLayout(nodes, edges)
    positions = layout.calculate_layout()

    # Convert tuple positions to dict format
    result = {}
    for node_id, (x, y) in positions.items():
        result[node_id] = {'x': x, 'y': y}

    return result
