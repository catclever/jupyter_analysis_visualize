
import ast

def original_infer_node_id(code: str):
    """
    Copy of the ORIGINAL _infer_node_id from project_builder.py (before my changes).
    """
    try:
        tree = ast.parse(code)
        last_assign_target = None
        # Iterate through the AST nodes in reverse order to find the last assignment
        for node in reversed(list(ast.walk(tree))):
            if isinstance(node, ast.Assign):
                # Get the last target of the assignment
                if node.targets:
                    target = node.targets[-1]
                    if isinstance(target, ast.Name):
                        last_assign_target = target.id
                        break
                    elif isinstance(target, (ast.Tuple, ast.List)):
                        # If it's a tuple/list assignment, take the last element
                        if target.elts:
                            last_elt = target.elts[-1]
                            if isinstance(last_elt, ast.Name):
                                last_assign_target = last_elt.id
                                break
        return last_assign_target
    except SyntaxError:
        return None

def test_original():
    code_tool = """
def my_tool(x):
    return x + 1
"""
    print(f"Original Behavior for Tool: {original_infer_node_id(code_tool)}")

if __name__ == "__main__":
    test_original()
