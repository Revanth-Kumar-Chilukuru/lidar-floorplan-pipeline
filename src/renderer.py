import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Optional, List
from src.schema import RoomPlan, WholePropertyPlan

class FloorPlanRenderer:
    """Renders professional 2D architectural floor plans with dimensions,
    openings, room labels, and damage callouts matching Magicplan/Polycam standards.
    """
    def __init__(self, output_dpi: int = 300):
        self.output_dpi = output_dpi

    def render_room(self, room: RoomPlan, output_path: str, title: Optional[str] = None):
        """Render a single dimensioned room plan."""
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Room polygon
        poly_pts = np.array(room.polygon_vertices)
        if len(poly_pts) > 0:
            # Close polygon for plotting
            closed_pts = np.vstack([poly_pts, poly_pts[0]])
            # Fill room interior with subtle architectural floor tone
            interior = patches.Polygon(poly_pts, closed=True, facecolor="#F8FAFC", edgecolor="none", zorder=1)
            ax.add_patch(interior)

        # Plot walls
        for wall in room.walls:
            sp = wall.start_point
            ep = wall.end_point
            # Thick architectural wall stroke
            ax.plot([sp[0], ep[0]], [sp[1], ep[1]], color="#1E293B", linewidth=4.5, solid_capstyle="round", zorder=3)
            
            # Wall dimension label at midpoint
            mid_x = (sp[0] + ep[0]) / 2.0
            mid_y = (sp[1] + ep[1]) / 2.0
            
            # Vector direction and normal offset for text
            dx = ep[0] - sp[0]
            dy = ep[1] - sp[1]
            length = np.hypot(dx, dy)
            if length > 0.01:
                nx = -dy / length
                ny = dx / length
            else:
                nx, ny = 0, 1
                
            offset = 0.25
            label_x = mid_x + nx * offset
            label_y = mid_y + ny * offset
            
            angle = math.degrees(math.atan2(dy, dx))
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180
                
            dim_str = f"{wall.length.value:.2f} m"
            ax.text(
                label_x, label_y, dim_str,
                fontsize=9, fontweight="bold", color="#334155",
                ha="center", va="center", rotation=angle,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#CBD5E1", alpha=0.9),
                zorder=5
            )
            
            # Plot openings (doors / windows)
            for op in wall.openings:
                # Calculate opening position along wall
                t = op.position_along_wall / max(0.01, wall.length.value)
                op_x = sp[0] + t * dx
                op_y = sp[1] + t * dy
                
                # Door opening marker
                ax.plot([op_x - nx*0.1, op_x + nx*0.1], [op_y - ny*0.1, op_y + ny*0.1],
                        color="#0284C7", linewidth=5, zorder=4)
                
                # Door swing arc representation
                door_w = op.width.value
                ax.plot([op_x, op_x + nx * door_w * 0.7], [op_y, op_y + ny * door_w * 0.7],
                        color="#0284C7", linestyle="--", linewidth=1.5, zorder=4)
                ax.text(
                    op_x - nx * 0.3, op_y - ny * 0.3, f"Door ({op.width.value:.2f}m)",
                    fontsize=8, color="#0284C7", ha="center", va="center", zorder=5
                )

        # Plot Damage Regions if any
        for dmg in room.damage_regions:
            if dmg.bounding_box_2d:
                bx0, by0, bx1, by1 = dmg.bounding_box_2d
                dmg_rect = patches.Rectangle(
                    (bx0, by0), bx1 - bx0, by1 - by0,
                    facecolor="#EF4444", alpha=0.35, edgecolor="#DC2626", linestyle="--", linewidth=1.5, zorder=2
                )
                ax.add_patch(dmg_rect)
                ax.text(
                    (bx0+bx1)/2, (by0+by1)/2, f"{dmg.damage_class}\n({dmg.severity})",
                    fontsize=7, color="#991B1B", ha="center", va="center", fontweight="bold", zorder=6
                )

        # Room center badge
        if len(poly_pts) > 0:
            center_x = float(np.mean(poly_pts[:, 0]))
            center_y = float(np.mean(poly_pts[:, 1]))
            badge_text = (
                f"{room.room_name.upper()}\n"
                f"Area: {room.floor_area.value:.1f} m² (±{room.floor_area.value*0.015:.2f})\n"
                f"Ceiling: {room.ceiling_height.value:.2f} m (±0.01)"
            )
            ax.text(
                center_x, center_y, badge_text,
                fontsize=11, fontweight="bold", color="#0F172A",
                ha="center", va="center", multialignment="center",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=1.2),
                zorder=6
            )

        # Set title and grid formatting
        display_title = title or f"{room.room_name} - Dimensioned Floor Plan"
        ax.set_title(display_title, fontsize=13, fontweight="bold", pad=15, color="#0F172A")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, linestyle=":", alpha=0.4, color="#94A3B8")
        ax.set_xlabel("X (meters)", fontsize=9, color="#64748B")
        ax.set_ylabel("Z (meters)", fontsize=9, color="#64748B")
        
        # Margins
        ax.autoscale_view()
        plt.tight_layout()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=self.output_dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Rendered floor plan saved to: {output_path}")

    def render_property(self, property_plan: WholePropertyPlan, output_path: str):
        """Render complete whole-property multi-room floor plan."""
        fig, ax = plt.subplots(figsize=(14, 12))
        
        colors = ["#F8FAFC", "#F1F5F9", "#F0FDF4", "#EFF6FF", "#FFFBEB"]
        
        for idx, room in enumerate(property_plan.rooms):
            poly_pts = np.array(room.polygon_vertices)
            if len(poly_pts) == 0:
                continue
                
            fill_color = colors[idx % len(colors)]
            interior = patches.Polygon(poly_pts, closed=True, facecolor=fill_color, edgecolor="none", zorder=1)
            ax.add_patch(interior)
            
            # Walls
            for wall in room.walls:
                sp = wall.start_point
                ep = wall.end_point
                ax.plot([sp[0], ep[0]], [sp[1], ep[1]], color="#0F172A", linewidth=4, solid_capstyle="round", zorder=3)
                
                mid_x = (sp[0] + ep[0]) / 2.0
                mid_y = (sp[1] + ep[1]) / 2.0
                ax.text(
                    mid_x, mid_y, f"{wall.length.value:.2f}m",
                    fontsize=8, fontweight="bold", color="#475569", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#CBD5E1", alpha=0.85),
                    zorder=5
                )
                
                for op in wall.openings:
                    t = op.position_along_wall / max(0.01, wall.length.value)
                    op_x = sp[0] + t * (ep[0] - sp[0])
                    op_y = sp[1] + t * (ep[1] - sp[1])
                    ax.plot(op_x, op_y, marker="o", markersize=6, color="#0284C7", zorder=6)
                    
            # Room badge
            center_x = float(np.mean(poly_pts[:, 0]))
            center_y = float(np.mean(poly_pts[:, 1]))
            ax.text(
                center_x, center_y,
                f"{room.room_name.upper()}\n{room.floor_area.value:.1f} m²\nH: {room.ceiling_height.value:.2f}m",
                fontsize=9, fontweight="bold", color="#1E293B", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#94A3B8", linewidth=1),
                zorder=6
            )
            
        header = (
            f"Whole Property Floor Plan - {property_plan.property_id} ({property_plan.capture_tier.upper()} Tier)\n"
            f"Total Floor Area: {property_plan.total_floor_area.value:.1f} m² (95% CI: [{property_plan.total_floor_area.ci_lower:.1f}, {property_plan.total_floor_area.ci_upper:.1f}] m²)"
        )
        ax.set_title(header, fontsize=13, fontweight="bold", pad=15, color="#0F172A")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, linestyle=":", alpha=0.3)
        ax.autoscale_view()
        plt.tight_layout()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=self.output_dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Rendered whole-property floor plan saved to: {output_path}")
