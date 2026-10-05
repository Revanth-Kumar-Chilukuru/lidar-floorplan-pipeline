"""
Author: Revanth Kumar Chilukuru
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lidar_pipeline import LidarReconstructionPipeline
from src.renderer import FloorPlanRenderer

def main():
    pipeline = LidarReconstructionPipeline(voxel_size=0.03, confidence_threshold=2)
    scan_path = "Assignment - YC Startup/single_scan_with_ceiling/c7d28f72c6"
    
    print(f"Processing scan: {scan_path}")
    room_plan, metrics = pipeline.process_scan(scan_path, room_id="rm_suite", room_name="Main Suite")
    
    renderer = FloorPlanRenderer()
    out_img = "outputs/renders/main_suite_floorplan.png"
    renderer.render_room(room_plan, out_img, title="Main Suite - LiDAR Scan (Dimensioned)")
    print(f"Success! Output rendered to {out_img}")

if __name__ == "__main__":
    main()
