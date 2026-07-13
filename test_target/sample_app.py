"""
sample_app.py

A tiny, deliberately simple Python file used to test our AST parser and
call graph builder. Not part of the scanner itself -- this is the "thing
being scanned" for testing purposes.
"""

import requests


def main():
    data = fetch_data()
    process(data)


def fetch_data():
    response = requests.get("https://example.com")
    return response.text


def process(data):
    print(data)


def unused_function():
    # This function is never called from anywhere -- useful for testing
    # that our reachability logic correctly identifies "dead code."
    requests.get("https://unused-path.com")