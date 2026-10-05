"""
Author: Revanth Kumar Chilukuru
"""
import sys
import os
import numpy as np
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.lidar_pipeline import LidarReconstructionPipeline
pipeline = LidarReconstructionPipeline()
room, metrics = pipeline.process_scan("data/sample_subset/single_room/c00a170fe1", drift_correction=True)
print(json.dumps([list(np.round(p, 2)) for p in room.polygon_vertices]))
