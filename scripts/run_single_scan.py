"""
Author: Revanth Kumar Chilukuru
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from src.lidar_pipeline import LidarReconstructionPipeline

def main():
    pipeline = LidarReconstructionPipeline(voxel_size=0.03, confidence_threshold=2)
    scan_path = "Assignment - YC Startup/single_room/c00a170fe1"
    
    print(f"Running LiDAR Pipeline on: {scan_path}")
    room_plan, metrics = pipeline.process_scan(scan_path, room_id="benchmark_room_1", room_name="Primary Room")
    
    print("\n--- Room Plan Output ---")
    print(f"Room ID: {room_plan.room_id} ({room_plan.room_name})")
    print(f"Ceiling Height: {room_plan.ceiling_height.value:.3f} m [CI: {room_plan.ceiling_height.ci_lower} - {room_plan.ceiling_height.ci_upper}]")
    print(f"Floor Area: {room_plan.floor_area.value:.2f} m² [CI: {room_plan.floor_area.ci_lower} - {room_plan.floor_area.ci_upper}]")
    print(f"Perimeter: {room_plan.perimeter:.2f} m")
    print(f"Walls ({len(room_plan.walls)}):")
    for w in room_plan.walls:
        print(f"  {w.id}: length={w.length.value:.3f} m, start={w.start_point}, end={w.end_point}, openings={len(w.openings)}")
        for op in w.openings:
            print(f"    - {op.type} (id: {op.id}): width={op.width.value:.3f}m, pos={op.position_along_wall:.2f}m")
            
    print("\n--- Pipeline Diagnostics ---")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
