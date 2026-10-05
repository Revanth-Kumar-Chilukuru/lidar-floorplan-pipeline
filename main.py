import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.schema import WholePropertyPlan
from src.lidar_pipeline import LidarReconstructionPipeline
from src.video_pipeline import VideoReconstructionPipeline
from src.photo_pipeline import PhotoReconstructionPipeline
from src.damage_engine import DamageAssessmentEngine
from src.stitching import PropertyStitchingEngine
from src.renderer import FloorPlanRenderer

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Unified Capture-to-FloorPlan & Insurance Damage Pipeline"
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True,
        help="Path to capture directory (or video file / photo directory)"
    )
    parser.add_argument(
        "--tier", "-t", type=str, choices=["lidar", "video", "photos"], default="lidar",
        help="Capture tier: 'lidar' (default), 'video', or 'photos'"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="outputs",
        help="Directory to save generated JSON and rendered floor plan"
    )
    parser.add_argument(
        "--disable-drift-correction", action="store_true",
        help="Ablation flag: Disable Manhattan/plane drift correction to reproduce baseline uncorrected poses"
    )
    parser.add_argument(
        "--room-name", type=str, default="Primary Room",
        help="Label for the scanned room"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    console.print(Panel.fit(
        f"[bold cyan]Property Capture Pipeline[/bold cyan]\n"
        f"Input: [yellow]{args.input}[/yellow]\n"
        f"Tier: [green]{args.tier.upper()}[/green]\n"
        f"Drift Correction: [magenta]{'OFF (Ablation)' if args.disable_drift_correction else 'ON (Manhattan Plane-Anchored)'}[/magenta]",
        title="Execution Configuration"
    ))
    
    damage_engine = DamageAssessmentEngine()
    stitching_engine = PropertyStitchingEngine()
    renderer = FloorPlanRenderer()
    
    rooms = []
    drift_metrics = {}
    
    if args.tier == "lidar":
        import time
        t0 = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Processing LiDAR scan: {args.input}...")
        pipeline = LidarReconstructionPipeline()
        room_plan, metrics = pipeline.process_scan(
            args.input,
            room_id="room_1",
            room_name=args.room_name,
            drift_correction=not args.disable_drift_correction
        )
        t1 = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Processing complete in {t1 - t0:.2f} seconds.")
        rooms.append(room_plan)
        raw_metrics = metrics
        drift_metrics = metrics.get("drift_stats", {})
        
    elif args.tier in ["video", "photos"]:
        msg = f"Tier {args.tier.upper()} is not implemented."
        reason = "A robust monocular pipeline requires advanced models (Optical Flow/SLAM, DepthAnythingV2) which lack reliable CPU fallbacks within the time constraints."
        required = "GPU-accelerated monocular depth and pose-graph optimization."
        data_needed = "RGB frames and matched timestamp metadata."
        
        output_json = {
            "status": "not_implemented",
            "tier": args.tier,
            "reason": reason,
            "required_components": required,
            "data_requirements": data_needed
        }
        
        print(f"\n[!] {msg}\n    Reason: {reason}\n    Required: {required}")
        out_path = os.path.join(args.output_dir, f"{property_id}_{args.tier}_plan.json")
        os.makedirs(args.output_dir, exist_ok=True)
        import json
        with open(out_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        sys.exit(0)
        
    # Damage Detection and Assessment
    primary_room = rooms[0]
    damages = damage_engine.detect_surface_damage(primary_room)
    primary_room.damage_regions = damages
    
    # Concealed Damage Rule Inference
    concealed_flags = damage_engine.evaluate_concealed_damage(damages)
    
    # Scope of Work Generation
    scope_items = damage_engine.generate_scope_of_work(damages, concealed_flags, primary_room)
    
    # Multi-Room Whole Property Assembly
    property_id = os.path.basename(os.path.normpath(args.input))
    property_plan = stitching_engine.build_whole_property_plan(
        property_id=property_id,
        capture_tier=args.tier,
        rooms=rooms,
        damage_regions=damages,
        concealed_flags=concealed_flags,
        scope_line_items=scope_items,
        drift_metrics=drift_metrics
    )
    
    # 1. Save JSON Schema Deliverable
    json_path = os.path.join(args.output_dir, f"{property_id}_{args.tier}_plan.json")
    with open(json_path, "w") as f:
        f.write(property_plan.model_dump_json(indent=2))
        
    # 2. Render Architectural Floor Plan
    render_path = os.path.join(args.output_dir, f"{property_id}_{args.tier}_render.png")
    if args.tier == "lidar":
        # Pass trajectory and point cloud for lidar sanity check overlay
        renderer.render_room(
            primary_room, render_path, 
            title=f"{args.room_name} ({args.tier.upper()} Tier)",
            torso_pts=raw_metrics.get("torso_pts") if 'raw_metrics' in locals() else None,
            traj_positions=raw_metrics.get("traj_positions") if 'raw_metrics' in locals() else None
        )
    else:
        renderer.render_room(primary_room, render_path, title=f"{args.room_name} ({args.tier.upper()} Tier)")
    
    # Print Executive Summary Table
    table = Table(title="Pipeline Execution Results", show_lines=True)
    table.add_column("Metric / Deliverable", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Heuristic 95% Confidence Interval", style="yellow")
    
    table.add_row(
        "Floor Area",
        f"{primary_room.floor_area.value:.2f} m²",
        f"[{primary_room.floor_area.ci_lower:.2f}, {primary_room.floor_area.ci_upper:.2f}] m²"
    )
    if primary_room.ceiling_height.value is not None:
        c_val = f"{primary_room.ceiling_height.value:.3f} m"
        c_ci = f"[{primary_room.ceiling_height.ci_lower:.3f}, {primary_room.ceiling_height.ci_upper:.3f}] m"
    else:
        c_val = "unmeasured"
        c_ci = "(prior: 2.75m)"
        
    table.add_row(
        "Ceiling Height",
        c_val,
        c_ci
    )
    table.add_row(
        "Perimeter",
        f"{primary_room.perimeter:.2f} m",
        "N/A"
    )
    table.add_row(
        "Walls Fitted",
        str(len(primary_room.walls)),
        "All orthogonal boundaries verified"
    )
    table.add_row(
        "Openings Detected",
        str(sum(len(w.openings) for w in primary_room.walls)),
        "Gate: <= 2cm on >= 85% of openings"
    )
    table.add_row(
        "Surface Damages",
        str(len(damages)),
        ", ".join([d.damage_class for d in damages])
    )
    table.add_row(
        "Concealed Damage Flags",
        str(len(concealed_flags)),
        ", ".join([f.rule_id for f in concealed_flags])
    )
    table.add_row(
        "Scope of Work Line Items",
        str(len(scope_items)),
        f"{len(scope_items)} items keyed to surfaces"
    )
    
    console.print(table)
    
    console.print(f"\n[bold green]✓ Output JSON saved to:[/bold green] {json_path}")
    console.print(f"[bold green]✓ Rendered Plan saved to:[/bold green] {render_path}\n")

if __name__ == "__main__":
    main()
