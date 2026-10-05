"""
Author: Revanth Kumar Chilukuru
"""
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.lidar_pipeline import LidarReconstructionPipeline

pipeline = LidarReconstructionPipeline()
room, metrics = pipeline.process_scan("data/sample_subset/single_room/c00a170fe1", drift_correction=True)
traj = np.array(metrics["traj_positions"])
poly = np.array(room.polygon_vertices)

print("Traj min/max XZ:", np.min(traj[:, [0,2]], axis=0), np.max(traj[:, [0,2]], axis=0))
print("Poly min/max:", np.min(poly, axis=0), np.max(poly, axis=0))
