"""
dependency_parser.py

Parses a requirements.txt file into a clean list of (package_name, version) pairs.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Dependency:
    name: str
    version: str  # "unknown" if no version was pinned


# Matches: package_name==1.2.3 / package_name>=1.2.3 / package_name (no version)
DEP_PATTERN = re.compile(
    r"^([A-Za-z0-9_.\-]+)\s*(==|>=|<=|~=|!=)?\s*([A-Za-z0-9_.\-]*)"
)


def parse_requirements(file_path: str) -> list[Dependency]:
    """
    Read a requirements.txt file and return a list of Dependency objects.
    Skips comments, blank lines, and non-pip-install lines (like -e git+...).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No requirements file found at {file_path}")

    dependencies = []

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or line.startswith("-"):
            continue

        match = DEP_PATTERN.match(line)
        if not match:
            continue

        name = match.group(1).lower()
        version = match.group(3) if match.group(3) else "unknown"

        dependencies.append(Dependency(name=name, version=version))

    return dependencies


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python dependency_parser.py <path_to_requirements.txt>")
        sys.exit(1)

    deps = parse_requirements(sys.argv[1])
    print(f"Found {len(deps)} dependencies:\n")
    for dep in deps:
        print(f"  {dep.name} == {dep.version}")