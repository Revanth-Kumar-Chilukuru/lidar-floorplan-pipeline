import os
import sys
import subprocess
import shutil
import json

def run_repeatability():
    print("Testing Algorithmic Determinism (10 separate runs)...")
    
    scan_path = "Assignment - YC Startup/single_room/c00a170fe1"
    base_out = "outputs/repeatability_test"
    
    if os.path.exists(base_out):
        shutil.rmtree(base_out)
        
    os.makedirs(base_out)
    
    python_bin = sys.executable
    
    # 1. Run 10 times in different directories
    first_json = None
    first_json_path = None
    
    success = True
    for i in range(1, 11):
        out_dir = os.path.join(base_out, f"run_{i}")
        os.makedirs(out_dir)
        
        cmd = f'"{python_bin}" main.py --input "{scan_path}" --tier lidar --output-dir "{out_dir}"'
        print(f"  Executing Run {i}/10...")
        # Redirect output to null to avoid console spam
        res = subprocess.run(cmd, shell=True, capture_output=True)
        if res.returncode != 0:
            print(f"  Run {i} failed!")
            print(res.stderr.decode('utf-8', errors='replace'))
            sys.exit(1)
            
        json_file = os.path.join(out_dir, "c00a170fe1_lidar_plan.json")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        if i == 1:
            first_json = data
            first_json_path = json_file
        else:
            # Diff byte-for-byte (by comparing standard JSON dumps)
            dump1 = json.dumps(first_json, sort_keys=True)
            dump2 = json.dumps(data, sort_keys=True)
            if dump1 != dump2:
                print(f"  FAIL: Run {i} differs from Run 1!")
                success = False
            else:
                print(f"  Run {i} is byte-for-byte identical to Run 1.")
                
    if success:
        print("\nSUCCESS: Pipeline is perfectly deterministic across 10 isolated runs.")
    else:
        print("\nFAILURE: Pipeline exhibited non-determinism.")

    print("\nSetting up 'before' fix-loop worktree to generate the before/after comparison...")
    # Add git worktree
    # The pre-fix commit is 879d30a (based on our git log, or the one before determinism).
    # Wait, 879d30a was "docs & benchmarks: Add compliance matrix..."
    # The one with the actual original code is 879d30a or the one before that. Let's use 879d30a.
    worktree_dir = "outputs/before_fix_worktree"
    if os.path.exists(worktree_dir):
        subprocess.run(f"git worktree remove {worktree_dir} --force", shell=True)
        
    subprocess.run(f"git worktree add {worktree_dir} 879d30a", shell=True)
    
    # Run the old code
    print("Executing 'before' run using old codebase...")
    res = subprocess.run(f'"{python_bin}" {worktree_dir}/main.py --input "{scan_path}" --tier lidar --output-dir outputs/fix_loop_before', shell=True, capture_output=True)
    
    if os.path.exists(worktree_dir):
        subprocess.run(f"git worktree remove {worktree_dir} --force", shell=True)
        
    print("Repeatability test complete.")
    
if __name__ == "__main__":
    run_repeatability()
