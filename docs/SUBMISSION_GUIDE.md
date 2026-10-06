# Submission Guide: Property Capture Pipeline

**Project**: An end-to-end pipeline that processes consumer smartphone LiDAR captures into dimensioned 2D architectural floor plans and automated repair scopes of work.
**Repository**: `<span style="white-space: nowrap;">https://github.com/Revanth-Kumar-Chilukuru/lidar-floorplan-pipeline</span>`

## Quick Start (3 Commands)
```bash
# 1. Clone and enter repo
git clone https://github.com/Revanth-Kumar-Chilukuru/lidar-floorplan-pipeline && cd lidar-floorplan-pipeline

# 2. Setup environment (Python 3.11 required)
uv venv --python 3.11 && uv pip install -r requirements.txt

# 3. Reproduce all verified claims
uv run python scripts/reproduce_all.py
```

## Device & Tier Matrix

| Tier | Required Hardware | Status | What it Delivers |
|---|---|---|---|
| **Tier 3 (LiDAR)** | iPhone 12+ Pro, iPad Pro 2020+ | **Active** | 2D dimensioned floor plans, orthogonal wall footprint, metric scale, room boundaries. |
| **Tier 2 (Video)** | iPhone 15 or newer (per the case study) | **Not Implemented** | Explicitly fails cleanly. Requires GPU/SLAM. |
| **Tier 1 (Photos)** | Any modern smartphone | **Not Implemented** | Explicitly fails cleanly. Requires LayoutNet models. |

**Hardware Constraint Note**: The author does not own an iPhone. All captures and code tests were run using the provided sample `Stray Scanner` dataset. As Stray Scanner requires an active LiDAR sensor, processing data from non-Pro phones or video/photo fallbacks is not currently possible on this CPU-bound pipeline without fabricating results.

## Verification Status

**Verified:**
- ✅ **Algorithmic Determinism**: Deterministic math replaces RANSAC/Open3D, ensuring 0 variance on the same data.
- ✅ **Honest Null-Safety**: Missing ceilings or out-of-bounds constraints are strictly reported as "unmeasured" (null) rather than defaulted to arbitrary integers. 
- ✅ **Trajectory Bounding**: Extracted footprint fully encompasses the camera tracking path for all sample scans.

**Not Verified:**
- ❌ **Physical Repeatability**: We cannot prove scan-to-scan physical reproducibility without multiple physical captures of the same room. 
- ❌ **Head-to-Head Accuracy**: No `Polycam` exports were available in the dataset for a true comparison.
- ❌ **Opening Detection Accuracy**: "±2 cm on ≥85% gate" for opening detection remains unverified, as no laser/tape ground truth exists in the dataset.

## Known Failure Modes
1. **Pose-Graph Drift**: True SLAM loop closure is not implemented. A PCA footprint alignment heuristic partially corrects orthogonal orientation, but cumulative odometry drift remains in large loops.
2. **Disconnected Wall Convex Hull**: To bound the trajectory, we rely on a Convex Hull which may overestimate concave or L-shaped rooms if large gaps exist in the walls. *Note: The `single_room` area varied between the full capture and the subset (33.4 m² vs 27.3 m²) because the full capture contains more frames looking further out the open doorway, inflating the outermost convex hull repair boundary.*

## Deliverables Index
- `README.md`: Entry point and reproduction steps.
- `TECHNICAL_REPORT.pdf`: Honest architectural analysis and algorithm decisions.
- `COMPLIANCE_MATRIX.md`: Mapping of prompt requirements to code realities.
- `FIX_LOOP_DECLARATION.md`: Before/after metrics for the determinism fix.

- `STOCK_CAPTURE_PROTOCOL.md`: Operator instructions for LiDAR capturing.

- `results/`: Output artifacts (JSON payloads, renders).
