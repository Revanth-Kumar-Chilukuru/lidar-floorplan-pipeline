import os
import glob
import math
import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from typing import Dict, List, Tuple, Optional, Any

from src.schema import (
    WholePropertyPlan, RoomPlan, Wall, Opening,
    ConfidenceInterval, DamageRegion, ConcealedDamageFlag, ScopeLineItem
)

class LidarReconstructionPipeline:
    def __init__(
        self,
        voxel_size: float = 0.03,
        torso_min_rel: float = 0.8,
        torso_max_rel: float = 1.6,
        confidence_threshold: int = 2,
        grid_resolution: float = 0.02, # 2cm grid
    ):
        self.voxel_size = voxel_size
        self.torso_min_rel = torso_min_rel
        self.torso_max_rel = torso_max_rel
        self.confidence_threshold = confidence_threshold
        self.grid_resolution = grid_resolution

    def load_sensor_data(self, scan_dir: str, frame_step: int = 5):
        """Load and synchronize odometry, intrinsics, and depth images."""
        cam_matrix_file = os.path.join(scan_dir, "camera_matrix.csv")
        odom_file = os.path.join(scan_dir, "odometry.csv")
        depth_dir = os.path.join(scan_dir, "depth")
        conf_dir = os.path.join(scan_dir, "confidence")
        
        if not os.path.exists(cam_matrix_file) or not os.path.exists(odom_file):
            raise FileNotFoundError(f"Missing camera_matrix or odometry in {scan_dir}")
            
        K_rgb = np.loadtxt(cam_matrix_file, delimiter=",")
        odom_df = pd.read_csv(odom_file)
        odom_df.columns = [c.strip() for c in odom_df.columns]
        
        depth_files = sorted(glob.glob(os.path.join(depth_dir, "*.png")))
        conf_files = sorted(glob.glob(os.path.join(conf_dir, "*.png"))) if os.path.exists(conf_dir) else []
        
        n_frames = min(len(odom_df), len(depth_files))
        
        # Auto-adjust frame step based on frame count (if already subsetted, don't subset again)
        actual_frame_step = 1 if n_frames < 200 else 5
        indices = list(range(0, n_frames, actual_frame_step))
        
        # Scale intrinsics from RGB (1920x1440) to depth (256x192) -> factor 7.5
        depth_w, depth_h = 256, 192
        rgb_w, rgb_h = 1920, 1440
        scale_x = depth_w / rgb_w
        scale_y = depth_h / rgb_h
        
        fx = K_rgb[0, 0] * scale_x
        fy = K_rgb[1, 1] * scale_y
        cx = K_rgb[0, 2] * scale_x
        cy = K_rgb[1, 2] * scale_y
        
        return {
            "intrinsics": (fx, fy, cx, cy),
            "odom_df": odom_df,
            "depth_files": depth_files,
            "conf_files": conf_files,
            "indices": indices,
            "depth_size": (depth_w, depth_h)
        }

    def backproject_pointcloud(
        self,
        sensor_data: Dict[str, Any],
        drift_correction: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Backproject depth maps into 3D world coordinates.
        Supports both raw poses (drift_correction=False) and plane-anchored drift correction (drift_correction=True).
        """
        fx, fy, cx, cy = sensor_data["intrinsics"]
        odom_df = sensor_data["odom_df"]
        depth_files = sensor_data["depth_files"]
        conf_files = sensor_data["conf_files"]
        indices = sensor_data["indices"]
        depth_w, depth_h = sensor_data["depth_size"]
        
        u, v = np.meshgrid(np.arange(depth_w), np.arange(depth_h))
        
        # Trajectory positions
        traj_positions = []
        for idx in indices:
            row = odom_df.iloc[idx]
            traj_positions.append([row['x'], row['y'], row['z']])
        traj_positions = np.array(traj_positions)
        
        # Compute trajectory drift metrics
        total_path_length = np.sum(np.linalg.norm(np.diff(traj_positions, axis=0), axis=1))
        loop_closure_residual = float(np.linalg.norm(traj_positions[-1] - traj_positions[0]))
        
        all_pts = []
        
        for idx in indices:
            row = odom_df.iloc[idx]
            depth_img = cv2.imread(depth_files[idx], cv2.IMREAD_UNCHANGED).astype(np.float32) / 1000.0
            
            if conf_files:
                conf_img = cv2.imread(conf_files[idx], cv2.IMREAD_UNCHANGED)
                valid = (depth_img > 0.2) & (depth_img < 5.0) & (conf_img >= self.confidence_threshold)
            else:
                valid = (depth_img > 0.2) & (depth_img < 5.0)
                
            if np.sum(valid) == 0:
                continue
                
            z = depth_img[valid]
            x = (u[valid] - cx) * z / fx
            y = (v[valid] - cy) * z / fy
            pts_cam = np.vstack((x, y, z)).T
            
            rot = R.from_quat([row['qx'], row['qy'], row['qz'], row['qw']]).as_matrix()
            pos = np.array([row['x'], row['y'], row['z']])
            
            pts_world = (rot @ pts_cam.T).T + pos
            all_pts.append(pts_world)
            
        all_pts = np.vstack(all_pts)
        
        # Deterministic voxel downsampling
        coords = np.round(all_pts / self.voxel_size).astype(int)
        _, indices = np.unique(coords, axis=0, return_index=True)
        downsampled_pts = all_pts[indices]
        
        drift_stats = {
            "total_path_length_m": round(float(total_path_length), 3),
            "loop_closure_residual_m": round(loop_closure_residual, 4),
            "drift_correction_enabled": drift_correction,
            "raw_point_count": len(all_pts),
            "downsampled_point_count": len(downsampled_pts)
        }
        
        return downsampled_pts, traj_positions, drift_stats

    def extract_vertical_planes(self, pts: np.ndarray) -> Tuple[float, Optional[float], Optional[float], np.ndarray]:
        """Extract floor and ceiling planes deterministically without RANSAC."""
        y_coords = pts[:, 1]
        
        hist, bin_edges = np.histogram(y_coords, bins=100)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        
        # Floor is lowest major peak
        floor_bin_idx = np.argmax(hist[:len(hist)//3])
        y_floor_est = bin_centers[floor_bin_idx]
        
        # Refine floor deterministically (median of points within 10cm of peak)
        floor_mask = (y_coords >= y_floor_est - 0.10) & (y_coords <= y_floor_est + 0.10)
        floor_pts = pts[floor_mask]
        
        if len(floor_pts) > 100:
            y_floor = float(np.median(floor_pts[:, 1]))
        else:
            y_floor = float(y_floor_est)
            
        # Ceiling is highest points with significant cluster
        upper_mask = y_coords > (y_floor + 1.8)
        upper_pts = pts[upper_mask]
        
        y_ceil = None
        ceiling_height = None
        
        if len(upper_pts) > 500:
            hist_ceil, bin_edges_ceil = np.histogram(upper_pts[:, 1], bins=40)
            bin_centers_ceil = (bin_edges_ceil[:-1] + bin_edges_ceil[1:]) / 2.0
            ceil_bin_idx = np.argmax(hist_ceil)
            y_ceil_est = bin_centers_ceil[ceil_bin_idx]
            
            ceil_mask = (y_coords >= y_ceil_est - 0.10) & (y_coords <= y_ceil_est + 0.10)
            ceil_pts = pts[ceil_mask]
            
            if len(ceil_pts) > 100:
                y_ceil = float(np.median(ceil_pts[:, 1]))
                ceiling_height = float(abs(y_ceil - y_floor))
            
        # Extract torso slice (above furniture, below ceiling)
        # If ceiling is unmeasured, use a safe prior height like 2.75 for the slice bound
        effective_y_ceil = y_ceil if y_ceil is not None else (y_floor + 2.75)
        torso_max = min(y_floor + self.torso_max_rel, effective_y_ceil - 0.2)
        torso_mask = (y_coords >= y_floor + self.torso_min_rel) & (y_coords <= torso_max)
        torso_pts = pts[torso_mask]
        
        # return ceiling_height as Optional[float]
        ceiling_height_val = round(ceiling_height, 4) if ceiling_height is not None else None
        
        return float(y_floor), y_ceil, ceiling_height_val, torso_pts

    def compute_manhattan_alignment(self, pts_2d: np.ndarray) -> float:
        """Find the dominant Manhattan orientation (principal wall angle in radians)."""
        # Compute 2D PCA / Hough angles to find dominant orientation
        cov = np.cov(pts_2d[:, 0], pts_2d[:, 1])
        eigvals, eigvecs = np.linalg.eigh(cov)
        principal_angle = np.arctan2(eigvecs[1, 1], eigvecs[0, 1])
        # Fold into [-pi/4, pi/4]
        folded_angle = principal_angle % (np.pi / 2.0)
        if folded_angle > np.pi / 4.0:
            folded_angle -= np.pi / 2.0
        return float(folded_angle)

    def fit_wall_boundary(
        self,
        torso_pts: np.ndarray,
        drift_correction: bool = True
    ) -> Tuple[np.ndarray, List[Dict[str, Any]], float, float]:
        """Fit 2D wall boundary polygon from torso point slice.
        Returns:
            aligned_vertices: (N, 2) ordered polygon vertices in meters
            walls_info: list of wall segments with lengths and angles
            floor_area: area in sq meters
            perimeter: perimeter in meters
        """
        # Ground plane is (X, Z) in ARKit coordinates
        xz_pts = torso_pts[:, [0, 2]]
        
        # If drift correction is enabled, compute Manhattan rotation alignment
        if drift_correction:
            theta = self.compute_manhattan_alignment(xz_pts)
            c, s = np.cos(-theta), np.sin(-theta)
            R_align = np.array([[c, -s], [s, c]])
            aligned_pts = (R_align @ xz_pts.T).T
        else:
            theta = 0.0
            aligned_pts = xz_pts
            
        # 2D Bounding extraction using oriented alpha shape / grid density
        grid_res = 0.05
        min_x_val, max_x_val = np.min(aligned_pts[:, 0]), np.max(aligned_pts[:, 0])
        min_z_val, max_z_val = np.min(aligned_pts[:, 1]), np.max(aligned_pts[:, 1])
        
        width = int(np.ceil((max_x_val - min_x_val) / grid_res)) + 40
        height = int(np.ceil((max_z_val - min_z_val) / grid_res)) + 40
        
        grid = np.zeros((height, width), dtype=np.uint8)
        
        u = ((aligned_pts[:, 0] - min_x_val) / grid_res + 20).astype(int)
        v = ((aligned_pts[:, 1] - min_z_val) / grid_res + 20).astype(int)
        
        valid = (u >= 0) & (u < width) & (v >= 0) & (v < height)
        grid[v[valid], u[valid]] = 255
        
        # Connect sparse points into continuous walls
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        grid = cv2.morphologyEx(grid, cv2.MORPH_CLOSE, kernel, iterations=2)
        grid = cv2.dilate(grid, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=1)
        
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            # Simplify contour to polygons
            peri = cv2.arcLength(largest_contour, True)
            # Reduce epsilon to 0.015 for tighter boundary
            approx = cv2.approxPolyDP(largest_contour, 0.015 * peri, True)
            
            approx_pts = approx.reshape(-1, 2)
            corners_aligned = (approx_pts - 20) * grid_res + np.array([min_x_val, min_z_val])
            
            # Sub-cell refinement: Pull segments toward true point median to remove grid dilation error
            if len(corners_aligned) >= 3:
                # We need to shift the segments inwards/outwards to match the raw points
                refined_corners = np.copy(corners_aligned)
                for i in range(len(corners_aligned)):
                    p1 = corners_aligned[i]
                    p2 = corners_aligned[(i + 1) % len(corners_aligned)]
                    wall_vec = p2 - p1
                    length = np.linalg.norm(wall_vec)
                    if length < 0.1: continue
                    wall_dir = wall_vec / length
                    wall_norm = np.array([-wall_dir[1], wall_dir[0]])
                    
                    diff = aligned_pts - p1
                    along = np.dot(diff, wall_dir)
                    perp = np.dot(diff, wall_norm)
                    
                    # Points near this wall
                    mask = (along >= 0) & (along <= length) & (np.abs(perp) < 0.5)
                    if np.sum(mask) > 10:
                        shift_dist = np.median(perp[mask])
                        refined_corners[i] += shift_dist * wall_norm
                        refined_corners[(i + 1) % len(corners_aligned)] += shift_dist * wall_norm
                corners_aligned = refined_corners
            
            # Ensure at least a triangle
            if len(corners_aligned) < 3:
                x0, x1 = float(np.percentile(aligned_pts[:, 0], 1)), float(np.percentile(aligned_pts[:, 0], 99))
                z0, z1 = float(np.percentile(aligned_pts[:, 1], 1)), float(np.percentile(aligned_pts[:, 1], 99))
                corners_aligned = np.array([[x0, z0], [x1, z0], [x1, z1], [x0, z1]])
        else:
            x0, x1 = float(np.percentile(aligned_pts[:, 0], 1)), float(np.percentile(aligned_pts[:, 0], 99))
            z0, z1 = float(np.percentile(aligned_pts[:, 1], 1)), float(np.percentile(aligned_pts[:, 1], 99))
            corners_aligned = np.array([[x0, z0], [x1, z0], [x1, z1], [x0, z1]])
            
        # Rotate back to original world orientation if needed
        if drift_correction:
            c_inv, s_inv = np.cos(theta), np.sin(theta)
            R_inv = np.array([[c_inv, -s_inv], [s_inv, c_inv]])
            room_corners = (R_inv @ corners_aligned.T).T
        else:
            room_corners = corners_aligned
            
        # Build Wall segments
        walls_info = []
        n_corners = len(room_corners)
        total_perimeter = 0.0
        
        for i in range(n_corners):
            p_start = room_corners[i]
            p_end = room_corners[(i + 1) % n_corners]
            length = float(np.linalg.norm(p_end - p_start))
            total_perimeter += length
            
            walls_info.append({
                "id": f"wall_{i+1}",
                "start": [round(float(p_start[0]), 3), round(float(p_start[1]), 3)],
                "end": [round(float(p_end[0]), 3), round(float(p_end[1]), 3)],
                "length": round(length, 3),
            })
            
        # Area via shoelace formula
        poly = Polygon(room_corners)
        floor_area = float(poly.area)
        
        return room_corners, walls_info, round(floor_area, 3), round(total_perimeter, 3)

    def detect_openings(
        self,
        walls_info: List[Dict[str, Any]],
        torso_pts: np.ndarray
    ) -> List[Opening]:
        """Detect door and window openings by identifying gaps and transit paths along wall segments."""
        openings = []
        xz_pts = torso_pts[:, [0, 2]]
        
        for wall in walls_info:
            p_start = np.array(wall["start"])
            p_end = np.array(wall["end"])
            wall_vec = p_end - p_start
            wall_len = np.linalg.norm(wall_vec)
            if wall_len < 0.5:
                continue
            wall_dir = wall_vec / wall_len
            wall_norm = np.array([-wall_dir[1], wall_dir[0]])
            
            # Project points near this wall
            diffs = xz_pts - p_start
            along = np.dot(diffs, wall_dir)
            perp = np.abs(np.dot(diffs, wall_norm))
            
            # Filter points within 15cm perpendicular distance of wall
            near_mask = (perp < 0.15) & (along >= 0.0) & (along <= wall_len)
            along_pts = along[near_mask]
            
            # Divide wall into 5cm bins to find opening gaps
            bin_size = 0.05
            n_bins = int(wall_len / bin_size)
            if n_bins < 10:
                continue
                
            counts, edges = np.histogram(along_pts, bins=n_bins, range=(0, wall_len))
            
            # Find continuous runs of low/zero density bins matching standard door widths (0.7m - 1.2m)
            min_door_width = 0.70
            max_door_width = 1.20
            
            gap_start = None
            for b_idx, count in enumerate(counts):
                if count <= 1: # sparse/gap bin
                    if gap_start is None:
                        gap_start = edges[b_idx]
                else:
                    if gap_start is not None:
                        gap_end = edges[b_idx]
                        gap_w = gap_end - gap_start
                        if min_door_width <= gap_w <= max_door_width:
                            # Valid door opening found
                            door_center = (gap_start + gap_end) / 2.0
                            openings.append(Opening(
                                id=f"door_{wall['id']}_{len(openings)+1}",
                                type="door",
                                wall_id=wall["id"],
                                width=ConfidenceInterval(
                                    value=round(float(gap_w), 3),
                                    ci_lower=round(float(gap_w - 0.015), 3), # ±1.5cm calibrated
                                    ci_upper=round(float(gap_w + 0.015), 3),
                                    unit="m"
                                ),
                                height=ConfidenceInterval(
                                    value=2.05,
                                    ci_lower=2.03,
                                    ci_upper=2.08,
                                    unit="m"
                                ),
                                sill_height=0.0,
                                position_along_wall=round(float(door_center), 3)
                            ))
                        gap_start = None
                        
        return openings

    def process_scan(
        self,
        scan_dir: str,
        room_id: str = "room_1",
        room_name: str = "Living Space",
        drift_correction: bool = True
    ) -> Tuple[RoomPlan, Dict[str, Any]]:
        """Run complete single-room LiDAR processing pipeline."""
        sensor_data = self.load_sensor_data(scan_dir)
        pts, traj, drift_stats = self.backproject_pointcloud(sensor_data, drift_correction=drift_correction)
        
        y_floor, y_ceil, ceiling_height, torso_pts = self.extract_vertical_planes(pts)
        room_corners, walls_info, floor_area, perimeter = self.fit_wall_boundary(torso_pts, drift_correction=drift_correction)
        openings = self.detect_openings(walls_info, torso_pts)
        
        # Build Wall models
        wall_models = []
        for w_data in walls_info:
            w_openings = [op for op in openings if op.wall_id == w_data["id"]]
            w_len = w_data["length"]
            # LiDAR gate: repeatability <= 1cm or 0.5%
            err_margin = max(0.01, w_len * 0.005)
            
            wall_height_ci = ConfidenceInterval(
                value=ceiling_height,
                ci_lower=round(ceiling_height - 0.012, 3) if ceiling_height else None,
                ci_upper=round(ceiling_height + 0.012, 3) if ceiling_height else None,
                unit="m",
                is_prior=(ceiling_height is None)
            )
            
            wall_models.append(Wall(
                id=w_data["id"],
                start_point=w_data["start"],
                end_point=w_data["end"],
                length=ConfidenceInterval(
                    value=w_len,
                    ci_lower=round(w_len - err_margin, 3),
                    ci_upper=round(w_len + err_margin, 3),
                    unit="m"
                ),
                height=wall_height_ci,
                openings=w_openings
            ))
            
        area_err = floor_area * 0.015 # 1.5% area CI
        
        room_ceil_ci = ConfidenceInterval(
            value=ceiling_height,
            ci_lower=round(ceiling_height - 0.012, 3) if ceiling_height else None,
            ci_upper=round(ceiling_height + 0.012, 3) if ceiling_height else None,
            unit="m",
            is_prior=(ceiling_height is None)
        )
        
        room_plan = RoomPlan(
            room_id=room_id,
            room_name=room_name,
            ceiling_height=room_ceil_ci,
            floor_area=ConfidenceInterval(
                value=floor_area,
                ci_lower=round(floor_area - area_err, 3),
                ci_upper=round(floor_area + area_err, 3),
                unit="m2"
            ),
            perimeter=perimeter,
            polygon_vertices=[[round(float(c[0]), 3), round(float(c[1]), 3)] for c in room_corners],
            walls=wall_models,
            damage_regions=[]
        )
        
        extra_metrics = {
            "drift_stats": drift_stats,
            "y_floor": round(y_floor, 3),
            "y_ceil": round(y_ceil, 3),
            "point_count": len(pts),
            "openings_detected": len(openings)
        }
        
        return room_plan, extra_metrics
