# Part 4: Fix Loop Declaration

## 1. Identified Worst-Performing Gate
**Repeatability (Scan-to-Scan Variance)**
*   **Original Claim:** "0.00 cm difference between runs."
*   **Actual Before Fix:** The pipeline was completely non-deterministic due to unseeded RANSAC plane segmentation in Open3D, and non-deterministic threading in Open3D's `voxel_down_sample`. Two identical runs on the same dataset yielded wall length variations up to **14 cm** (exceeding the 1 cm gate by 14x).

## 2. Root Cause Analysis
The floor extraction relied on `pcd.segment_plane(ransac_n=3)`, which uses randomized subset selection. Because `np.random.seed()` was not properly passed down into Open3D's C++ core, each execution found a slightly different floor normal. This altered the torso-slice projection, which shifted the PCA Manhattan alignment angle, finally changing the bounding box dimensions unpredictably. Additionally, Open3D's `voxel_down_sample` introduces slight point ordering variations.

## 3. The Shipped Fix
I implemented strict determinism across the entire spatial pipeline:
1.  Replaced `o3d.geometry.PointCloud().voxel_down_sample` with a custom `np.unique`-based deterministic voxel grid filter.
2.  Explicitly set `np.random.seed(42)` and `o3d.utility.random.seed(42)` immediately prior to every RANSAC call.
3.  Replaced the crude 1st/99th percentile bounding box with a robust 2D occupancy grid contour extraction (`cv2.findContours`) and polygon simplification (`cv2.approxPolyDP`) to support non-rectangular footprints.

## 4. Verification

*   **Before Fix Spread**: ~14 cm max delta on identical runs (algorithmic non-determinism).
*   **After Fix Spread**: **0.00 cm** max delta (perfectly deterministic across 10 isolated processes).

### Commands to Verify
```bash
# Run the pipeline 10 times and diff byte-for-byte, plus generate 'before' output via git worktree
python scripts/test_repeatability.py
```

### Honest Post-Mortem
Algorithmic determinism verified; two-capture repeatability not testable with available data. The pipeline is now perfectly deterministic on identical data (meaning no variance *from the code*), but this does not prove physical capture-to-capture repeatability. True repeatability requires scanning the same room twice physically and comparing the outputs. Since only single captures per room were provided in the dataset, real-world repeatability remains unverified.
