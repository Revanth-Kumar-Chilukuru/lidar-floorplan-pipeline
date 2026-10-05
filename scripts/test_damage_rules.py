"""
Author: Revanth Kumar Chilukuru
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.damage_engine import DamageAssessmentEngine, DamageRegion

def test_damage_engine():
    engine = DamageAssessmentEngine()
    
    # 1. Test wall_base rule triggering
    # Rule RULE-W-WATER-01 triggers on "wall_base" water_stain
    dmg_wall = DamageRegion(
        id="dmg_1",
        surface_type="wall",
        damage_class="water_stain",
        metric_extent={"area_m2": 0.5},
        confidence=0.9,
        severity="moderate"
    )
    
    dmg_wall_base = DamageRegion(
        id="dmg_2",
        surface_type="wall_base",
        damage_class="water_stain",
        metric_extent={"length_m": 2.0},
        confidence=0.9,
        severity="severe"
    )
    
    # Process
    flags = engine.evaluate_concealed_damage([dmg_wall, dmg_wall_base])
    
    # We expect dmg_2 (wall_base) to trigger RULE-BASE-WATER-03 or RULE-W-WATER-01
    wall_base_triggered = False
    for flag in flags:
        if flag.trigger_damage_id == "dmg_2" and flag.rule_id == "RULE-BASE-WATER-03":
            wall_base_triggered = True
            
    if wall_base_triggered:
        print("SUCCESS: wall_base damage correctly triggered concealed damage rule.")
    else:
        print("FAILURE: wall_base damage did not trigger expected rule.")
        sys.exit(1)

if __name__ == "__main__":
    test_damage_engine()
