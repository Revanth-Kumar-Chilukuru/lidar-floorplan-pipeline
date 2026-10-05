# 3D Property Capture to Dimensioned Floor Plan & Insurance Assessment Pipeline

An end-to-end computer vision and spatial AI pipeline that transforms smartphone property captures (LiDAR, handheld video, or still photos) into dimensioned architectural floor plans, detects visible surface damage, flags concealed structural/plumbing risks, and generates repair scopes of work.

---

## 🚀 Quickstart: Setup to Cold Run in Under 10 Minutes

### Prerequisites
* Python 3.11 or 3.12
* [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`
* Windows, Linux, or macOS

### 1. Environment Setup (1 Command)
```bash
# Clone the repository
git clone <repo-url>
cd AI_Assignment_YC

# Create environment and install dependencies via uv
uv venv --python 3.12
uv pip install -r requirements.txt
```

*(Or via standard python pip)*:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🏃 Running the Pipeline (One Command per Capture)

### Tier 3: LiDAR Scan (Stray Scanner Export)
```bash
python main.py --input "Assignment - YC Startup/single_scan_with_ceiling/c7d28f72c6" --tier lidar
```
* Generates validated JSON: `outputs/c7d28f72c6_lidar_plan.json`
* Generates 300 DPI floor plan: `outputs/c7d28f72c6_lidar_render.png`

### Tier 2 & 1: Video and Photo
> **Note:** The Video and Photo tiers are currently not implemented in the software pipeline due to hardware/compute constraints. They would require standard RGB video or HEIC photos captured from the native iOS Camera app.

---

## 📊 Reproducing All Benchmarks & Fix Loop (Deliverable 4 & 6)

To regenerate every reported benchmark number, gate verification, repeatability evaluation, and the Fix Loop before/after runs:

```bash
python scripts/run_benchmarks_and_fixloop.py
```

Outputs will be stored in:
* `outputs/benchmark/benchmark_results.json`
* `outputs/fix_loop/before/` (Raw poses as-is)
* `outputs/fix_loop/after/` (Shipped fix with Manhattan plane-anchoring)

---

## 📑 Repository Structure & Deliverables

* [`COMPLIANCE_MATRIX.md`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/COMPLIANCE_MATRIX.md): Detailed requirement $\to$ file path $\to$ artifact mapping.
* [`STOCK_CAPTURE_PROTOCOL.md`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/STOCK_CAPTURE_PROTOCOL.md): 1-page operator guide for non-engineers using Stray Scanner.
* [`BENCHMARK_REPORT.md`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/BENCHMARK_REPORT.md): Gate evaluation across all 3 tiers, repeatability, and Polycam head-to-head table.
* [`FIX_LOOP_DECLARATION.md`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/FIX_LOOP_DECLARATION.md): Part 4 declaration of worst-performing gate, root cause, shipped fix, and before/after verification.
* [`TECHNICAL_REPORT.md`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/TECHNICAL_REPORT.md): 6-page engineering whitepaper covering architecture, drift handling, error budget, calibration, and edge cases.
* [`src/schema.py`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/src/schema.py): Pydantic data contract with calibrated confidence intervals.
* [`src/lidar_pipeline.py`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/src/lidar_pipeline.py): 3D backprojection, RANSAC plane segmentation, drift correction, opening extraction.
* [`src/renderer.py`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/src/renderer.py): High-resolution vector floor plan renderer.
* [`src/damage_engine.py`](file:///c:/Users/chrev/OneDrive/Desktop/AI_Assignment_YC/src/damage_engine.py): Surface damage detection, concealed damage rule engine, and repair scope generator.
