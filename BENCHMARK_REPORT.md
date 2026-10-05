# Benchmark & Accuracy Report

## 1. Ground Truth Validation
> **Note:** The dataset does not contain tape or laser measurements. Previous claims of a 7.30m x 8.00m x 2.50m ground truth were fabricated and have been removed. Accuracy is instead assessed based on internal consistency and architectural plausibility.

## 2. Gate Verification

| Gate | Status | Evidence |
|:---|:---|:---|
| **Opening Widths (<= 2cm on 85%)** | **Unverified** | Pipeline detects doorways using density gaps (0.7m-1.2m widths), but without ground truth, precision cannot be proven. |
| **Ceiling Height (<= 1.5cm)** | **Partial** | Fixed extraction logic requires near-horizontal support. Scan `c7d28f72c6` extracts a plausible 2.47m ceiling. Scans without ceilings now correctly fallback to unmeasured 2.75m priors rather than hallucinating 1.77m heights. |
| **Repeatability (<= 1cm or 0.5%)** | **Partial (Deterministic)** | Fixed RANSAC non-determinism. Running the exact same scan twice now yields **0.00 cm** delta (perfectly deterministic). However, true physical capture-to-capture repeatability cannot be tested without dual captures. |
| **Head-to-Head vs Incumbent** | **Unverified** | Polycam data was not provided in the dataset. Fabricated comparison tables have been removed. |

## 3. Drift Accountability Ablation
The pipeline uses a PCA-based Manhattan alignment on the XY torso projection to orient the footprint rectilinearly. 

*   **Before Fix (Raw Poses)**: Rotated unaligned footprint.
*   **After Fix (PCA Aligned)**: The footprint is rotated so its principal axes align with the standard Cartesian coordinate system, enforcing Manhattan world priors.
*   **Disclaimer**: This is a rotation heuristic, not a true pose-graph optimization loop closure. The residual drift (e.g., 0.38m in `c7d28f72c6`) remains uncorrected in the underlying point cloud.

## 4. Input Tier Robustness

| Tier | Capable? | Accuracy | Notes |
|:---|:---|:---|:---|
| **Tier 3 (LiDAR)** | Yes | Moderate | Produces scale-accurate 2D footprints. Polygon extraction now handles basic non-rectangular shapes instead of forcing bounding boxes. |
| **Tier 2 (Video)** | No | N/A | **Not Implemented.** Requires Metric3D/SLAM pipeline. Fake constants removed. |
| **Tier 1 (Photos)** | No | N/A | **Not Implemented.** Requires LayoutNet/RoomNet. Fake constants removed. |
