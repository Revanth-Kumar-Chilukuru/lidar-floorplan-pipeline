# Technical Report: End-to-End Property Capture, Reconstruction, and Insurance Damage Assessment Pipeline

**Author:** Antigravity Engineering Candidate  
**Target:** Founding Backend AI Engineer Take-Home  

---

## 1. System Architecture

The pipeline processes consumer smartphone captures into dimensioned 2D architectural floor plans, identifies visible surface damage, applies rule-based concealed insurance damage inferences, and compiles repair scopes of work.

```
                     ┌────────────────────────────────┐
                     │          Input Tiers           │
                     └────────────────────────────────┘
                                      │
                  ┌───────────────────┼───────────────────┐
                  │                   │                   │
         Tier 1: Photos            Tier 2: Video           Tier 3: LiDAR
         (Not Implemented)         (Not Implemented)       (Depth, Poses, IMU)
                                                          │
                                                  Confidence Filter
                                                  & Voxel Downsample
                                                          │
                         ┌────────────────────────────────┐
                         │   Structural Geometry Engine   │
                         │  - Histogram & Median 1D Peak  │
                         │  - PCA Manhattan Footprint     │
                         │  - Torso-Height 2D Slicing     │
                         │  - Sub-cell Contour Extraction │
                         └────────────────────────────────┘
                                          │
                         ┌────────────────────────────────┐
                         │   Damage & Insurance Engine    │
                         │  - (Synthetic / Rule-based)    │
                         │  - Concealed Damage Graph      │
                         │  - Surface-Keyed Scope         │
                         └────────────────────────────────┘
                                          │
                         ┌────────────────────────────────┐
                         │      Deliverable Generators    │
                         │  - Validated Pydantic Schema   │
                         │  - Dimensioned Floor Plan      │
                         └────────────────────────────────┘
```

---

## 2. Tier Design & Device Matrix

| Tier | Input Medium | Sensor Requirements | Implementation Status |
| :--- | :--- | :--- | :--- |
| **Tier 3 (LiDAR)** | Depth + Poses | Apple dToF LiDAR (16-bit) | **Implemented and Validated** |
| **Tier 2 (Video)** | Handheld MP4 clip | Monocular RGB | **Not Implemented** |
| **Tier 1 (Photos)** | 2 to 8 stills / room | Native camera | **Not Implemented** |

*Note: The user did not have access to an iPhone, thus no non-Pro captures were created. Tier 1 and 2 fail loudly with `NotImplementedError` rather than returning fabricated numbers.*

---

## 3. Drift Accountability & Manhattan Alignment

ARKit visual-inertial odometry integrates IMU accelerometer measurements with sparse visual feature tracks. Over time, this causes rotational drift in yaw.

### Manhattan Alignment Ablation (Not True Loop Closure)
In this submission, true pose-graph optimization loop closure is **not implemented**. Instead, a PCA-based Manhattan alignment footprint rotation is applied to correct orthogonal shearing.
1. **Dominant Normal Extraction:** Perform 2D PCA on torso-height slices to determine the room's principal Manhattan orientation angle $\theta_0$.
2. **Orthogonal Plane Snapping:** Rotate the footprint by $-\theta_0$, ensuring walls align with canonical Cartesian axes ($X$ and $Z$). 
3. **Loop Closure Residual:** The raw odometry loop-closure residual is reported for diagnostic purposes, but it is not relaxed across the trajectory graph.

---

## 4. Error Budget & Heuristics

The provided intervals are heuristics and are not derived from a formal sensor noise calibration experiment. True real-world accuracy benchmarking requires ground truth laser measurements which are not present in the dataset.

* **Ceiling Heights:** Estimated using robust 1D histogram-peak extraction and median filtering. If a ceiling cannot be extracted with sufficient support points, it strictly returns `unmeasured` (value `None`, `is_prior=True`).
* **Heuristic Confidence Bounds:**
  - Wall lengths: $\pm 1.5\%$ (heuristic)
  - Area: $\pm 1.5\%$ (heuristic)

---

## 5. The Fix Loop Story (Determinism)

* **Baseline Problem:** The pipeline exhibited algorithmic non-determinism, producing different metric outputs on the exact same scan data in consecutive runs.
* **Root Cause:** Use of `o3d.geometry.PointCloud().voxel_down_sample` and C++ RANSAC (`segment_plane`), which cannot be seeded by NumPy.
* **Shipped Fix:** Eliminated Open3D entirely. Point downsampling was rewritten using a deterministic `np.unique` voxel hashing method. RANSAC was replaced with a deterministic median filter. Footprint extraction was upgraded to sub-cell refinement.
* **Empirical Delta:** Wall spread variance dropped from 11.8 cm to 0.00 cm across 10 identical separate-process runs. Note that this proves algorithmic determinism, not capture-to-capture physical repeatability.

---

## 6. Known Failure Modes & What Was Not Done

1. **No True Pose-Graph Optimization:** The PCA Manhattan rotation only aligns the footprint. It does not correct intra-trajectory drift or true loop closures.
2. **Video & Photo Tiers Omitted:** They have been marked as explicitly `NotImplementedError`. Returning fabricated/hardcoded constants was rejected as it violates the honesty rule constraint.
3. **Synthetic Damage Detection:** The damage regions and classifications are synthetic inputs injected to demonstrate the rule engine and schema mapping, not produced by a live vision model.
4. **Sub-cell Grid Approximation Errors:** OpenCV morphological operators heavily dilate wall bounds. While sub-cell point-projection refinement reduces this error to ~1cm on synthetic shapes, complex concave rooms may still experience discretization artifacts.

## 7. AI Assistance & Engineering Process
The initial version of this submission was AI-generated in a single rushed session, which resulted in fabricated benchmark numbers, hardcoded measurement constants instead of algorithmic outputs, and exaggerated claims about pose-graph loop closure that were not actually implemented. In subsequent separate commits, the pipeline was thoroughly audited and honestly repaired. All hardcoded constants were removed in favor of real algorithms or explicit \
Not
Implemented\ outputs, non-deterministic bugs (like C++ RANSAC and Open3D multithreading) were replaced with robust deterministic Python math, and all claims in this document were rewritten to match exactly what the code actually does.
