"""
models.py

Defines the SQLAlchemy database schemas for our application:
1. Scan: Tracks historical runs of the scanner.
2. VulnerabilityCache: Stores CVE details locally to prevent NVD rate limiting.
3. Finding: Records the analyzed vulnerability details, reachability, and priority scores.
"""

from datetime import datetime
import json
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    repository_path = Column(String, nullable=False)
    entry_point = Column(String, nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  # "completed", "failed"

    # Relationship: A Scan has many Findings. If the scan is deleted, delete its findings.
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")


class VulnerabilityCache(Base):
    __tablename__ = "vulnerability_cache"

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String, index=True, nullable=False)
    cve_id = Column(String, nullable=False)
    cvss_score = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    package_name = Column(String, nullable=False)
    cve_id = Column(String, nullable=False)
    cvss_score = Column(Float, nullable=True)
    is_reachable = Column(Boolean, default=False)
    priority_score = Column(Integer, nullable=False)
    recommendation = Column(Text, nullable=False)
    
    # Store the list of call site functions (e.g. ['main.fetch_data']) as a JSON-encoded string
    _call_sites = Column("call_sites", Text, default="[]")

    # Relationship: Connects back to the parent Scan
    scan = relationship("Scan", back_populates="findings")

    @property
    def call_sites(self) -> list[str]:
        """Helper getter that decodes the database string back into a Python list."""
        try:
            return json.loads(self._call_sites)
        except Exception:
            return []

    @call_sites.setter
    def call_sites(self, value: list[str]):
        """Helper setter that encodes a Python list into a database string."""
        self._call_sites = json.dumps(value)
