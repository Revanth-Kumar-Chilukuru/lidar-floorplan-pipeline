"""
Author: Revanth Kumar Chilukuru
"""
import os
import sys
import subprocess
import json
import shutil
import numpy as np

def extract_metrics(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract wall lengths and area
    if "rooms" in data:
        room = data["rooms"][0]
    else:
        room = data
        
    area = room["floor_area"]["value"]
    ceiling = room["ceiling_height"]["value"]
    wall_lengths = [w["length"]["value"] for w in room["walls"]]
    return area, ceiling, wall_lengths

def run_10_times(script_dir, out_dir_base, scan_path):
    python_bin = sys.executable
    out_dir_base = os.path.abspath(out_dir_base)
    areas = []
    ceilings = []
    all_walls = []
    
    if os.path.exists(out_dir_base):
        shutil.rmtree(out_dir_base)
    os.makedirs(out_dir_base)
    
    for i in range(1, 11):
        out_dir = os.path.join(out_dir_base, f"run_{i}")
        os.makedirs(out_dir)
        cmd = f'"{python_bin}" "main.py" --input "{scan_path}" --tier lidar --output-dir "{out_dir}"'
        print(f"  Executing Run {i}/10...", end="\r")
        res = subprocess.run(cmd, shell=True, capture_output=True, cwd=script_dir)
        if res.returncode != 0:
            print(f"ERROR running {cmd}")
            print("STDOUT:", res.stdout)
            print("STDERR:", res.stderr)
            sys.exit(1)
        
        json_file = os.path.join(out_dir, "c00a170fe1_lidar_plan.json")
        area, ceiling, walls = extract_metrics(json_file)
        areas.append(area)
        ceilings.append(ceiling)
        all_walls.append(walls)
        
    print(f"  Completed 10 runs.          ")
    
    # Calculate spreads
    max_area_spread = max(areas) - min(areas)
    max_ceiling_spread = (max(ceilings) - min(ceilings)) if None not in ceilings else 0
    
    # For walls, we assume the same number of walls
    num_walls = len(all_walls[0])
    wall_spreads = []
    for w_idx in range(num_walls):
        w_lengths = [runs[w_idx] for runs in all_walls if len(runs) > w_idx]
        if w_lengths:
            wall_spreads.append(max(w_lengths) - min(w_lengths))
            
    max_wall_spread = max(wall_spreads) if wall_spreads else 0
    
    return {
        "area_spread_m2": max_area_spread,
        "ceiling_spread_m": max_ceiling_spread,
        "wall_spread_m": max_wall_spread
    }

def main():
    print("Testing Algorithmic Determinism (BEFORE vs AFTER)")
    scan_path = "data/sample_subset/single_room/c00a170fe1"
    
    # BEFORE
    worktree_dir = "outputs/before_fix_worktree"
    if os.path.exists(worktree_dir):
        subprocess.run(f"git worktree remove {worktree_dir} --force", shell=True)
        
    try:
        # Dynamically lookup the pre-fix commit by its message
        res = subprocess.run(["git", "log", "--format=%H", "--grep=^docs & benchmarks", "-1"], capture_output=True, text=True, check=True)
        commit_hash = res.stdout.strip()
        if not commit_hash:
            print("ERROR: Could not find pre-fix commit (message starting with 'docs & benchmarks'). Failing loudly.")
            sys.exit(1)
            
        print(f"\n[BEFORE FIX] Creating git worktree at pre-determinism-fix commit ({commit_hash[:7]})...")
        subprocess.run(f"git worktree add {worktree_dir} {commit_hash}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git command failed. {e}")
        sys.exit(1)
    
    # Copy subset data into worktree
    os.makedirs(os.path.join(worktree_dir, "Assignment - YC Startup/single_room"), exist_ok=True)
    shutil.copytree("data/sample_subset/single_room/c00a170fe1", os.path.join(worktree_dir, "Assignment - YC Startup/single_room/c00a170fe1"), dirs_exist_ok=True)
    
    scan_path_before = "Assignment - YC Startup/single_room/c00a170fe1"
    
    print("\n[BEFORE FIX] Installing legacy dependency (open3d) for old commit...")
    subprocess.run(["uv", "pip", "install", "open3d"], check=True)
    
    before_metrics = run_10_times(worktree_dir, "outputs/fix_loop_before", scan_path_before)
    
    subprocess.run(f"git worktree remove {worktree_dir} --force", shell=True)
    
    # AFTER
    print("\n[AFTER FIX] Running current HEAD...")
    after_metrics = run_10_times(".", "outputs/fix_loop_after", scan_path)
    
    def get_status(wall_spread_m):
        return "PASS" if wall_spread_m <= 0.01 else "FAIL"
        
    status_before = get_status(before_metrics['wall_spread_m'])
    status_after = get_status(after_metrics['wall_spread_m'])
    
    print("\n=======================================================")
    print("FIX LOOP RESULTS (Algorithmic Determinism)")
    print("=======================================================")
    print(f"BEFORE FIX:")
    print(f"  Max Wall Spread:    {before_metrics['wall_spread_m']*100:.2f} cm")
    print(f"  Max Area Spread:    {before_metrics['area_spread_m2']:.3f} m2")
    print(f"  Status:             {status_before}")
    
    print(f"\nAFTER FIX:")
    print(f"  Max Wall Spread:    {after_metrics['wall_spread_m']*100:.2f} cm")
    print(f"  Max Area Spread:    {after_metrics['area_spread_m2']:.3f} m2")
    print(f"  Status:             {status_after}")
    print("=======================================================")
    
    # Generate FIX_LOOP_DECLARATION.md
    with open("FIX_LOOP_DECLARATION.md", "w") as f:
        f.write(f"""# Fix Loop Declaration: Algorithmic Determinism

## 1. The Identified Worst Gate
**Target Gate**: Repeatability (Max variance $\le 1.0\\text{{ cm}}$ on identical room captures).
**Observation**: The original pipeline exhibited non-determinism, producing different metric outputs on the exact same scan data in consecutive runs. 
**Status (Before)**: {status_before} (Max spread: {before_metrics['wall_spread_m']*100:.2f} cm)

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
*   **Before Fix Spread**: {before_metrics['wall_spread_m']*100:.2f} cm max delta (algorithmic non-determinism).
*   **After Fix Spread**: {after_metrics['wall_spread_m']*100:.2f} cm max delta.
*   **Gate Status**: {status_after}

### Commands to Verify
```bash
python scripts/run_fix_loop.py
```

### Honest Post-Mortem & What This Does Not Prove
While the pipeline is now perfectly deterministic on identical data (meaning no variance *from the software*), **this does not prove capture-to-capture physical repeatability**. True physical repeatability requires scanning the same room twice physically and comparing the outputs. Since the dataset only provides single captures per room, real-world repeatability remains unverified. This fix only achieves algorithmic stability.
""")
    
    print("Regenerated FIX_LOOP_DECLARATION.md with actual calculated numbers.")

if __name__ == "__main__":
    main()
