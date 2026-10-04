import os
import glob
import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import open3d as o3d

def inspect_dataset(dataset_dir: str):
    print(f"\n=======================================================")
    print(f"Inspecting Dataset: {dataset_dir}")
    print(f"=======================================================")
    
    # 1. Camera Matrix
    cam_matrix_path = os.path.join(dataset_dir, "camera_matrix.csv")
    if os.path.exists(cam_matrix_path):
        K = np.loadtxt(cam_matrix_path, delimiter=",")
        print(f"Camera Intrinsics Matrix K:\n{K}")
    else:
        print("Camera matrix not found!")
        K = None

    # 2. Odometry
    odom_path = os.path.join(dataset_dir, "odometry.csv")
    if os.path.exists(odom_path):
        odom_df = pd.read_csv(odom_path)
        odom_df.columns = [c.strip() for c in odom_df.columns]
        print(f"Odometry rows: {len(odom_df)}")
        print(f"Columns: {list(odom_df.columns)}")
        print(f"Trajectory bounds:")
        print(f"  X: [{odom_df['x'].min():.3f}, {odom_df['x'].max():.3f}] m")
        print(f"  Y: [{odom_df['y'].min():.3f}, {odom_df['y'].max():.3f}] m")
        print(f"  Z: [{odom_df['z'].min():.3f}, {odom_df['z'].max():.3f}] m")
    else:
        print("Odometry not found!")
        odom_df = None

    # 3. Depth & Confidence files
    depth_dir = os.path.join(dataset_dir, "depth")
    conf_dir = os.path.join(dataset_dir, "confidence")
    depth_files = sorted(glob.glob(os.path.join(depth_dir, "*.png")))
    conf_files = sorted(glob.glob(os.path.join(conf_dir, "*.png"))) if os.path.exists(conf_dir) else []
    
    print(f"Depth frames found: {len(depth_files)}")
    print(f"Confidence frames found: {len(conf_files)}")
    
    if depth_files:
        sample_depth = cv2.imread(depth_files[0], cv2.IMREAD_UNCHANGED)
        print(f"Depth map shape: {sample_depth.shape}, dtype: {sample_depth.dtype}")
        valid_depth = sample_depth[sample_depth > 0]
        if len(valid_depth) > 0:
            print(f"Depth stats (raw mm): min={valid_depth.min()}, median={np.median(valid_depth):.1f}, max={valid_depth.max()}")
            print(f"Depth stats (meters): min={valid_depth.min()/1000.0:.2f}m, median={np.median(valid_depth)/1000.0:.2f}m, max={valid_depth.max()/1000.0:.2f}m")
    
    if conf_files:
        sample_conf = cv2.imread(conf_files[0], cv2.IMREAD_UNCHANGED)
        print(f"Confidence map shape: {sample_conf.shape}, dtype: {sample_conf.dtype}")
        unique_conf = np.unique(sample_conf)
        print(f"Confidence unique values: {unique_conf} (0=low, 1=medium, 2=high)")

    # 4. Video info
    video_path = os.path.join(dataset_dir, "rgb.mp4")
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        print(f"RGB Video: {w}x{h} @ {fps:.1f} fps, Total Frames={n_frames}")

    return K, odom_df, depth_files, conf_files

if __name__ == "__main__":
    scan_path = "Assignment - YC Startup/single_room/c00a170fe1"
    inspect_dataset(scan_path)
