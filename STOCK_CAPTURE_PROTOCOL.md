# Stock Capture Protocol & Device Matrix (Route 2)

This one-page protocol is designed for non-engineer operators capturing properties using consumer iPhones.

---

## 1. Device Matrix & Hardware Limits

| Capture Tier | Required Hardware | Supported Devices | Pipeline Status |
| :--- | :--- | :--- | :--- |
| **Tier 3: LiDAR** | Direct Time-of-Flight LiDAR sensor + A15+ Bionic | iPhone 12 Pro/Pro Max through 16 Pro/Pro Max, iPad Pro 2020+ | **Active** (Verifiable metric output) |
| **Tier 2: Video** | Ultra-wide / 4K60p Camera | iPhone 11-16 (Non-Pro and Pro devices) | **Not Implemented** (Requires external ML models) |
| **Tier 1: Photos** | Native Camera | Any modern smartphone | **Not Implemented** (Requires external ML models) |

**Important Hardware Note**: The Stray Scanner app *requires* a LiDAR-equipped Apple device (Pro or Pro Max). Non-Pro devices lack the depth sensor and cannot generate the required point cloud data. Attempting to use the pipeline without a Pro device means relying on the Video or Photo tiers, which are currently disabled in this implementation.

---

## 2. Capture Protocol Instructions

### App Installation (Under 2 Minutes)
1. **For LiDAR Tier (Pro Devices Only):**
   * Open the Apple App Store on your iPhone Pro.
   * Search for **"Stray Scanner"** (by Stray Robots - Free, open source).
   * Install the app and allow **Camera** and **Motion & Orientation** permissions.
2. **For Video & Photo Tiers (If implemented in future):**
   * Use the iOS native **Camera** app.

---

### Step-by-Step Operator Walking Guide

#### A. Pre-Scan Preparation (30 seconds)
1. Turn on all interior overhead lights. Open room doors fully against walls.
2. Hold the iPhone at **chest height (~1.40m)**, tilted slightly downward (~$15^\circ$) so the floor boundary is visible in the lower half of the frame.

#### B. Walking the Space (LiDAR / Video)
* **Walk Pace:** Maintain a steady, smooth walking pace (approx. **$0.5\text{ m/s}$**).
* **Trajectory:** Walk continuously along the room perimeter in a clockwise loop. Traverse connectors (hallways) with a sweeping motion across both walls.
* **Ceiling & Openings:** At doorway transitions, pause for 1 second and tilt the device up smoothly toward the ceiling joist, then level back to chest height.

#### C. Photo Tier Capture (If implemented)
* Stand in the center of the room and take 4-8 overlapping photos pointing at the walls, ensuring corners are visible.
* **Folder Naming:** You *must* save photos into per-room folders (e.g., `bedroom_1/`, `kitchen/`) to allow the pipeline to stitch and process rooms individually.

#### D. What to Avoid
* ❌ **Do NOT run or make abrupt rotational jerks** (causes visual odometry tracking loss).
* ❌ **Do NOT point exclusively at blank white ceilings or featureless floors** for more than 3 seconds.
* ❌ **Do NOT stand stationary while rotating on your heels** (creates rotational drift without parallax). Always translate through the room.

---

### Handing Files to the Pipeline

1. **LiDAR Tier:**
   * In Stray Scanner, tap **Stop Recording**.
   * Connect iPhone to PC via USB or AirDrop the scan folder (named with UUID, e.g., `c7d28f72c6`).
   * Run:
     ```bash
     python main.py --input path/to/c7d28f72c6 --tier lidar
     ```

2. **Video Tier & Photo Tier:**
   * **Note:** The Video and Photo tiers are currently **not implemented** in the software pipeline due to hardware/compute constraints. If they were implemented, they would require standard RGB video or HEIC photos captured from the native iOS Camera app.
