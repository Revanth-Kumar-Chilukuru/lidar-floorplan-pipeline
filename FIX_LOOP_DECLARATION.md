# Fix Loop Declaration: Algorithmic Determinism

## 1. The Identified Worst Gate
**Target Gate**: Repeatability (Max variance $\le 1.0\text{ cm}$ on identical room captures).
**Observation**: The original pipeline exhibited non-determinism, producing different metric outputs on the exact same scan data in consecutive runs. 
**Status (Before)**: FAIL (Max spread: 22.50 cm)

## 2. Root Cause Analysis
The variability was isolated to two sources of algorithmic non-determinism:
1. `o3d.geometry.PointCloud().voxel_down_sample` uses threaded, non-deterministic point aggregation.
2. `pcd.segment_plane(ransac_n=3)` uses C++ RANSAC, which cannot be seeded by `numpy.random.seed`.

## 3. The Fix
We eliminated Open3D from the plane extraction pipeline entirely. 
* Point downsampling was rewritten using a deterministic `np.unique` voxel hashing method.
* RANSAC was replaced with a robust, deterministic 1D histogram-peak extraction and median filtering for floor/ceiling heights.
* Wall footprint extraction was upgraded to sub-cell refinement, removing dependency on unstable bounding boxes.

## 4. Verification Results (10 Runs)
*   **Before Fix Spread**: 22.50 cm max delta (algorithmic non-determinism).
*   **After Fix Spread**: 0.00 cm max delta.
*   **Gate Status**: PASS

### Commands to Verify
```bash
python scripts/run_fix_loop.py
```

### Honest Post-Mortem & What This Does Not Prove
While the pipeline is now perfectly deterministic on identical data (meaning no variance *from the software*), **this does not prove capture-to-capture physical repeatability**. True physical repeatability requires scanning the same room twice physically and comparing the outputs. Since the dataset only provides single captures per room, real-world repeatability remains unverified. This fix only achieves algorithmic stability.
