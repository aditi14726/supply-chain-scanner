"""
reachability_engine.py

Connects the call graph with dependency + CVE data to answer:
"is this vulnerable package actually called from reachable code?"
"""

from dataclasses import dataclass
from framework.call_graph_builder import CallGraph


@dataclass
class ReachabilityResult:
    package_name: str
    is_reachable: bool
    call_sites: list[str]  # which functions in the graph call this package


def check_package_reachability(
    graph: CallGraph, entry_point: str, package_name: str
) -> ReachabilityResult:
    """
    Checks whether any function belonging to `package_name` is called
    from within the reachable functions starting at `entry_point`.

    Matches on calls like "requests.get" -> package "requests"
    """
    try:
        reachable_functions = graph.get_reachable_functions(entry_point)
    except ValueError:
        # If the entry point isn't found in the codebase
        return ReachabilityResult(
            package_name=package_name,
            is_reachable=False,
            call_sites=[]
        )

    call_sites = []
    for func_name in reachable_functions:
        # Check if the function name matches the package name prefix
        # e.g., 'requests.get' starts with 'requests.'
        if func_name == package_name or func_name.startswith(f"{package_name}."):
            call_sites.append(func_name)

    return ReachabilityResult(
        package_name=package_name,
        is_reachable=len(call_sites) > 0,
        call_sites=call_sites,
    )


if __name__ == "__main__":
    import sys
    from framework.ast_parser import parse_directory

    if len(sys.argv) != 4:
        print("Usage: python reachability_engine.py <directory_path> <entry_point> <package_name>")
        sys.exit(1)

    dir_path, entry_point, package_name = sys.argv[1], sys.argv[2], sys.argv[3]

    # Parse all files in the directory
    functions = parse_directory(dir_path)
    graph = CallGraph(functions)

    result = check_package_reachability(graph, entry_point, package_name)

    print(f"Package: {result.package_name}")
    print(f"Reachable: {result.is_reachable}")
    if result.call_sites:
        print("Called via:")
        for site in result.call_sites:
            print(f"  - {site}")