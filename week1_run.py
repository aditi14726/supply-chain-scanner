"""
week1_run.py

Week 1 deliverable: parse a requirements.txt, look up CVEs for each
dependency via NVD, print a raw findings list.
"""

import sys
from framework.dependency_parser import parse_requirements
from framework.nvd_client import search_cves_for_package


def main(requirements_path: str):
    print(f"Parsing {requirements_path}...\n")
    dependencies = parse_requirements(requirements_path)
    print(f"Found {len(dependencies)} dependencies.\n")
    print("=" * 60)

    for dep in dependencies:
        print(f"\n{dep.name} ({dep.version})")
        cves = search_cves_for_package(dep.name, max_results=3)

        if not cves:
            print("  No CVEs found.")
            continue

        for cve in cves:
            score = cve.cvss_score if cve.cvss_score is not None else "N/A"
            print(f"  - {cve.cve_id}  |  CVSS: {score}")

    print("\n" + "=" * 60)
    print("Week 1 pipeline complete: dependencies parsed, CVEs looked up.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python week1_run.py <path_to_requirements.txt>")
        sys.exit(1)

    main(sys.argv[1])