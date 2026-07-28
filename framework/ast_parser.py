"""
ast_parser.py

Parses an entire directory of Python files and extracts:
1. Every function definition (using its fully qualified name: e.g., 'main.fetch_data')
2. Every function call made inside each function, resolved via import maps
   (e.g., if 'import requests as req' is used, 'req.get()' resolves to 'requests.get')
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionInfo:
    name: str           # Fully qualified name, e.g., 'main.fetch_data'
    file_path: str      # Path to the source file
    line_number: int    # Definition line number
    calls_made: list[str] = field(default_factory=list)  # Resolved names of functions called


def get_module_name(file_path: Path, root_path: Path) -> str:
    """
    Computes the Python module name for a file relative to the root directory.
    Example:
      Root: C:/project
      File: C:/project/utils/helper.py
      Returns: 'utils.helper'
    """
    try:
        relative = file_path.relative_to(root_path)
    except ValueError:
        relative = file_path
    
    # Remove suffix (.py) and replace directory separators with dots
    module_parts = list(relative.with_suffix("").parts)
    # If the file is __init__.py, its module name is the parent folder name
    if module_parts[-1] == "__init__":
        module_parts.pop()
    
    return ".".join(module_parts)


def parse_directory(dir_path: str) -> dict[str, FunctionInfo]:
    """
    Scans all Python files in dir_path, resolves imports, and extracts
    function definitions and calls mapped by their fully qualified names.
    """
    root_path = Path(dir_path).resolve()
    py_files = list(root_path.rglob("*.py"))

    # Pass 1: Find all files and build a catalog of all local functions defined in the project.
    # We need this catalog so we can tell if a call like 'helper()' refers to a local function
    # or an external builtin/dependency.
    local_functions: set[str] = set()
    file_ast_trees: dict[Path, tuple[str, ast.AST]] = {}

    for file_path in py_files:
        module_name = get_module_name(file_path, root_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            tree = ast.parse(source_code, filename=str(file_path))
            file_ast_trees[file_path] = (module_name, tree)

            # Catalog all function definitions in this module
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Fully qualified name: e.g., 'utils.helper.fetch_data'
                    fq_name = f"{module_name}.{node.name}"
                    local_functions.add(fq_name)
        except Exception as e:
            print(f"[warn] Failed to parse {file_path}: {e}")

    # Pass 2: Extract imports, functions, and resolve calls for each file
    all_functions: dict[str, FunctionInfo] = {}

    for file_path, (module_name, tree) in file_ast_trees.items():
        # Step 2a: Parse imports in this file to construct the import map
        import_map = _extract_imports(tree, module_name)

        # Step 2b: Find every function definition in this file
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fq_func_name = f"{module_name}.{node.name}"
                func_info = FunctionInfo(
                    name=fq_func_name,
                    file_path=str(file_path),
                    line_number=node.lineno
                )

                # Step 2c: Walk inside this function's body to resolve its calls
                for inner_node in ast.walk(node):
                    if isinstance(inner_node, ast.Call):
                        called_name = _resolve_call(
                            inner_node,
                            import_map,
                            local_functions,
                            module_name
                        )
                        if called_name:
                            func_info.calls_made.append(called_name)

                all_functions[fq_func_name] = func_info

    return all_functions


def _extract_imports(tree: ast.AST, module_name: str) -> dict[str, str]:
    """
    Builds a map from local name references to their fully qualified targets.
    Example imports:
      import requests -> {'requests': 'requests'}
      import requests as req -> {'req': 'requests'}
      from utils.helper import fetch -> {'fetch': 'utils.helper.fetch'}
    """
    import_map: dict[str, str] = {}

    for node in ast.walk(tree):
        # Case 1: 'import requests' or 'import requests as req'
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname if alias.asname else alias.name
                import_map[local_name] = alias.name

        # Case 2: 'from requests import get' or 'from utils.helper import fetch as f'
        elif isinstance(node, ast.ImportFrom):
            # node.module is the source module (e.g., 'requests' or 'utils.helper')
            # If it's a relative import (e.g., 'from . import config'), node.module might be None or relative.
            if not node.module:
                continue
            
            # Simple handling of relative imports (e.g., 'from .utils import helper')
            source_module = node.module
            if node.level > 0:
                # level > 0 means relative imports. We simplify relative imports to absolute
                # based on current module name.
                parts = module_name.split(".")
                # pop elements depending on the level (level=1 is sibling, level=2 is parent, etc.)
                slice_len = len(parts) - node.level + 1
                if slice_len > 0:
                    parent_module = ".".join(parts[:slice_len])
                    source_module = f"{parent_module}.{node.module}" if node.module else parent_module

            for alias in node.names:
                local_name = alias.asname if alias.asname else alias.name
                import_map[local_name] = f"{source_module}.{alias.name}"

    return import_map


def _resolve_call(
    call_node: ast.Call,
    import_map: dict[str, str],
    local_functions: set[str],
    current_module: str
) -> str | None:
    """
    Resolves the name of the function being called, checking the import map
    and the set of locally defined functions.
    """
    func = call_node.func

    # Case 1: Simple call like 'fetch_data()' or 'print()'
    if isinstance(func, ast.Name):
        func_id = func.id
        
        # 1a. Check if it's imported
        if func_id in import_map:
            return import_map[func_id]
        
        # 1b. Check if it's a local function defined in this module
        fq_local = f"{current_module}.{func_id}"
        if fq_local in local_functions:
            return fq_local
        
        # 1c. Else it's a builtin or global call
        return func_id

    # Case 2: Attribute call like 'req.get()' or 'utils.helper.fetch()'
    elif isinstance(func, ast.Attribute):
        # We need to extract the base variable/module (e.g., 'req' in 'req.get')
        # and resolve the chain recursively.
        chain = _get_attribute_chain(func)
        if not chain:
            return None
        
        base = chain[0]
        # Check if the base is in the import map
        if base in import_map:
            resolved_base = import_map[base]
            # Replace the base with its fully qualified name
            return ".".join([resolved_base] + chain[1:])
        
        # If the base refers to a module defined locally
        # e.g., if we imported 'utils' and call 'utils.helper.do_something()'
        # 'utils' is in the import_map, but if it was imported as a local module:
        fq_local_base = f"{current_module}.{base}"
        # We rebuild the chain
        return ".".join(chain)

    return None


def _get_attribute_chain(attr_node: ast.Attribute) -> list[str] | None:
    """
    Recursively extracts the parts of a dot-separated call name.
    Example: requests.get -> ['requests', 'get']
             self.utils.fetch -> ['self', 'utils', 'fetch']
    """
    parts = []
    current = attr_node
    while isinstance(current, ast.Attribute):
        parts.insert(0, current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        parts.insert(0, current.id)
        return parts
    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python ast_parser.py <path_to_directory>")
        sys.exit(1)

    result = parse_directory(sys.argv[1])
    print(f"Parsed {len(result)} functions across directory:\n")
    for name, info in result.items():
        print(f"{name} ({info.file_path}:{info.line_number})")
        for call in info.calls_made:
            print(f"  -> calls: {call}")
        print()