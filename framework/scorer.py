"""
scorer.py

Combines CVE severity (CVSS score) with reachability (from
reachability_engine.py) into a single priority score.

Formula (from the blueprint):
    reachability_multiplier = 1.5 if reachable else 0.5
    priority_score = round(cvss_score * reachability_multiplier * 10)

Why this shape: a reachable medium-severity CVE should outrank an
unreachable critical-severity one, because reachable = actually
exploitable in this codebase. The multiplier makes that concrete.
"""

from dataclasses import dataclass


@dataclass
class Finding:
    package_name: str
    cve_id: str
    cvss_score: float
    is_reachable: bool
    priority_score: int
    recommendation: str


def calculate_priority_score(cvss_score: float, is_reachable: bool) -> int:
    """
    Turns a raw CVSS score + reachability flag into a single priority number.
    Higher = fix this first.
    """
    reachability_multiplier = 1.5 if is_reachable else 0.5
    return round(cvss_score * reachability_multiplier * 10)


def build_finding(
    package_name: str,
    cve_id: str,
    cvss_score: float,
    is_reachable: bool,
) -> Finding:
    """
    Builds a complete Finding object, including a human-readable
    recommendation based on the reachability + severity combination.
    """
    priority_score = calculate_priority_score(cvss_score, is_reachable)

    if is_reachable and cvss_score >= 7.0:
        recommendation = "Fix immediately -- high severity and actively used in your code."
    elif is_reachable:
        recommendation = "Reachable but lower severity -- fix soon, not urgent."
    elif cvss_score >= 7.0:
        recommendation = "High severity but not reachable in current code -- monitor, low urgency for now."
    else:
        recommendation = "Low severity and not reachable -- low priority."

    return Finding(
        package_name=package_name,
        cve_id=cve_id,
        cvss_score=cvss_score,
        is_reachable=is_reachable,
        priority_score=priority_score,
        recommendation=recommendation,
    )


if __name__ == "__main__":
    # Manual test with a few made-up scenarios, to see the ranking logic
    # in action before wiring it to real data.
    test_cases = [
        ("critical-but-unused-package", "CVE-FAKE-001", 9.0, False),
        ("medium-but-actively-used-package", "CVE-FAKE-002", 5.0, True),
        ("low-and-unused-package", "CVE-FAKE-003", 2.0, False),
        ("high-and-actively-used-package", "CVE-FAKE-004", 8.5, True),
    ]

    findings = [build_finding(*case) for case in test_cases]

    # Sort by priority score, highest first -- this is what the dashboard
    # will eventually show at the top.
    findings.sort(key=lambda f: f.priority_score, reverse=True)

    print("Findings ranked by priority (highest first):\n")
    for f in findings:
        print(f"  [{f.priority_score:>3}] {f.cve_id} in {f.package_name}")
        print(f"        CVSS: {f.cvss_score} | Reachable: {f.is_reachable}")
        print(f"        {f.recommendation}\n")