import sys, os, numpy as np, cv2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.lidar_pipeline import LidarReconstructionPipeline
p = LidarReconstructionPipeline()
room, _ = p.process_scan("data/sample_subset/single_room/c00a170fe1", drift_correction=True)
print("Area:", room.floor_area.value)
