import os
import sys
import numpy as np
import cv2
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.lidar_pipeline import LidarReconstructionPipeline

def generate_synthetic_room(
    length=7.30, 
    width=8.00, 
    height=2.50, 
    door_width=0.82,
    noise_std=0.01
):
    """Generate a synthetic point cloud for a rectangular room with a door."""
    points = []
    
    # 1. Floor (y = 0)
    # Generate points across the floor area
    num_floor = int(length * width * 1000)
    x_f = np.random.uniform(-length/2, length/2, num_floor)
    z_f = np.random.uniform(-width/2, width/2, num_floor)
    y_f = np.random.normal(0, noise_std, num_floor)
    points.append(np.column_stack((x_f, y_f, z_f)))
    
    # 2. Ceiling (y = height)
    num_ceil = int(length * width * 1000)
    x_c = np.random.uniform(-length/2, length/2, num_ceil)
    z_c = np.random.uniform(-width/2, width/2, num_ceil)
    y_c = np.random.normal(height, noise_std, num_ceil)
    points.append(np.column_stack((x_c, y_c, z_c)))
    
    # 3. Walls
    # Wall 1 (z = -width/2)
    num_w1 = int(length * height * 1000)
    x_w1 = np.random.uniform(-length/2, length/2, num_w1)
    y_w1 = np.random.uniform(0, height, num_w1)
    z_w1 = np.random.normal(-width/2, noise_std, num_w1)
    points.append(np.column_stack((x_w1, y_w1, z_w1)))
    
    # Wall 2 (z = width/2) - Contains door gap
    num_w2 = int(length * height * 1000)
    x_w2 = np.random.uniform(-length/2, length/2, num_w2)
    y_w2 = np.random.uniform(0, height, num_w2)
    z_w2 = np.random.normal(width/2, noise_std, num_w2)
    
    # Remove points to create a door gap
    door_start_x = -door_width / 2.0
    door_end_x = door_width / 2.0
    door_mask = ~((x_w2 > door_start_x) & (x_w2 < door_end_x) & (y_w2 < 2.05))
    points.append(np.column_stack((x_w2[door_mask], y_w2[door_mask], z_w2[door_mask])))
    
    # Wall 3 (x = -length/2)
    num_w3 = int(width * height * 1000)
    z_w3 = np.random.uniform(-width/2, width/2, num_w3)
    y_w3 = np.random.uniform(0, height, num_w3)
    x_w3 = np.random.normal(-length/2, noise_std, num_w3)
    points.append(np.column_stack((x_w3, y_w3, z_w3)))
    
    # Wall 4 (x = length/2)
    num_w4 = int(width * height * 1000)
    z_w4 = np.random.uniform(-width/2, width/2, num_w4)
    y_w4 = np.random.uniform(0, height, num_w4)
    x_w4 = np.random.normal(length/2, noise_std, num_w4)
    points.append(np.column_stack((x_w4, y_w4, z_w4)))
    
    return np.vstack(points)

def test_synthetic_geometry():
    print("==================================================================")
    print("Testing Pipeline Accuracy against Known Synthetic Geometry")
    print("==================================================================")
    
    # Ground Truth values
    gt_length = 7.30
    gt_width = 8.00
    gt_height = 2.50
    gt_area = gt_length * gt_width
    gt_door_width = 0.82
    
    print(f"Ground Truth: {gt_length}x{gt_width}m, Area: {gt_area} m², Ceiling: {gt_height}m, Door: {gt_door_width}m")
    
    # Set up deterministic pipeline
    np.random.seed(42)
    pipeline = LidarReconstructionPipeline()
    
    # Generate points
    pts = generate_synthetic_room(length=gt_length, width=gt_width, height=gt_height, door_width=gt_door_width)
    
    # 1. Plane Extraction
    y_floor, y_ceil, ceiling_height, torso_pts = pipeline.extract_vertical_planes(pts)
    print(f"Extracted Ceiling Height: {ceiling_height} m (Error: {abs(ceiling_height - gt_height):.4f} m)")
    
    # 2. Wall Boundary Extraction (test with standard epsilon)
    room_corners, walls_info, floor_area, perimeter = pipeline.fit_wall_boundary(torso_pts, drift_correction=False)
    
    # Calculate dimensional errors
    area_error = abs(floor_area - gt_area)
    
    # Extract lengths and match to gt_length/gt_width
    lengths = [w['length'] for w in walls_info]
    # We expect two walls around 7.3 and two around 8.0
    lengths.sort()
    
    # Lengths might be rotated based on how findContours builds the box
    if len(lengths) == 4:
        w_err = (abs(lengths[0] - gt_length) + abs(lengths[1] - gt_length)) / 2.0
        l_err = (abs(lengths[2] - gt_width) + abs(lengths[3] - gt_width)) / 2.0
        if w_err > 1.0: # Swap
            w_err = (abs(lengths[0] - gt_width) + abs(lengths[1] - gt_width)) / 2.0
            l_err = (abs(lengths[2] - gt_length) + abs(lengths[3] - gt_length)) / 2.0
            
        print(f"Avg Wall Length Errors: L_err={l_err:.3f}m, W_err={w_err:.3f}m")
    else:
        print(f"Warning: Extracted {len(lengths)} walls instead of 4.")
        
    print(f"Extracted Floor Area: {floor_area:.3f} m² (Error: {area_error:.3f} m²)")
    
    # 3. Openings Detection
    openings = pipeline.detect_openings(walls_info, torso_pts)
    
    if openings:
        op = openings[0]
        door_err = abs(op.width.value - gt_door_width)
        print(f"Extracted Door Width: {op.width.value:.3f} m (Error: {door_err:.3f} m)")
    else:
        print("Failed to detect synthetic door opening.")
        
    print("\nNote: The 5cm (0.05m) voxel grid limits sub-cell accuracy. Wall errors around 2-5cm are expected due to discretization.")
    
    # Write synthetic test results for audit traceability
    results = {
        "ground_truth": {
            "length_m": gt_length,
            "width_m": gt_width,
            "area_m2": gt_area,
            "ceiling_m": gt_height,
            "door_width_m": gt_door_width
        },
        "pipeline_extracted": {
            "ceiling_m": ceiling_height,
            "floor_area_m2": floor_area,
            "num_walls": len(lengths),
            "door_width_m": openings[0].width.value if openings else None
        }
    }
    
    os.makedirs("outputs/synthetic", exist_ok=True)
    with open("outputs/synthetic/synthetic_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    test_synthetic_geometry()
