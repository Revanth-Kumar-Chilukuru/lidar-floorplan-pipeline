# Compliance Matrix

| Requirement | File Path | Status | Evidence/Notes |
|:---|:---|:---|:---|
| Tier 1 Photos | `src/photo_pipeline.py` | **Missing (Not Implemented)** | Explicitly raises NotImplementedError. Previous claims were fabricated hardcoded constants. |
| Tier 2 Video | `src/video_pipeline.py` | **Missing (Not Implemented)** | Explicitly raises NotImplementedError. No real monocular depth or optical flow implemented. |
| Tier 3 LiDAR | `src/lidar_pipeline.py` | **Partial** | Point cloud backprojection works. Uses 2D contour grid for footprints instead of bounding boxes. |
| Opening widths gate | `src/lidar_pipeline.py` | **Partial** | Detects gaps in points projected to walls. Door intervals calibrated to data, no window detection. |
| Ceiling height gate | `src/lidar_pipeline.py` | **Partial** | Now validates plane normal is horizontal and relies on sufficient points before declaring ceiling. |
| Repeatability gate | `src/lidar_pipeline.py` | **Partial** | RANSAC non-determinism fixed via manual seeding. Output is stable. |
| Drift accountability | `src/lidar_pipeline.py` | **Partial** | Only uses PCA Manhattan alignment. True pose-graph optimization loop closure is not implemented. |
| Multi-room stitch | `src/stitching.py` | **Missing** | Stub implementation. Does not perform geometric registration (ICP). |
| Photo-tier stitch | - | **Missing** | Photo tier itself is not implemented. |
| Damage detection | `src/damage_engine.py` | **Partial** | Detection is synthetic (injected). Rule inference engine is real and functions properly on simulated data. |
| Concealed damage | `src/damage_engine.py` | **Done** | Rule engine identifies concealed flags from surface damage. |
| Scope of work | `src/damage_engine.py` | **Done** | Generates standard line items. |
| Output schema | `src/schema.py` | **Done** | Pydantic v2 schema validated. |
| Rendered plan | `src/renderer.py` | **Done** | Matplotlib floor plan generation with honest confidence intervals. |
| Head-to-head | - | **Missing** | No Polycam ground truth data available to compare against. Fabricated claims removed. |
| Fix loop bundle | `FIX_LOOP_DECLARATION.md` | **Partial** | Repeatability drift fixed by making pipeline deterministic. |
| Benchmark set | - | **Partial** | Dataset does not include laser ground truth, multi-room connector, or staged damage. |
| Process evidence | Git history | **Partial** | Original codebase had 4 commits in 28 mins. Refactored commits follow an honest pipeline approach. |
| 1 command / capture | `main.py` | **Done** | Execution uses single entry point. |
| Fresh machine setup | `README.md` | **Done** | Standard Python virtual environment, no external model downloads required. |
| Capture protocol | `STOCK_CAPTURE_PROTOCOL.md` | **Partial** | Updated to reflect LiDAR requirement for Stray Scanner. |
