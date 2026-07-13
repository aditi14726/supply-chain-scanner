"""
call_graph_builder.py

Takes the function info from ast_parser.py and builds an actual graph
structure: nodes = functions, edges = "this function calls that function."

Then provides a reachability check: starting from an entry point (like
main()), which functions can actually be reached by following calls?
"""

from framework.ast_parser import parse_python_file, FunctionInfo


class CallGraph:
    def __init__(self, functions: dict[str, FunctionInfo]):
        self.functions = functions
        # adjacency list: function_name -> list of function names it calls
        self.edges: dict[str, list[str]] = {
            name: info.calls_made for name, info in functions.items()
        }

    def get_reachable_functions(self, entry_point: str) -> set[str]:
        """
        Starting from entry_point, follow every call chain and return
        the set of all function names that are reachable.

        Uses BFS (Breadth-First Search) -- start at entry_point, visit
        everything it calls, then everything those calls, and so on,
        until no new functions are found.
        """
        if entry_point not in self.functions:
            raise ValueError(f"'{entry_point}' is not a known function in this codebase.")

        visited: set[str] = set()
        queue: list[str] = [entry_point]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # look at everything `current` calls
            for called_name in self.edges.get(current, []):
                if called_name not in visited:
                    queue.append(called_name)

        return visited

    def is_reachable(self, entry_point: str, target_function: str) -> bool:
        """
        Convenience check: can `target_function` be reached from `entry_point`?
        """
        reachable = self.get_reachable_functions(entry_point)
        return target_function in reachable


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python call_graph_builder.py <path_to_python_file> <entry_point_function>")
        sys.exit(1)

    file_path = sys.argv[1]
    entry_point = sys.argv[2]

    functions = parse_python_file(file_path)
    graph = CallGraph(functions)

    reachable = graph.get_reachable_functions(entry_point)

    print(f"Starting from '{entry_point}', reachable functions are:\n")
    for name in reachable:
        print(f"  - {name}")

    print(f"\nAll functions in file: {list(functions.keys())}")
    unreachable = set(functions.keys()) - reachable
    if unreachable:
        print(f"\nUnreachable from '{entry_point}': {list(unreachable)}")