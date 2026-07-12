# Supply-Chain Vulnerability Scanner

A dependency vulnerability scanner that goes beyond a flat CVE list. It checks
whether the vulnerable function is actually reachable from your own code, so
you can tell the difference between a real, exploitable risk and a CVE sitting
unused in a dependency you barely touch.

## Scope note
This project targets Python codebases and static, direct-call-chain
reachability. Dynamic imports, reflection, and monkey-patched calls are
explicitly out of scope -- a deliberate boundary, documented here.

## Project status
🚧 Week 1 of 4 -- in progress.

- [x] Dependency parser (requirements.txt → package list)
- [x] NVD API client (package → CVE lookup)
- [ ] AST parser + call graph builder (Week 2)
- [ ] Reachability engine + priority scoring (Week 3)
- [ ] FastAPI + PostgreSQL backend, dashboard (Week 4)

## Setup
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running it (Week 1)
```bash
python week1_run.py sample_requirements.txt
```