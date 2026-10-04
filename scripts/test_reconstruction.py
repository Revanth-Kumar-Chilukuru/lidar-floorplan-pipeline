import os
import glob
import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import open3d as o3d

def test_point_cloud_projection(dataset_dir: str, step: int = 15, max_frames: int = 150):
    print(f"\n--- Testing 3D Point Cloud Projection on {dataset_dir} ---")
    
    # Load camera matrix
    cam_matrix = np.loadtxt(os.path.join(dataset_dir, "camera_matrix.csv"), delimiter=",")
    # Depth resolution is 256x192, RGB is 1920x1440 (scale factor 7.5)
    depth_w, depth_h = 256, 192
    rgb_w, rgb_h = 1920, 1440
    scale_x = depth_w / rgb_w
    scale_y = depth_h / rgb_h
    
    # Scale intrinsics for depth image
    fx = cam_matrix[0, 0] * scale_x
    fy = cam_matrix[1, 1] * scale_y
    cx = cam_matrix[0, 2] * scale_x
    cy = cam_matrix[1, 2] * scale_y
    
    print(f"Depth Intrinsics: fx={fx:.2f}, fy={fy:.2f}, cx={cx:.2f}, cy={cy:.2f}")

    # Load odometry
    odom_df = pd.read_csv(os.path.join(dataset_dir, "odometry.csv"))
    odom_df.columns = [c.strip() for c in odom_df.columns]
    
    # Grid of pixel coordinates
    u, v = np.meshgrid(np.arange(depth_w), np.arange(depth_h))
    
    depth_files = sorted(glob.glob(os.path.join(dataset_dir, "depth", "*.png")))
    conf_files = sorted(glob.glob(os.path.join(dataset_dir, "confidence", "*.png")))
    
    all_points = []
    
    indices = range(0, min(len(depth_files), len(odom_df)), step)
    count = 0
    for idx in indices:
        if count >= max_frames:
            break
        
        row = odom_df.iloc[idx]
        depth_file = depth_files[idx]
        conf_file = conf_files[idx] if conf_files else None
        
        # Read depth (in mm)
        depth = cv2.imread(depth_file, cv2.IMREAD_UNCHANGED).astype(np.float32) / 1000.0 # to meters
        
        # Read confidence (0, 1, 2)
        if conf_file:
            conf = cv2.imread(conf_file, cv2.IMREAD_UNCHANGED)
            mask = (depth > 0.1) & (depth < 6.0) & (conf >= 2) # High confidence only
        else:
            mask = (depth > 0.1) & (depth < 6.0)
            
        if np.sum(mask) == 0:
            continue
            
        z = depth[mask]
        x = (u[mask] - cx) * z / fx
        y = (v[mask] - cy) * z / fy
        
        # Camera points in standard CV frame (X right, Y down, Z forward):
        # In Stray Scanner / ARKit: ARKit camera coordinate frame has X right, Y up, -Z forward,
        # OR Stray Scanner exports OpenCV camera convention or ARKit convention.
        # Let's test standard OpenCV convention: (x, y, z)
        pts_cam = np.vstack((x, y, z)).T
        
        # Camera to world transformation from odometry:
        # ARKit pose: position (x, y, z), quaternion (qx, qy, qz, qw)
        quat = [row['qx'], row['qy'], row['qz'], row['qw']]
        rot = R.from_quat(quat).as_matrix()
        pos = np.array([row['x'], row['y'], row['z']])
        
        # In Stray Scanner dataset conventions:
        # T_WC = rot @ pts_cam.T + pos
        pts_world = (rot @ pts_cam.T).T + pos
        all_points.append(pts_world)
        count += 1
        
    all_points = np.vstack(all_points)
    print(f"Total reconstructed points: {len(all_points):,}")
    print(f"Point Cloud Bounding Box:")
    min_b = np.min(all_points, axis=0)
    max_b = np.max(all_points, axis=0)
    print(f"  X bounds: [{min_b[0]:.2f}, {max_b[0]:.2f}] m  (Range = {max_b[0]-min_b[0]:.2f}m)")
    print(f"  Y bounds: [{min_b[1]:.2f}, {max_b[1]:.2f}] m  (Range = {max_b[1]-min_b[1]:.2f}m)")
    print(f"  Z bounds: [{min_b[2]:.2f}, {max_b[2]:.2f}] m  (Range = {max_b[2]-min_b[2]:.2f}m)")
    
    # Save as Open3D point cloud and test plane RANSAC
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_points)
    
    # Downsample
    pcd_down = pcd.voxel_down_sample(voxel_size=0.03)
    print(f"Downsampled points (3cm voxel): {len(pcd_down.points):,}")
    
    # RANSAC plane segmentation (looking for floor or walls)
    plane_model, inliers = pcd_down.segment_plane(distance_threshold=0.03, ransac_n=3, num_iterations=1000)
    [a, b, c, d] = plane_model
    print(f"Dominant Plane equation: {a:.3f}x + {b:.3f}y + {c:.3f}z + {d:.3f} = 0")
    print(f"Dominant Plane Normal: [{a:.3f}, {b:.3f}, {c:.3f}]")
    print(f"Inliers in dominant plane: {len(inliers):,} ({len(inliers)/len(pcd_down.points)*100:.1f}%)")
    
    return pcd_down

if __name__ == "__main__":
    scan_path = "Assignment - YC Startup/single_room/c00a170fe1"
    test_point_cloud_projection(scan_path)
