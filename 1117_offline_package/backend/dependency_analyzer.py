"""
Dependency Analyzer

Analyzes and manages node dependencies:
- Extracts dependencies from project metadata
- Performs topological sorting for execution order
- Finds complete dependency chains (transitive dependencies)
- Detects circular dependencies
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque


class DependencyAnalyzer:
    """Analyzes dependencies between nodes"""

    def __init__(self, nodes_metadata: Dict[str, Dict]):
        """
        Initialize analyzer with project metadata

        Args:
            nodes_metadata: Dict of node_id -> node_info
                Expected structure: {
                    "node1": {
                        "node_id": "node1",
                        "depends_on": ["node2"],
                        ...
                    },
                    ...
                }
        """
        self.nodes = nodes_metadata
        self.all_node_ids = list(nodes_metadata.keys())

        # Build dependency graph
        self.graph = self._build_graph()
        self.reverse_graph = self._build_reverse_graph()

        # Check for circular dependencies
        self.has_cycles = self._check_cycles()

    def _build_graph(self) -> Dict[str, List[str]]:
        """
        Build dependency graph: node -> list of nodes it depends on

        Returns:
            {
                "node1": ["node2", "node3"],  # node1 depends on node2, node3
                ...
            }
        """
        graph = {}
        for node_id, node_info in self.nodes.items():
            depends_on = node_info.get("depends_on", [])
            graph[node_id] = depends_on if depends_on else []
        return graph

    def _build_reverse_graph(self) -> Dict[str, List[str]]:
        """
        Build reverse dependency graph: node -> list of nodes that depend on it

        Returns:
            {
                "node1": ["node2"],  # node2 depends on node1
                ...
            }
        """
        reverse = defaultdict(list)
        for node_id, dependencies in self.graph.items():
            for dep in dependencies:
                reverse[dep].append(node_id)

        # Ensure all nodes are in the graph
        for node_id in self.all_node_ids:
            if node_id not in reverse:
                reverse[node_id] = []

        return dict(reverse)

    def _check_cycles(self) -> bool:
        """
        Check if there are circular dependencies using DFS

        Returns:
            True if cycles exist, False otherwise
        """
        visited = set()
        rec_stack = set()

        def has_cycle_dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.all_node_ids:
            if node not in visited:
                if has_cycle_dfs(node):
                    return True

        return False

    def get_dependencies(self, node_id: str) -> Dict[str, any]:
        """
        Get complete dependency information for a node

        Returns:
            {
                "node_id": "node1",
                "direct_dependencies": ["node2"],         # Immediate parents
                "all_dependencies": ["node2", "node3"],   # All transitive
                "execution_order": ["node2", "node3", "node1"],  # Topo sort order
                "dependents": ["node4"]                   # Who depends on this
            }
        """
        if node_id not in self.all_node_ids:
            raise ValueError(f"Node {node_id} not found")

        direct_deps = self.graph.get(node_id, [])
        all_deps = self._get_transitive_dependencies(node_id)
        execution_order = self._get_execution_order(node_id)
        dependents = self.reverse_graph.get(node_id, [])

        return {
            "node_id": node_id,
            "direct_dependencies": direct_deps,
            "all_dependencies": sorted(all_deps),
            "execution_order": execution_order,
            "dependents": sorted(dependents),
            "has_circular_dependency": self.has_cycles
        }

    def _get_transitive_dependencies(self, node_id: str) -> Set[str]:
        """
        Get all transitive dependencies (not just direct parents)

        Args:
            node_id: Node to analyze

        Returns:
            Set of all node IDs this node depends on (directly or transitively)
        """
        visited = set()
        stack = deque(self.graph.get(node_id, []))

        while stack:
            current = stack.popleft()
            if current in visited:
                continue

            visited.add(current)
            for dep in self.graph.get(current, []):
                if dep not in visited:
                    stack.append(dep)

        return visited

    def _get_execution_order(self, node_id: str) -> List[str]:
        """
        Get the order in which nodes should be executed to compute this node

        Uses topological sort to ensure dependencies are executed before dependents.

        Args:
            node_id: Node to analyze

        Returns:
            List of node IDs in execution order (dependencies first, then the node itself)
        """
        # Only consider nodes that are dependencies of the target
        relevant_nodes = self._get_transitive_dependencies(node_id) | {node_id}

        # Build subgraph for relevant nodes
        subgraph = {
            n: [d for d in self.graph[n] if d in relevant_nodes]
            for n in relevant_nodes
        }

        # Topological sort using Kahn's algorithm
        in_degree = {n: 0 for n in relevant_nodes}
        for node in relevant_nodes:
            for neighbor in subgraph[node]:
                in_degree[neighbor] += 1

        queue = deque([n for n in relevant_nodes if in_degree[n] == 0])
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            for neighbor in subgraph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Verify all nodes were processed (no cycles in subgraph)
        if len(topo_order) != len(relevant_nodes):
            raise RuntimeError(f"Circular dependency detected in {relevant_nodes}")

        return topo_order

    def get_execution_plan(
        self,
        node_id: str,
        already_executed: Optional[Set[str]] = None
    ) -> Dict[str, any]:
        """
        Get execution plan for a node, considering already-executed nodes

        This is useful for resuming execution - we don't re-execute nodes that
        are already done.

        Args:
            node_id: Node to execute
            already_executed: Set of node IDs that have already been executed

        Returns:
            {
                "target_node": "node1",
                "execution_order": ["node2", "node1"],     # Full order
                "nodes_to_execute": ["node1"],             # What actually needs to run
                "already_executed": ["node2"]              # What's already done
            }
        """
        if already_executed is None:
            already_executed = set()

        full_order = self._get_execution_order(node_id)
        nodes_to_execute = [n for n in full_order if n not in already_executed]

        return {
            "target_node": node_id,
            "execution_order": full_order,
            "nodes_to_execute": nodes_to_execute,
            "already_executed": sorted(already_executed),
            "will_skip": len(already_executed),
            "will_execute": len(nodes_to_execute)
        }

    def get_all_nodes_info(self) -> Dict[str, Dict]:
        """
        Get dependency info for all nodes

        Returns:
            {
                "node1": {"direct_dependencies": [...], ...},
                ...
            }
        """
        return {
            node_id: self.get_dependencies(node_id)
            for node_id in self.all_node_ids
        }

    def find_chains(self) -> Dict[str, List[List[str]]]:
        """
        Find all dependency chains (paths from sources to leaves)

        Useful for understanding the overall project structure.

        Returns:
            {
                "chains": [
                    ["source_node", "intermediate", "leaf_node"],
                    ...
                ],
                "source_nodes": ["node_without_dependencies"],
                "leaf_nodes": ["node_no_one_depends_on"]
            }
        """
        # Find source nodes (no dependencies)
        source_nodes = [n for n in self.all_node_ids if not self.graph[n]]

        # Find leaf nodes (no one depends on them)
        leaf_nodes = [n for n in self.all_node_ids if not self.reverse_graph[n]]

        # Find all paths from sources to leaves
        chains = []

        def dfs_paths(node: str, path: List[str], visited: Set[str]):
            path.append(node)
            visited.add(node)

            # If this is a leaf, we found a chain
            if not self.reverse_graph[node]:
                chains.append(path.copy())
            else:
                # Continue exploring nodes that depend on this one
                for dependent in self.reverse_graph[node]:
                    if dependent not in visited:
                        dfs_paths(dependent, path, visited)

            path.pop()
            visited.remove(node)

        for source in source_nodes:
            dfs_paths(source, [], set())

        return {
            "chains": chains,
            "source_nodes": sorted(source_nodes),
            "leaf_nodes": sorted(leaf_nodes),
            "total_chains": len(chains)
        }

    def validate(self) -> Dict[str, any]:
        """
        Validate the dependency graph

        Returns:
            {
                "valid": True/False,
                "errors": [...],
                "warnings": [...]
            }
        """
        errors = []
        warnings = []

        # Check for cycles
        if self.has_cycles:
            errors.append("Circular dependency detected")

        # Check for missing nodes (depends_on references non-existent nodes)
        all_referenced = set()
        for node_id, deps in self.graph.items():
            for dep in deps:
                all_referenced.add(dep)

        missing = all_referenced - set(self.all_node_ids)
        if missing:
            errors.append(f"Missing nodes referenced in depends_on: {missing}")

        # Check for isolated nodes (no dependencies, no dependents)
        # This is not an error, just a warning
        for node_id in self.all_node_ids:
            if not self.graph[node_id] and not self.reverse_graph[node_id]:
                warnings.append(f"Isolated node: {node_id}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
