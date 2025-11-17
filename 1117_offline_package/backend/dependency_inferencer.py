"""
Dependency Inferencer

Infers node dependencies from notebook code by analyzing variable usage.
No need to maintain explicit depends_on lists - they're inferred from code.

Key insight: If a node's code uses a variable that matches another node's ID,
then it depends on that node. Simple string matching is sufficient.
"""

import re
from typing import List, Set, Optional


class DependencyInferencer:
    """Infers dependencies from notebook code"""

    @staticmethod
    def infer_dependencies(
        node_id: str,
        code: str,
        all_node_ids: List[str],
        explicit_dependencies: Optional[List[str]] = None
    ) -> List[str]:
        """
        Infer which nodes this code depends on.

        Args:
            node_id: Current node ID
            code: Node's source code
            all_node_ids: List of all node IDs in project
            explicit_dependencies: Explicit @depends_on from metadata (overrides inference)

        Returns:
            List of node IDs that this node depends on
        """
        # If explicit dependencies are provided, use those (they override inference)
        if explicit_dependencies:
            return explicit_dependencies

        # Otherwise, infer from code
        return DependencyInferencer._infer_from_variable_usage(
            node_id, code, all_node_ids
        )

    @staticmethod
    def _infer_from_variable_usage(
        node_id: str,
        code: str,
        all_node_ids: List[str]
    ) -> List[str]:
        """
        Infer dependencies by checking which node variables are used in code.

        A node depends on another if:
        1. The other node's ID appears in the code
        2. It's not the current node
        3. It's actually used (not just mentioned in comments)

        Args:
            node_id: Current node ID
            code: Source code to analyze
            all_node_ids: All available node IDs

        Returns:
            List of inferred dependencies
        """
        dependencies = []

        # Remove comments to avoid false positives
        code_without_comments = DependencyInferencer._remove_comments(code)

        # Check each other node
        for other_id in all_node_ids:
            if other_id == node_id:
                continue

            # Look for the node ID as a complete word (not substring)
            # Use word boundaries to avoid matching substrings
            pattern = r'\b' + re.escape(other_id) + r'\b'

            if re.search(pattern, code_without_comments):
                dependencies.append(other_id)

        # Sort for consistent ordering
        dependencies.sort()

        return dependencies

    @staticmethod
    def _remove_comments(code: str) -> str:
        """
        Remove Python comments from code to avoid false positives.

        Removes:
        - Single-line comments (# ...)
        - Multi-line strings (triple quotes)
        """
        lines = []

        in_multiline = False
        multiline_marker = None

        for line in code.split('\n'):
            # Check for multi-line string start/end
            if '"""' in line or "'''" in line:
                marker = '"""' if '"""' in line else "'''"

                if not in_multiline:
                    in_multiline = True
                    multiline_marker = marker
                    # Remove the start of multiline
                    line = line.split(marker, 1)[0]
                else:
                    if marker == multiline_marker:
                        in_multiline = False
                        # Remove from the end of multiline
                        line = line.split(marker, 1)[-1]

            if in_multiline:
                continue

            # Remove comments from this line
            if '#' in line:
                # But make sure it's not inside a string
                # Simple heuristic: split on # and take first part
                # (doesn't handle edge cases like # in strings, but good enough)
                comment_pos = line.find('#')

                # Count quotes before the # to see if we're inside a string
                before_hash = line[:comment_pos]
                single_quotes = before_hash.count("'") - before_hash.count("\\'")
                double_quotes = before_hash.count('"') - before_hash.count('\\"')

                if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                    # We're not inside a string, remove the comment
                    line = line[:comment_pos]

            lines.append(line)

        return '\n'.join(lines)

    @staticmethod
    def extract_explicit_dependencies(code: str) -> Optional[List[str]]:
        """
        Extract explicit @depends_on from code metadata.

        Format:
            # @depends_on: [node1, node2]
            or
            # @depends_on: node1, node2

        Returns:
            List of dependencies or None if not specified
        """
        # Look for @depends_on in metadata comments
        pattern = r'@depends_on:\s*\[(.*?)\]|@depends_on:\s*(.*?)(?:\n|$)'

        match = re.search(pattern, code)
        if not match:
            return None

        # Extract the dependencies string
        deps_str = match.group(1) or match.group(2)
        if not deps_str:
            return None

        # Parse the list
        deps = [d.strip().strip("'\"") for d in deps_str.split(',')]
        deps = [d for d in deps if d]  # Remove empty strings

        return deps if deps else None
