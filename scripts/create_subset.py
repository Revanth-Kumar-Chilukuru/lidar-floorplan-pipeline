"""
Author: Revanth Kumar Chilukuru
"""
import os
import shutil
import pandas as pd
import glob

def create_subset(src_dir, dest_dir, step=5):
    if not os.path.exists(src_dir):
        print(f"Source {src_dir} not found.")
        return
        
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copy camera_matrix.csv
    if os.path.exists(os.path.join(src_dir, 'camera_matrix.csv')):
        shutil.copy2(os.path.join(src_dir, 'camera_matrix.csv'), dest_dir)
        
    # Read odometry to find valid frames
    odom_path = os.path.join(src_dir, 'odometry.csv')
    if os.path.exists(odom_path):
        df = pd.read_csv(odom_path)
        # Take every step-th frame
        df_subset = df.iloc[::step].copy()
        df_subset.to_csv(os.path.join(dest_dir, 'odometry.csv'), index=False)
        
        # Copy corresponding depth and confidence
        os.makedirs(os.path.join(dest_dir, 'depth'), exist_ok=True)
        os.makedirs(os.path.join(dest_dir, 'confidence'), exist_ok=True)
        
        # The original filenames are 000000.png, 000001.png, etc. corresponding to the row index
        for idx in df_subset.index:
            idx_str = f"{idx:06d}"
            d_src = os.path.join(src_dir, 'depth', f"{idx_str}.png")
            c_src = os.path.join(src_dir, 'confidence', f"{idx_str}.png")
            
            # The indices in the subset should be renamed to match their new row index?
            # Or just copy the selected frames and keep their original names, and subset the odometry to match?
            # Wait, the pipeline relies on the filenames in depth/ to match the rows in odometry.csv?
            # Let's just copy everything that is in df_subset and keep original names, 
            # BUT the pipeline in `lidar_pipeline.py` lists depth_files = sorted(glob.glob(os.path.join(depth_dir, "*.png")))
            # and matches them 1-to-1 with odom_df rows!
            # SO we MUST rename them sequentially!
            new_idx_str = f"{len(os.listdir(os.path.join(dest_dir, 'depth'))):06d}"
            
            if os.path.exists(d_src):
                shutil.copy2(d_src, os.path.join(dest_dir, 'depth', f"{new_idx_str}.png"))
            if os.path.exists(c_src):
                shutil.copy2(c_src, os.path.join(dest_dir, 'confidence', f"{new_idx_str}.png"))
    else:
        print(f"No odometry found in {src_dir}")

def main():
    base_src = "Assignment - YC Startup"
    base_dest = "data/sample_subset"
    
    scans = [
        "single_room/c00a170fe1", 
        "single_scan_with_ceiling/c7d28f72c6",
        "single_scan_floor_only/1a8384c3f6"
    ]
    
    for s in scans:
        print(f"Creating subset for {s}...")
        create_subset(os.path.join(base_src, s), os.path.join(base_dest, s), step=5)
        
    print("Subset creation complete.")

if __name__ == "__main__":
    main()
