#!/usr/bin/env python3
"""
Prints the real source code of get_pace_range_for_group (and a couple of
related helpers) from your script, so we can see exactly what logic is
running -- no guessing.

Usage:
    python3 print_pace_func.py generate_workout_pace_mk10.py
"""

import sys
import types
import inspect
import importlib.util

script_path = sys.argv[1] if len(sys.argv) > 1 else 'generate_workout_pace_mk10.py'

stub = types.ModuleType("workout_pace_generator")
class _StubGenerator:
    def generate_page(self, **kwargs):
        return ""
stub.WorkoutPacePageGenerator = _StubGenerator
sys.modules["workout_pace_generator"] = stub

spec = importlib.util.spec_from_file_location("target_script", script_path)
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)

for fn_name in ["get_pace_range_for_group", "add_paces_to_groups", "load_training_paces"]:
    fn = getattr(gw, fn_name, None)
    print("=" * 70)
    print(fn_name)
    print("=" * 70)
    if fn is None:
        print("  (not found in this module)")
    else:
        print(inspect.getsource(fn))
    print()
