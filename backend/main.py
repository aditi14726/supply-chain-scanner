"""
main.py

The main FastAPI application. Orchestrates the scanning process:
1. Parses requirements.txt.
2. Traverses and parses the target directory AST and builds a call graph.
3. Performs reachability checks for dependencies.
4. Looks up CVE data from cache or NVD API.
5. Scores findings and saves results.
6. Serves REST endpoints to the frontend dashboard.
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

# Import database configuration
from backend.database import engine, Base, get_db
import backend.models as models

# Import scanning engine components
from framework.dependency_parser import parse_requirements
from framework.nvd_client import search_cves_for_package, CVEResult
from framework.ast_parser import parse_directory
from framework.call_graph_builder import CallGraph
from framework.reachability_engine import check_package_reachability
from framework.scorer import calculate_priority_score, build_finding

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Supply Chain Reachability Scanner API")

# Enable CORS so the frontend dashboard (running on another port or locally) can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic schemas for API inputs
class ScanRequest(BaseModel):
    repository_path: str
    requirements_path: str
    entry_point: str


@app.post("/api/scan")
def run_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Triggers a new reachability scan on a local project directory.
    """
    repo_path = Path(request.repository_path).resolve()
    req_path = Path(request.requirements_path).resolve()

    # Validation: Ensure paths exist on system
    if not repo_path.exists() or not repo_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Repository path does not exist or is not a directory: {request.repository_path}"
        )
    if not req_path.exists() or not req_path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Requirements file does not exist or is not a file: {request.requirements_path}"
        )

    # 1. Initialize Scan record in the DB
    scan_record = models.Scan(
        repository_path=str(repo_path),
        entry_point=request.entry_point,
        status="completed"  # We perform the scan synchronously for now since it runs locally
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    try:
        # Clear placeholder cache entries ("NONE") to trigger fresh evaluations
        db.query(models.VulnerabilityCache).filter(models.VulnerabilityCache.cve_id == "NONE").delete()
        db.commit()

        # 2. Parse dependencies from requirements.txt
        dependencies = parse_requirements(str(req_path))

        # 3. Parse target directory and construct global call graph
        parsed_functions = parse_directory(str(repo_path))
        graph = CallGraph(parsed_functions)

        # 4. Analyze each dependency
        for dep in dependencies:
            package_name = dep.name

            # Check local DB cache first to avoid hitting NVD rate limit
            cached_cves = db.query(models.VulnerabilityCache).filter(
                models.VulnerabilityCache.package_name == package_name
            ).all()

            cves_to_process = []

            if cached_cves:
                # If cached, load them. Check if the cache contains the placeholder "NONE"
                for cached in cached_cves:
                    if cached.cve_id != "NONE":
                        cves_to_process.append(
                            CVEResult(
                                cve_id=cached.cve_id,
                                cvss_score=cached.cvss_score,
                                description=cached.description
                            )
                        )
            else:
                # Not in cache, query NVD API
                print(f"[info] Cache miss. Querying NVD for package: {package_name}")
                api_results = search_cves_for_package(package_name, max_results=5)

                if not api_results:
                    # Save a placeholder record in cache so we know we've scanned this package
                    # and found 0 vulnerabilities. This prevents future API calls for clean packages.
                    none_placeholder = models.VulnerabilityCache(
                        package_name=package_name,
                        cve_id="NONE",
                        cvss_score=None,
                        description="No vulnerabilities found"
                    )
                    db.add(none_placeholder)
                else:
                    # Save API results to cache
                    for result in api_results:
                        cache_entry = models.VulnerabilityCache(
                            package_name=package_name,
                            cve_id=result.cve_id,
                            cvss_score=result.cvss_score,
                            description=result.description
                        )
                        db.add(cache_entry)
                        cves_to_process.append(result)
                
                db.commit()

            # If the package has vulnerabilities, check its reachability
            if cves_to_process:
                reach_result = check_package_reachability(graph, request.entry_point, package_name)

                # 5. Build and store findings
                for cve in cves_to_process:
                    finding_data = build_finding(
                        package_name=package_name,
                        cve_id=cve.cve_id,
                        cvss_score=cve.cvss_score if cve.cvss_score is not None else 0.0,
                        is_reachable=reach_result.is_reachable
                    )

                    db_finding = models.Finding(
                        scan_id=scan_record.id,
                        package_name=package_name,
                        cve_id=cve.cve_id,
                        cvss_score=cve.cvss_score,
                        is_reachable=reach_result.is_reachable,
                        priority_score=finding_data.priority_score,
                        recommendation=finding_data.recommendation,
                        call_sites=reach_result.call_sites  # List gets converted to JSON string via setter
                    )
                    db.add(db_finding)
        
        db.commit()

    except Exception as e:
        scan_record.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Scan execution failed: {str(e)}"
        )

    # Return scan summary
    return {
        "scan_id": scan_record.id,
        "repository_path": scan_record.repository_path,
        "entry_point": scan_record.entry_point,
        "scanned_at": scan_record.scanned_at,
        "status": scan_record.status,
        "findings_count": db.query(models.Finding).filter(models.Finding.scan_id == scan_record.id).count()
    }


@app.get("/api/scans")
def get_scans(db: Session = Depends(get_db)):
    """
    Returns history of all scans run.
    """
    scans = db.query(models.Scan).order_by(models.Scan.scanned_at.desc()).all()
    results = []
    for s in scans:
        findings_count = db.query(models.Finding).filter(models.Finding.scan_id == s.id).count()
        results.append({
            "id": s.id,
            "repository_path": s.repository_path,
            "entry_point": s.entry_point,
            "scanned_at": s.scanned_at,
            "status": s.status,
            "findings_count": findings_count
        })
    return results


@app.get("/api/scans/{scan_id}")
def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed findings for a single scan.
    """
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings = db.query(models.Finding).filter(models.Finding.scan_id == scan_id).order_by(
        models.Finding.priority_score.desc()
    ).all()

    formatted_findings = []
    for f in findings:
        # Dynamically fetch the description from our local database cache
        cache_entry = db.query(models.VulnerabilityCache).filter(
            models.VulnerabilityCache.package_name == f.package_name,
            models.VulnerabilityCache.cve_id == f.cve_id
        ).first()
        description = cache_entry.description if cache_entry else "No vulnerability description available."

        formatted_findings.append({
            "id": f.id,
            "package_name": f.package_name,
            "cve_id": f.cve_id,
            "cvss_score": f.cvss_score,
            "is_reachable": f.is_reachable,
            "priority_score": f.priority_score,
            "recommendation": f.recommendation,
            "call_sites": f.call_sites,
            "description": description
        })

    return {
        "id": scan.id,
        "repository_path": scan.repository_path,
        "entry_point": scan.entry_point,
        "scanned_at": scan.scanned_at,
        "status": scan.status,
        "findings": formatted_findings
    }


@app.delete("/api/scans/{scan_id}")
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    """
    Deletes a historical scan from the database.
    """
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    db.delete(scan)
    db.commit()
    return {"detail": "Scan deleted successfully"}
