"""
test_dependency_parser.py

Unit tests for framework/dependency_parser.py using pytest.
Tests formatting variations, comments, empty lines, and missing file errors.
"""

import pytest
import os
from framework.dependency_parser import parse_requirements, Dependency

# Temporary file name for testing
TEMP_REQ_FILE = "temp_test_requirements.txt"


@pytest.fixture
def create_test_req_file():
    """
    Fixture that creates a temporary requirements file for testing
    and deletes it after the test run finishes.
    """
    def _create_file(content: str):
        with open(TEMP_REQ_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return TEMP_REQ_FILE

    yield _create_file

    # Clean up the file after test executes
    if os.path.exists(TEMP_REQ_FILE):
        os.remove(TEMP_REQ_FILE)


def test_parse_valid_requirements(create_test_req_file):
    # Setup test file content with different variations of package declarations
    content = """
    flask==2.0.1
    requests>=2.25.0
    pyyaml
    Cryptography==41.0.0
    """
    file_path = create_test_req_file(content)

    dependencies = parse_requirements(file_path)

    assert len(dependencies) == 4
    # The parser converts package names to lowercase automatically
    assert dependencies[0] == Dependency(name="flask", version="2.0.1")
    assert dependencies[1] == Dependency(name="requests", version="2.25.0")
    assert dependencies[2] == Dependency(name="pyyaml", version="unknown")
    assert dependencies[3] == Dependency(name="cryptography", version="41.0.0")


def test_parse_skips_comments_and_empty_lines(create_test_req_file):
    # Setup content containing comments, blank spaces, and git repository parameters
    content = """
    # This is a core dependency comment
    flask==2.0.1
    
    # Another comment here
    requests==2.25.0
    -e git+https://github.com/django/django.git@stable/4.2.x#egg=Django
    """
    file_path = create_test_req_file(content)

    dependencies = parse_requirements(file_path)

    # It should skip comment lines, empty lines, and lines starting with '-'
    assert len(dependencies) == 2
    assert dependencies[0].name == "flask"
    assert dependencies[1].name == "requests"


def test_parser_file_not_found():
    # Calling the parser on a non-existent file should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        parse_requirements("non_existent_file_path.txt")
