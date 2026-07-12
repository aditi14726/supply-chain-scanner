"""
nvd_client.py

Queries the NVD (National Vulnerability Database) API for CVEs matching
a given package name.
"""

import time
import requests
from dataclasses import dataclass

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


@dataclass
class CVEResult:
    cve_id: str
    cvss_score: float | None
    description: str

def search_cves_for_package(package_name: str, max_results: int = 5) -> list[CVEResult]:
    """
    Search NVD for CVEs mentioning this package name.
    """
    params = {
        "keywordSearch": package_name,
        "resultsPerPage": max_results,
    }
    response = requests.get(NVD_BASE_URL, params=params, timeout=15)
    # Be a polite API citizen -- unauthenticated requests are rate limited.
    time.sleep(1.5)

    if response.status_code != 200:
        print(f"  [warn] NVD lookup failed for '{package_name}': HTTP {response.status_code}")
        return []

    data = response.json()
    results = []

    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "UNKNOWN")

        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available",
        )

        cvss_score = None
        metrics = cve.get("metrics", {})
        for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metric_key in metrics and metrics[metric_key]:
                cvss_score = metrics[metric_key][0]["cvssData"].get("baseScore")
                break

        # Basic noise filter -- NVD's keyword search matches the word anywhere,
        # so "flask" also returns unrelated Xen hypervisor CVEs. This is a cheap
        # filter for Week 1; real precision (CPE-based matching) comes in Week 3.
        is_likely_relevant = "python" in description.lower() or "pypi" in description.lower()
        if is_likely_relevant:
            results.append(CVEResult(cve_id=cve_id, cvss_score=cvss_score, description=description))

    return results
if __name__ == "__main__":
    import sys

    package = sys.argv[1] if len(sys.argv) > 1 else "flask"
    print(f"Searching NVD for CVEs mentioning '{package}'...\n")

    cves = search_cves_for_package(package)
    if not cves:
        print("No CVEs found (or lookup failed).")
    for cve in cves:
        score_display = cve.cvss_score if cve.cvss_score is not None else "N/A"
        print(f"  {cve.cve_id}  |  CVSS: {score_display}")
        print(f"    {cve.description[:120]}...\n")