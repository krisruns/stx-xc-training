#!/usr/bin/env python3
"""
Inspect training_paces.csv to identify column structure
This will help us find where the 3K pace data is
"""

import pandas as pd

# Read the CSV (first few rows to see structure)
print("=" * 70)
print("TRAINING PACES CSV STRUCTURE")
print("=" * 70)

# Read with header rows
df_with_headers = pd.read_csv('training_paces.csv', nrows=10)
print("\nFirst 3 header rows:")
for i in range(min(3, len(df_with_headers))):
    print(f"Row {i}: {df_with_headers.iloc[i].tolist()}")

# Read as actual data (skipping 3 header rows)
df = pd.read_csv('training_paces.csv', skiprows=3, nrows=5)

print("\n" + "=" * 70)
print("COLUMN MAPPING (0-indexed)")
print("=" * 70)

for idx, col in enumerate(df.columns):
    sample_value = df.iloc[0, idx] if len(df) > 0 else "N/A"
    print(f"Column {idx:2d}: {col:30s} | Sample: {sample_value}")

print("\n" + "=" * 70)
print("CURRENT PACE COLUMN MAPPING IN SCRIPT")
print("=" * 70)

current_mapping = {
    'tempo_400': 10,
    'tempo_1000': 11,
    'tempo_mile': 12,
    'pre_200': 13,
    'cv_400': 17,      # CV = 10k pace
    'cv_800': 18,
    'cv_1000': 19,
    'cv_1200': 20,
    '5k_400': 21,
    '5k_1000': 22,
    '5k_1200': 23,
    '5k_mile': 24,
    'mile_200': 25,
    'mile_300': 26,
    'mile_400': 27,
    'mile_600': 28,
    'mile_800': 29,
    '800_200': 30,
    '800_300': 31,
    '800_400': 32,
    '400_100': 33,
    '400_150': 34,
    '400_200': 35,
}

print("\nCurrently loading these columns:")
for pace_name, col_idx in sorted(current_mapping.items(), key=lambda x: x[1]):
    try:
        col_name = df.columns[col_idx]
        print(f"  {pace_name:15s} <- Column {col_idx:2d} ({col_name})")
    except:
        print(f"  {pace_name:15s} <- Column {col_idx:2d} (OUT OF RANGE)")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)
print("\n1. Look at the column list above")
print("2. Find columns that contain 3K pace data")
print("   (Look for headers like '3K 400', '3K 600', '3K 800', etc.)")
print("3. Add those column numbers to the pace_columns dictionary")
print("\nExample: If '3K 600m' is in column 15, add:")
print("  '3k_600': 15,")
