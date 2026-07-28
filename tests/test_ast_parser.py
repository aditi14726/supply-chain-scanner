"""
test_ast_parser.py

Integration/Unit tests for framework/ast_parser.py and framework/call_graph_builder.py.
Validates multi-file parsing, call resolution, and BFS graph reachability using test_target/sample_app.py.
"""

import os
from framework.ast_parser import parse_directory
from framework.call_graph_builder import CallGraph
from framework.reachability_engine import check_package_reachability

# Absolute path to the test_target directory containing sample_app.py
TEST_TARGET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_target"
)


def test_directory_parsing():
    # Parse the sample target application directory
    functions = parse_directory(TEST_TARGET_DIR)

    # Check that all functions in sample_app.py are detected under their module names
    assert "sample_app.main" in functions
    assert "sample_app.fetch_data" in functions
    assert "sample_app.process" in functions
    assert "sample_app.unused_function" in functions

    # Validate function metadata
    main_info = functions["sample_app.main"]
    assert main_info.name == "sample_app.main"
    assert main_info.line_number > 0
    assert "sample_app.fetch_data" in main_info.calls_made
    assert "sample_app.process" in main_info.calls_made


def test_import_resolution_in_calls():
    functions = parse_directory(TEST_TARGET_DIR)

    # In sample_app.py, fetch_data calls 'requests.get("...")'
    # Our AST parser should resolve it to "requests.get" using the import resolver
    fetch_data_info = functions["sample_app.fetch_data"]
    assert "requests.get" in fetch_data_info.calls_made


def test_call_graph_and_reachability():
    # 1. Parse directory and build global graph
    functions = parse_directory(TEST_TARGET_DIR)
    graph = CallGraph(functions)

    # 2. Check general reachability starting from main
    reachable = graph.get_reachable_functions("main")

    # 'main', 'fetch_data', and 'process' are called in the execution flow.
    # Therefore, they must be reachable.
    assert "sample_app.main" in reachable
    assert "sample_app.fetch_data" in reachable
    assert "sample_app.process" in reachable

    # 'unused_function' is dead code; it should NOT be in the reachable set.
    assert "sample_app.unused_function" not in reachable

    # 3. Check reachability mapping for the 'requests' package
    result_active = check_package_reachability(graph, "main", "requests")
    assert result_active.is_reachable is True
    # Verify it maps the correct call sites that trigger this package
    assert "requests.get" in result_active.call_sites

    # 4. Check reachability for an unused package (e.g. 'pyyaml')
    result_unused = check_package_reachability(graph, "main", "pyyaml")
    assert result_unused.is_reachable is False
    assert len(result_unused.call_sites) == 0
