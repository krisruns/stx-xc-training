#!/usr/bin/env python3
"""
Diagnostic: shows exactly what generate_workout_pace_mk9.py's
load_training_paces() sees for the Tempo columns (indices 10, 11, 12)
in your training_paces.csv.

Usage:
    python3 debug_tempo_paces.py [path/to/training_paces.csv]
"""

import sys
import pandas as pd

csv_path = sys.argv[1] if len(sys.argv) > 1 else 'training_paces.csv'

df = pd.read_csv(csv_path, skiprows=3)

print(f"Loaded {csv_path}")
print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

print("Raw values at columns 8-14 for the first 5 rows")
print("(expected: Aerobic, MP, Tempo400, Tempo1000, TempoMile, Pre30, Pre40)")
print("-" * 70)
for i in range(min(5, len(df))):
    row = df.iloc[i]
    vdot = row.iloc[0]
    vals = [row.iloc[c] for c in range(8, 15)]
    print(f"VDOT {vdot}: {vals}")

print()
print("If column 12 (TempoMile) does NOT look like a mm:ss time (e.g. 4:49),")
print("your CSV's column layout has shifted from what the script expects.")
print()

# Try the actual parsing logic used by load_training_paces for tempo_mile
print("Attempting to parse tempo_mile (column 12) for first 5 rows:")
print("-" * 70)
for i in range(min(5, len(df))):
    row = df.iloc[i]
    vdot = row.iloc[0]
    try:
        value = row.iloc[12]
        if pd.notna(value) and value != '-----':
            if isinstance(value, str) and ':' in value:
                parts = value.split(':')
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = int(value)
            print(f"VDOT {vdot}: raw={value!r} -> parsed {seconds} seconds")
        else:
            print(f"VDOT {vdot}: raw={value!r} -> SKIPPED (NaN or '-----')")
    except (IndexError, ValueError) as e:
        print(f"VDOT {vdot}: FAILED to parse -> {e}")
