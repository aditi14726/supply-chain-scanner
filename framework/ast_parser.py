"""
ast_parser.py

Parses a Python source file and extracts:
1. Every function definition (name + line number)
2. Every function call made inside each function (who calls whom)

This is Week 2's foundation -- the call graph builder (next file) will use
this output to construct the actual "who calls whom" map.
"""

import ast
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    name: str
    line_number: int
    calls_made: list[str] = field(default_factory=list)  # names of functions this one calls


def parse_python_file(file_path: str) -> dict[str, FunctionInfo]:
    """
    Reads a Python file, parses it into an AST, and returns a dictionary
    mapping function name -> FunctionInfo (including what it calls).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=file_path)

    functions: dict[str, FunctionInfo] = {}

    # Step 1: find every function definition in the file
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = FunctionInfo(name=node.name, line_number=node.lineno)

    # Step 2: for each function, look INSIDE it for calls to other functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            current_function = functions[node.name]
            # Walk only within this function's own body
            for inner_node in ast.walk(node):
                if isinstance(inner_node, ast.Call):
                    called_name = _extract_call_name(inner_node)
                    if called_name:
                        current_function.calls_made.append(called_name)

    return functions


def _extract_call_name(call_node: ast.Call) -> str | None:
    """
    Given a Call node, figures out the name of what's being called.
    Handles two common cases:
        fetch_data()          -> "fetch_data"
        requests.get(...)     -> "requests.get"
    """
    func = call_node.func

    if isinstance(func, ast.Name):
        # Simple call: fetch_data()
        return func.id

    if isinstance(func, ast.Attribute):
        # Attribute call: requests.get(...) or self.something()
        if isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
        return func.attr  # fallback for deeper chains

    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python ast_parser.py <path_to_python_file>")
        sys.exit(1)

    result = parse_python_file(sys.argv[1])

    print(f"Found {len(result)} function definitions:\n")
    for func_name, info in result.items():
        print(f"  {func_name}()  [line {info.line_number}]")
        if info.calls_made:
            for called in info.calls_made:
                print(f"      -> calls {called}")
        else:
            print(f"      -> calls nothing")
        print()