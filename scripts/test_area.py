import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.lidar_pipeline import LidarReconstructionPipeline
p = LidarReconstructionPipeline()
r, _ = p.process_scan("data/sample_subset/single_scan_with_ceiling/c7d28f72c6", drift_correction=True)
print("Area:", r.floor_area.value)
