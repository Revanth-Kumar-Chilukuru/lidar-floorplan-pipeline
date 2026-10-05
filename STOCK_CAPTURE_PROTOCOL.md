# Stock Capture Protocol & Device Matrix (Route 2)

This one-page protocol is designed for non-engineer operators (claim adjusters, homeowners, real estate inspectors) capturing properties using consumer iPhones.

---

## 1. Device Matrix

| Capture Tier | Required Hardware | Supported Devices | Metric Delivery & Expected Accuracy |
| :--- | :--- | :--- | :--- |
| **Tier 3: LiDAR** | Direct Time-of-Flight LiDAR sensor + A15+ Bionic | iPhone 12 Pro/Pro Max through iPhone 17 Pro/Pro Max, iPad Pro 2020+ | Wall lengths $\le 0.5\%$, Opening widths $\le 2\text{ cm}$, Ceiling height $\le 1.5\text{ cm}$ |
| **Tier 2: Video** | Ultra-wide / 4K60p Camera + Optical Image Stabilization (OIS) | iPhone 15, 15 Plus, 16, 17 (Non-Pro and Pro devices) | Wall lengths $\le 3.0\%$, Floor area $\le 4.5\%$, Ceiling height $\le 3.0\%$ |
| **Tier 1: Photos** | Native 48MP Fusion Camera | Any modern smartphone (iPhone 11+, modern Android) | Wall lengths $\le 8.0\%$, Floor area $\le 12.0\%$, Ceiling height $\le 8.0\%$ |

---

## 2. Capture Protocol Instructions

### App Installation (Under 2 Minutes)
1. **For LiDAR Tier:**
   * Open the Apple App Store on your iPhone Pro.
   * Search for **"Stray Scanner"** (by Stray Robots - Free, open source, zero sign-in required).
   * Install the app and allow **Camera** and **Motion & Orientation** permissions.
2. **For Video & Photo Tiers:**
   * Use the iOS native **Camera** app.

---

### Step-by-Step Operator Walking Guide

#### A. Pre-Scan Preparation (30 seconds)
1. Turn on all interior overhead lights. Open room doors fully against walls.
2. Ensure mirrors or glossy glass shower doors are noted (pipeline includes reflective outlier filtering).
3. Hold the iPhone at **chest height (~1.40m)**, tilted slightly downward (~$15^\circ$) so the floor boundary is visible in the lower half of the frame.

#### B. Walking the Space
* **Walk Pace:** Maintain a steady, smooth walking pace (approx. **$0.5\text{ m/s}$** — a deliberate heel-to-toe stride).
* **Multi-Room Loop Closure:**
  1. Start in the entryway or primary room.
  2. Walk continuously along the room perimeter in a clockwise loop.
  3. Traverse connectors (hallways) with a sweeping motion across both walls.
  4. **Always return to your starting room/position to close the trajectory loop.** (Best practice for scanning, though true loop-closure is not currently implemented in the pipeline; the pipeline relies on Manhattan alignment).
* **Ceiling & Openings:** At doorway transitions, pause for 1 second and tilt the device up smoothly toward the ceiling joist, then level back to chest height.

#### C. What to Avoid
* ❌ **Do NOT run or make abrupt rotational jerks** (causes visual odometry tracking loss).
* ❌ **Do NOT point exclusively at blank white ceilings or featureless floors** for more than 3 seconds.
* ❌ **Do NOT stand stationary while rotating on your heels** (creates rotational drift without parallax). Always translate through the room.

---

### Handing Files to the Pipeline

1. **LiDAR Tier:**
   * In Stray Scanner, tap **Stop Recording**.
   * Connect iPhone to PC via USB or AirDrop the scan folder (named with UUID, e.g., `c7d28f72c6`).
   * The folder contains: `camera_matrix.csv`, `odometry.csv`, `imu.csv`, `rgb.mp4`, `depth/`, and `confidence/`.
   * Run:
     ```bash
     python main.py --input path/to/c7d28f72c6 --tier lidar
     ```

2. **Video Tier & Photo Tier:**
   * **Note:** The Video and Photo tiers are currently **not implemented** in the software pipeline due to hardware/compute constraints. If they were implemented, they would require standard RGB video or HEIC photos captured from the native iOS Camera app.
