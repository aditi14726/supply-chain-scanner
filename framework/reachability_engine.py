"""
reachability_engine.py

Connects the call graph (Week 2) with dependency + CVE data (Week 1) to
answer: "is this vulnerable package actually called from reachable code?"

Honest scope note: NVD data usually doesn't tell us the EXACT vulnerable
function name -- so this checks package-level reachability (is any function
from this package called in the reachable call graph), not function-level.
This is documented as a known simplification, not a hidden gap.
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
    reachable_functions = graph.get_reachable_functions(entry_point)

    call_sites = []
    for func_name in reachable_functions:
        # A call like "requests.get" starts with "requests."
        if func_name.startswith(f"{package_name}."):
            call_sites.append(func_name)

    return ReachabilityResult(
        package_name=package_name,
        is_reachable=len(call_sites) > 0,
        call_sites=call_sites,
    )


if __name__ == "__main__":
    import sys
    from framework.ast_parser import parse_python_file

    if len(sys.argv) != 4:
        print("Usage: python reachability_engine.py <file.py> <entry_point> <package_name>")
        sys.exit(1)

    file_path, entry_point, package_name = sys.argv[1], sys.argv[2], sys.argv[3]

    functions = parse_python_file(file_path)
    graph = CallGraph(functions)

    result = check_package_reachability(graph, entry_point, package_name)

    print(f"Package: {result.package_name}")
    print(f"Reachable: {result.is_reachable}")
    if result.call_sites:
        print("Called via:")
        for site in result.call_sites:
            print(f"  - {site}")