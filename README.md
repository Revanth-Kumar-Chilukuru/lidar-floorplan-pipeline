# Property Capture & Reconstruction Pipeline

An end-to-end pipeline that processes consumer smartphone LiDAR captures into dimensioned 2D architectural floor plans, identifies visible surface damage, applies rule-based concealed insurance damage inferences, and compiles repair scopes of work.

## 🚀 Quickstart

### Prerequisites
* Python 3.11
* [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`
* Windows, Linux, or macOS

### 1. Environment Setup
```bash
git clone <this-repo>
cd AI_Assignment_YC

# Create environment and install dependencies via uv
uv venv --python 3.11
uv pip install -r requirements.txt
```

### 2. Reproduction Bundle
Execute all project deliverables in one command. This will process the tracked data subset and output JSON plans, PNG renders, and benchmarks to the `results/` folder:
```bash
python scripts/reproduce_all.py
```

### 3. Real Fix Loop (Algorithmic Determinism)
Validate the fix for the algorithmic non-determinism issue (Before/After comparison across 10 runs using git worktrees):
```bash
python scripts/run_fix_loop.py
```

---

## What is Implemented
- **Tier 3 (LiDAR):** Processes ARKit depth maps and odometry into dimensioned floor plans.
- **Deterministic Geometry Extraction:** Uses median/histogram peaks and deterministic voxel grid hashing (Open3D dependency removed).
- **Sub-cell Wall Refinement:** Contour projection maps wall segments back to the raw point median for centimeter-accurate synthetic bounds.
- **Null-safe Properties:** Ceilings strictly output as unmeasured (`None`) when insufficient data is available.

## What is NOT Implemented (Honesty Statement)
- **Tier 1 (Photos) and Tier 2 (Video):** Not implemented. They explicitly fail with `NotImplementedError` rather than returning fabricated bounds.
- **True Loop Closure:** Drift is "corrected" only via a post-hoc PCA Manhattan orientation rotation on the 2D footprint, not via pose-graph adjustment.
- **Live Damage Vision Model:** Damage events are synthetic seeds injected to demonstrate the downstream insurance rule engine.
- **iOS Capture App:** The author does not own an iPhone. All tests are run on the provided Stray Scanner sample data.

## Documentation
* `TECHNICAL_REPORT.md` - Honest architectural analysis and algorithms.
* `FIX_LOOP_DECLARATION.md` - Before/after metrics for the determinism fix.
* `COMPLIANCE_MATRIX.md` - Status tracking against the prompt constraints.
* `STOCK_CAPTURE_PROTOCOL.md` - Operator instructions for Stray Scanner LiDAR capturing.
