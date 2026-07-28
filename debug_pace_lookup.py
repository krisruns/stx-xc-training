#!/usr/bin/env python3
"""
Traces the tempo-pace lookup through your ACTUAL generate_workout_pace_mk9.py
to find exactly where it drops to None/N-A.

Usage (run from the folder containing all your files):
    python3 debug_pace_lookup.py
    # or specify paths explicitly:
    python3 debug_pace_lookup.py generate_workout_pace_mk9.py training_paces.csv athlete_groups.html
"""

import sys
import types
import copy
import importlib.util

script_path = sys.argv[1] if len(sys.argv) > 1 else 'generate_workout_pace_mk9.py'
paces_csv = sys.argv[2] if len(sys.argv) > 2 else 'training_paces.csv'
groups_html = sys.argv[3] if len(sys.argv) > 3 else 'athlete_groups.html'

# Stub out workout_pace_generator so we can import the target script even if
# that file / its dependencies aren't on this machine's path right now.
stub = types.ModuleType("workout_pace_generator")
class _StubGenerator:
    def generate_page(self, **kwargs):
        return ""
stub.WorkoutPacePageGenerator = _StubGenerator
sys.modules["workout_pace_generator"] = stub

spec = importlib.util.spec_from_file_location("target_script", script_path)
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)
print(f"✓ Imported {script_path}\n")

# Step 1: load pace table
vdot_paces = gw.load_training_paces(paces_csv)
print(f"✓ Loaded pace table for {len(vdot_paces)} VDOT levels")
for v in (65, 62, 61, 60, 59):
    print(f"    VDOT {v}: tempo_mile = {vdot_paces.get(v, {}).get('tempo_mile')!r}")
print()

# Step 2: extract groups from athlete_groups.html
with open(groups_html) as f:
    html = f.read()
groups = gw.extract_groups_from_html(html)
print(f"✓ Extracted {len(groups)} groups from {groups_html}")
g1 = groups[0]
print(f"    Group 1 athletes: {g1['athletes']}\n")

# Step 3: call get_pace_range_for_group directly for tempo/mile
result = gw.get_pace_range_for_group(vdot_paces, g1['athletes'], 'mile', 't')
print(f"✓ get_pace_range_for_group(vdot_paces, group1_athletes, 'mile', 't') -> {result}\n")

# Step 4: parse the real workout description
desc = "2mi@T - (2:00) - 1mi@T + 4-6x200m@R"
pace_needs = gw.parse_workout_description(desc)
print(f"✓ parse_workout_description({desc!r}) -> {pace_needs}\n")

# Step 5: run add_paces_to_groups exactly like the real pipeline does
groups_copy = copy.deepcopy(groups)
gw.add_paces_to_groups(groups_copy, pace_needs, vdot_paces)
print(f"✓ add_paces_to_groups result for Group 1: {groups_copy[0]['paces']}")
