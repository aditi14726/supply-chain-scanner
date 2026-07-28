"""
call_graph_builder.py

Takes the function definitions and calls from ast_parser.py and constructs
a global call graph (nodes = functions, edges = calls).

Provides reachability logic using BFS, allowing us to query if any path
exists from a main entry point to a target function or package.
"""

from framework.ast_parser import parse_directory, FunctionInfo


class CallGraph:
    def __init__(self, functions: dict[str, FunctionInfo]):
        self.functions = functions
        # Adjacency list: function_name -> list of function names it calls
        self.edges: dict[str, list[str]] = {
            name: info.calls_made for name, info in functions.items()
        }

    def get_reachable_functions(self, entry_point: str) -> set[str]:
        """
        Starting from an entry_point function, follow every call chain
        and return the set of all reachable function names.
        
        Handles both simple names (e.g., 'main') and fully qualified names
        (e.g., 'sample_app.main') by dynamically resolving the entry point.
        """
        resolved_entry = self._resolve_entry_point(entry_point)
        if not resolved_entry:
            raise ValueError(
                f"'{entry_point}' could not be resolved in the parsed codebase. "
                f"Available functions are: {list(self.functions.keys())}"
            )

        visited: set[str] = set()
        queue: list[str] = [resolved_entry]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # Look at everything `current` calls.
            # If it calls a function outside our codebase (e.g., 'requests.get'),
            # it won't be a node in `self.edges`, so we default to an empty list.
            for called_name in self.edges.get(current, []):
                if called_name not in visited:
                    queue.append(called_name)

        return visited

    def is_reachable(self, entry_point: str, target_function: str) -> bool:
        """
        Checks if target_function is reachable from the entry_point.
        """
        try:
            reachable = self.get_reachable_functions(entry_point)
            return target_function in reachable
        except ValueError:
            return False

    def _resolve_entry_point(self, entry_point: str) -> str | None:
        """
        Resolves a shorthand entry point (like 'main') to its fully qualified
        counterpart (like 'sample_app.main') if it exists in our parsed functions.
        """
        # Case 1: Exact match (e.g., user passed 'sample_app.main')
        if entry_point in self.functions:
            return entry_point

        # Case 2: Shorthand match (e.g., user passed 'main', matches 'sample_app.main')
        candidates = []
        for name in self.functions.keys():
            if name.endswith(f".{entry_point}"):
                candidates.append(name)

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            # Ambiguous: multiple functions with the same name in different modules
            # e.g., 'auth.login' and 'admin.login'. Fallback to first, or require qualification.
            print(f"[warn] Multiple entry point candidates found for '{entry_point}': {candidates}. Choosing {candidates[0]}")
            return candidates[0]

        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python call_graph_builder.py <path_to_directory> <entry_point_function>")
        sys.exit(1)

    dir_path = sys.argv[1]
    entry_point = sys.argv[2]

    # Parse all files in the directory
    functions = parse_directory(dir_path)
    graph = CallGraph(functions)

    try:
        reachable = graph.get_reachable_functions(entry_point)
        print(f"\nStarting from '{entry_point}', reachable functions are:")
        for name in sorted(reachable):
            print(f"  - {name}")
        
        all_funcs = set(functions.keys())
        unreachable = all_funcs - reachable
        if unreachable:
            print("\nUnreachable internal functions (dead code):")
            for name in sorted(unreachable):
                print(f"  - {name}")
    except ValueError as e:
        print(f"Error: {e}")