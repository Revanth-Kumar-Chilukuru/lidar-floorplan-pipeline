import os
import sys
import numpy as np
from shapely.geometry import Polygon, Point

def check_trajectory_inside(scan_path):
    print(f"Testing trajectory for {scan_path}...")
    # Import the pipeline dynamically
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.lidar_pipeline import LidarReconstructionPipeline
    
    pipeline = LidarReconstructionPipeline()
    room_plan, metrics = pipeline.process_scan(
        scan_path,
        room_id="room_1",
        room_name="Test Room",
        drift_correction=True
    )
    
    traj = metrics.get("traj_positions")
    if traj is None or len(traj) == 0:
        print("FAIL: No trajectory found.")
        return False
        
    poly_pts = room_plan.polygon_vertices
    poly = Polygon(poly_pts)
    
    # We buffer the polygon slightly to account for the camera being right against a wall
    buffered_poly = poly.buffer(0.3)
    
    inside_count = 0
    total = len(traj)
    for pos in traj:
        # Traj points are 3D (x, y, z), we need (x, z)
        p = Point(pos[0], pos[2])
        if buffered_poly.contains(p):
            inside_count += 1
            
    pct_inside = inside_count / total * 100
    print(f"Trajectory inside: {inside_count}/{total} points ({pct_inside:.1f}%)")
    
    if pct_inside < 95.0:
        print("FAIL: Camera trajectory significantly outside footprint!")
        return False
    print("PASS: Trajectory is inside footprint.")
    return True

if __name__ == "__main__":
    scans = [
        "data/sample_subset/single_room/c00a170fe1",
        "data/sample_subset/single_scan_with_ceiling/c7d28f72c6",
        "data/sample_subset/single_scan_floor_only/1a8384c3f6"
    ]
    
    all_passed = True
    for s in scans:
        if not check_trajectory_inside(s):
            all_passed = False
            
    if all_passed:
        print("\nAll scans passed trajectory check!")
        sys.exit(0)
    else:
        print("\nSome scans failed trajectory check.")
        sys.exit(1)
