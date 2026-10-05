from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ConfidenceInterval(BaseModel):
    """Calibrated confidence interval representing measurement uncertainty."""
    value: Optional[float] = Field(None, description="Estimated nominal measurement value. None if unmeasured.")
    ci_lower: Optional[float] = Field(None, description="Lower bound of 95% confidence interval")
    ci_upper: Optional[float] = Field(None, description="Upper bound of 95% confidence interval")
    unit: str = Field("m", description="Unit of measurement (m, m2, deg)")
    is_prior: bool = Field(False, description="True if value is an unmeasured prior/default.")

class Opening(BaseModel):
    """An opening such as a door, open entryway, or window in a wall."""
    id: str = Field(..., description="Unique opening identifier")
    type: str = Field(..., description="Type: 'door', 'window', 'cased_opening'")
    wall_id: str = Field(..., description="ID of the wall containing this opening")
    width: ConfidenceInterval = Field(..., description="Opening width in meters")
    height: Optional[ConfidenceInterval] = Field(None, description="Opening height in meters")
    sill_height: Optional[float] = Field(0.0, description="Height from floor to bottom of opening (m)")
    position_along_wall: float = Field(..., description="Offset in meters from start of wall")

class Wall(BaseModel):
    """A wall bounding a room."""
    id: str = Field(..., description="Unique wall identifier")
    start_point: List[float] = Field(..., description="2D [x, y] coordinates in room frame (meters)")
    end_point: List[float] = Field(..., description="2D [x, y] coordinates in room frame (meters)")
    length: ConfidenceInterval = Field(..., description="Wall length in meters with confidence")
    height: ConfidenceInterval = Field(..., description="Wall height in meters")
    openings: List[Opening] = Field(default_factory=list, description="Openings in this wall")
    adjacent_room_id: Optional[str] = Field(None, description="Adjacent room if shared wall")

class DamageRegion(BaseModel):
    """Surface damage identified on a room boundary or finish."""
    id: str = Field(..., description="Damage identification tag")
    surface_type: str = Field(..., description="'wall', 'ceiling', 'floor'")
    surface_id: Optional[str] = Field(None, description="ID of wall or surface element")
    damage_class: str = Field(..., description="Classification: 'water_stain', 'drywall_crack', 'peeling_paint', 'mold'")
    metric_extent: Dict[str, float] = Field(..., description="Metric dimensions: length_m, height_m, or area_m2")
    confidence: float = Field(..., description="Detection confidence score [0.0 - 1.0]")
    severity: str = Field("moderate", description="'low', 'moderate', 'severe'")
    bounding_box_2d: Optional[List[float]] = Field(None, description="Bounding coordinates [x_min, y_min, x_max, y_max]")

class ConcealedDamageFlag(BaseModel):
    """Rule-based inference of concealed damage behind visible surfaces."""
    rule_id: str = Field(..., description="Unique rule code (e.g. 'RULE-CEIL-WATER-01')")
    rule_name: str = Field(..., description="Human readable rule description")
    trigger_damage_id: str = Field(..., description="ID of the surface damage that triggered this rule")
    surface_id: Optional[str] = Field(None, description="Surface where concealed damage is suspected")
    suspected_cause: str = Field(..., description="Underlying hidden problem (e.g. roof leak, pipe corrosion)")
    recommended_action: str = Field(..., description="Action required (e.g. moisture probe, drywall removal)")
    urgency: str = Field("medium", description="'low', 'medium', 'high', 'immediate'")

class ScopeLineItem(BaseModel):
    """Insurance/repair scope of work line item keyed to a surface."""
    item_id: str = Field(..., description="Line item ID")
    category: str = Field(..., description="Trade category: 'drywall', 'painting', 'plumbing', 'flooring'")
    description: str = Field(..., description="Actionable repair scope description")
    surface_id: Optional[str] = Field(None, description="Keyed surface identifier")
    quantity: float = Field(..., description="Quantity of material or repair")
    unit: str = Field("sq_m", description="Unit: 'sq_m', 'linear_m', 'each'")
    estimated_cost_tier: str = Field("standard", description="'minor', 'standard', 'major'")

class RoomPlan(BaseModel):
    """Dimensioned geometric plan of a single room."""
    room_id: str = Field(..., description="Room identifier")
    room_name: str = Field("Room", description="Classified room type: 'living_room', 'bedroom', etc.")
    ceiling_height: ConfidenceInterval = Field(..., description="Ceiling height with confidence interval")
    floor_area: ConfidenceInterval = Field(..., description="Total floor area with confidence interval")
    perimeter: float = Field(..., description="Total perimeter in meters")
    polygon_vertices: List[List[float]] = Field(..., description="Ordered 2D polygon vertices [[x1, y1], [x2, y2], ...]")
    walls: List[Wall] = Field(..., description="Wall segments defining the perimeter")
    damage_regions: List[DamageRegion] = Field(default_factory=list, description="Surface damages in this room")

class WholePropertyPlan(BaseModel):
    """Complete multi-room property plan with adjacency, damage, and scope."""
    property_id: str = Field(..., description="Property scan identifier")
    capture_tier: str = Field(..., description="'lidar', 'video', 'photos'")
    timestamp: str = Field(..., description="Capture/processing timestamp")
    total_floor_area: ConfidenceInterval = Field(..., description="Total enclosed floor area")
    rooms: List[RoomPlan] = Field(..., description="Dimensioned rooms")
    room_adjacencies: List[Dict[str, Any]] = Field(default_factory=list, description="Topological connections between rooms")
    concealed_damage_flags: List[ConcealedDamageFlag] = Field(default_factory=list, description="Concealed damage flags across property")
    scope_of_work: List[ScopeLineItem] = Field(default_factory=list, description="Comprehensive repair line items")
    drift_metrics: Dict[str, Any] = Field(default_factory=dict, description="Drift and loop closure metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Device, resolution, frame count, runtime")
