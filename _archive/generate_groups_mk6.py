#!/usr/bin/env python3
"""
STX Training Groups Generator - Using Actual VDOT Lookup Table
Based on Jack Daniels 3rd Edition (Coach's custom chart)

REQUIRED FILES (all in same directory as script):
- training_paces.csv          : VDOT lookup table
- Athlete_Groups - Data.csv   : Performance data for athletes with times
- Roster.csv                  : Full team roster (optional but recommended)

OUTPUTS:
- athlete_groups.html         : Fresh training groups with VDOT toggle
- vdot_verification.csv       : VDOT calculations for verification

WORKFLOW:
1. Read performance data and calculate VDOTs using lookup table
2. Assign athletes to groups based on VDOT fitness levels (size: 4-8)
3. Check Roster.csv for any athletes not in performance data
4. Add unassigned athletes to final group labeled "Unassigned"
5. Generate fresh HTML file (no preservation of manual entries)

NOTE: This script generates groups fresh each time. All athletes must be in
either the performance data CSV or the roster CSV to be included.
"""

import csv
import re
import os
from collections import defaultdict
from pathlib import Path


# ============================================================================
# VDOT Lookup Table Functions
# ============================================================================

def parse_time_to_seconds(time_str):
    """Convert time string to seconds. Handles M:SS, MM:SS, H:MM:SS formats."""
    if not time_str or time_str.strip() == '' or time_str == '-----':
        return None
    
    time_str = time_str.strip()
    parts = time_str.split(':')
    
    try:
        if len(parts) == 3:  # H:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # M:SS or MM:SS
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:  # Just seconds
            return float(parts[0])
    except:
        return None


def load_vdot_table(csv_path):
    """
    Load VDOT lookup table from CSV.
    Returns dict with structure: {
        'vdot_to_times': {vdot: {'800m': seconds, '1600m': seconds, '3200m': seconds}},
        'vdot_values': [sorted list of VDOTs]
    }
    """
    vdot_table = {}
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    # Skip first 3 header rows, start from row with VDOTs
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('VDOT,') or ',VDOT,' in line:
            data_start = i + 1
            break
    
    # Parse data rows
    for line in lines[data_start:]:
        parts = line.strip().split(',')
        if len(parts) < 7:
            continue
        
        try:
            vdot = int(parts[0].strip())
            mile_time = parts[5].strip()  # Column 5: Mile
            time_800m = parts[6].strip()   # Column 6: 800m
            time_2mile = parts[3].strip()  # Column 3: 2 mile
            
            # Convert to seconds
            vdot_table[vdot] = {
                '800m': parse_time_to_seconds(time_800m),
                '1600m': parse_time_to_seconds(mile_time),
                '3200m': parse_time_to_seconds(time_2mile)
            }
        except:
            continue
    
    vdot_values = sorted(vdot_table.keys(), reverse=True)  # Highest to lowest
    
    return {
        'vdot_to_times': vdot_table,
        'vdot_values': vdot_values
    }


def find_closest_vdot(time_seconds, distance, vdot_table):
    """
    Find the VDOT that corresponds to the closest time in the table.
    
    Args:
        time_seconds: Athlete's time in seconds
        distance: '800m', '1600m', or '3200m'
        vdot_table: The loaded VDOT lookup table
    
    Returns:
        VDOT value (int) or None
    """
    if time_seconds is None:
        return None
    
    closest_vdot = None
    smallest_diff = float('inf')
    
    for vdot in vdot_table['vdot_values']:
        table_time = vdot_table['vdot_to_times'][vdot].get(distance)
        
        if table_time is None:
            continue
        
        diff = abs(table_time - time_seconds)
        
        if diff < smallest_diff:
            smallest_diff = diff
            closest_vdot = vdot
    
    return closest_vdot


# ============================================================================
# Data Processing
# ============================================================================

def read_roster(roster_path):
    """
    Read the roster.csv file and return set of athlete names.
    Handles both formats:
    - "Athlete" column with full name
    - "First" and "Last" separate columns (converts to "First Last")
    """
    roster_names = set()
    
    with open(roster_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check which format we have
            if 'First' in row and 'Last' in row:
                # Format: First, Last columns (convert to "First Last")
                first = row['First'].strip()
                last = row['Last'].strip()
                if first and last:
                    full_name = f"{first} {last}"
                    roster_names.add(full_name)
            elif 'Athlete' in row and row['Athlete'].strip():
                # Format: Athlete column (use as-is)
                roster_names.add(row['Athlete'].strip())
    
    return roster_names


def find_similar_names(name, name_list, threshold=0.8):
    """
    Find names in name_list that are similar to the given name.
    Uses simple similarity based on matching characters.
    """
    similar = []
    name_lower = name.lower()
    
    for candidate in name_list:
        candidate_lower = candidate.lower()
        
        # Check if names are very similar (ignoring case and minor differences)
        if name_lower == candidate_lower:
            continue  # Exact match, not a mismatch
        
        # Check for common issues: extra/missing letters, transpositions
        # Simple check: same last name?
        name_parts = name.split()
        candidate_parts = candidate.split()
        
        if len(name_parts) >= 2 and len(candidate_parts) >= 2:
            # Compare last names (assuming Last is the last word)
            if name_parts[-1].lower() == candidate_parts[-1].lower():
                # Same last name, different first name - might be a typo
                similar.append(candidate)
    
    return similar


def read_athlete_data(csv_path, vdot_table):
    """Read athlete performance data and calculate VDOTs using lookup table."""
    athletes = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            athlete = {
                'name': row['Athlete'].strip(),
                '800m': row.get('800M', '').strip(),
                '1600m': row.get('1600/Mile', '').strip(),
                '3200m': row.get('3200/2 Mile', '').strip(),
            }
            
            # Convert times to seconds
            time_800 = parse_time_to_seconds(athlete['800m'])
            time_1600 = parse_time_to_seconds(athlete['1600m'])
            time_3200 = parse_time_to_seconds(athlete['3200m'])
            
            # Look up VDOTs from table
            athlete['vdot_800'] = find_closest_vdot(time_800, '800m', vdot_table)
            athlete['vdot_1600'] = find_closest_vdot(time_1600, '1600m', vdot_table)
            athlete['vdot_3200'] = find_closest_vdot(time_3200, '3200m', vdot_table)
            
            # Calculate max VDOT
            vdots = [v for v in [athlete['vdot_800'], athlete['vdot_1600'], athlete['vdot_3200']] if v is not None]
            athlete['vdot_max'] = max(vdots) if vdots else None
            
            athletes.append(athlete)
    
    return athletes


def export_vdot_verification(athletes, output_path):
    """Export VDOT calculations to CSV for verification."""
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Athlete', '800M', 'VDOT_800', '1600/Mile', 'VDOT_1600', 
                     '3200/2Mile', 'VDOT_3200', 'VDOT_Max', 'Best_Event']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for athlete in sorted(athletes, key=lambda a: a.get('vdot_max') or 0, reverse=True):
            best_event = ''
            vdot_max = athlete['vdot_max']
            if vdot_max:
                if athlete['vdot_800'] == vdot_max:
                    best_event = '800m'
                elif athlete['vdot_1600'] == vdot_max:
                    best_event = '1600m'
                elif athlete['vdot_3200'] == vdot_max:
                    best_event = '3200m'
            
            writer.writerow({
                'Athlete': athlete['name'],
                '800M': athlete['800m'] or '',
                'VDOT_800': athlete['vdot_800'] or '',
                '1600/Mile': athlete['1600m'] or '',
                'VDOT_1600': athlete['vdot_1600'] or '',
                '3200/2Mile': athlete['3200m'] or '',
                'VDOT_3200': athlete['vdot_3200'] or '',
                'VDOT_Max': athlete['vdot_max'] or '',
                'Best_Event': best_event
            })
    
    print(f"✅ VDOT verification CSV created: {output_path}")


def assign_groups(athletes, vdot_field='vdot_max', group_size_min=4, group_size_max=8):
    """Assign athletes to groups based on VDOT."""
    valid_athletes = [a for a in athletes if a.get(vdot_field) is not None]
    valid_athletes.sort(key=lambda a: a[vdot_field], reverse=True)
    
    groups = defaultdict(list)
    current_group = 1
    
    for athlete in valid_athletes:
        groups[current_group].append(athlete)
        
        if len(groups[current_group]) >= group_size_max:
            current_group += 1
    
    # Merge last group if too small
    if len(groups[current_group]) < group_size_min and current_group > 1:
        groups[current_group - 1].extend(groups[current_group])
        del groups[current_group]
    
    return groups


def generate_html(groups, output_path, vdot_field='vdot_max'):
    """Generate HTML file with athlete groups including VDOT with toggle."""
    sorted_groups = sorted(groups.items())
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX Training Groups</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        
        h1 {
            text-align: center;
            color: #003366;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #003366;
        }
        
        .vdot-toggle-container {
            text-align: center;
            margin: 20px 0 30px 0;
            padding: 15px;
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
        }
        
        .vdot-toggle-btn {
            padding: 10px 20px;
            background: #003366;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .vdot-toggle-btn:hover {
            background: #004488;
            transform: translateY(-2px);
        }
        
        .vdot-info {
            margin-top: 10px;
            font-size: 0.9rem;
            color: #666;
        }
        
        .groups-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .group-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .group-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .group-header {
            font-size: 1.5em;
            font-weight: bold;
            color: #003366;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .athlete-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .athlete-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            color: #555;
        }
        
        .athlete-list li:last-child {
            border-bottom: none;
        }
        
        .athlete-list li:hover {
            color: #003366;
            background-color: #f8f8f8;
            padding-left: 5px;
            transition: all 0.2s;
        }
        
        .athlete-name {
            font-weight: 500;
        }
        
        .vdot-value {
            display: none;
            margin-left: 8px;
            padding: 2px 8px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .vdot-value.show {
            display: inline-block;
        }
        
        .manual-entry {
            font-style: italic;
            color: #888;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .groups-container {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.5em;
            }
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #777;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>St. Xavier Training Groups</h1>
    
    <div class="vdot-toggle-container">
        <button class="vdot-toggle-btn" onclick="toggleVDOT()">Show VDOT Values</button>
        <div class="vdot-info">
            Click to show/hide VDOT calculations for verification
        </div>
    </div>
    
    <div class="groups-container">
"""
    
    for group_num, athletes in sorted_groups:
        athletes_sorted = sorted(athletes, key=lambda a: a['name'])
        
        # Check if this is the Unassigned group
        is_unassigned = any(a.get('unassigned', False) for a in athletes)
        
        group_label = f"Group {group_num}"
        if is_unassigned:
            group_label = f"Group {group_num} - Unassigned"
        
        html += f"""        <div class="group-card">
            <div class="group-header">{group_label}</div>
            <ul class="athlete-list">
"""
        
        for athlete in athletes_sorted:
            name = athlete['name']
            vdot = athlete.get(vdot_field, None)
            is_unassigned = athlete.get('unassigned', False)
            
            if is_unassigned:
                # Unassigned athletes have no VDOT data
                html += f"""                <li class="manual-entry">
                    <span class="athlete-name">{name}</span>
                </li>
"""
            else:
                vdot_display = f'VDOT: {vdot}' if vdot else 'No VDOT'
                html += f"""                <li>
                    <span class="athlete-name">{name}</span>
                    <span class="vdot-value">{vdot_display}</span>
                </li>
"""
        
        html += """            </ul>
        </div>
"""
    
    html += """    </div>
    
    <div class="footer">
        St. Xavier High School Cross Country & Track
    </div>
    
    <script>
        function toggleVDOT() {
            const vdotElements = document.querySelectorAll('.vdot-value');
            const btn = document.querySelector('.vdot-toggle-btn');
            const isShowing = vdotElements[0].classList.contains('show');
            
            vdotElements.forEach(el => {
                el.classList.toggle('show');
            });
            
            btn.textContent = isShowing ? 'Show VDOT Values' : 'Hide VDOT Values';
        }
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ============================================================================
# Interactive Main
# ============================================================================

def main():
    """Interactive main function."""
    
    # Use current directory for all files
    script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    
    VDOT_TABLE_PATH = script_dir / 'training_paces.csv'
    CSV_PATH = script_dir / 'Athlete_Groups - Data.csv'
    ROSTER_PATH = script_dir / 'Roster.csv'
    OUTPUT_PATH = script_dir / 'athlete_groups.html'
    VDOT_CSV_PATH = script_dir / 'vdot_verification.csv'
    
    print("\n" + "=" * 70)
    print("STX TRAINING GROUPS GENERATOR")
    print("Using Jack Daniels 3rd Edition VDOT Table")
    print("=" * 70)
    
    # Show where script is looking for files
    print(f"\n📂 Script directory: {script_dir}")
    print(f"   Looking for files in: {script_dir.absolute()}")
    
    # Load VDOT lookup table
    print("\n📊 Loading VDOT lookup table from your chart...")
    vdot_table = load_vdot_table(str(VDOT_TABLE_PATH))
    print(f"   ✓ Loaded {len(vdot_table['vdot_values'])} VDOT values")
    
    # Load roster
    print("\n📋 Checking for Roster.csv...")
    print(f"   Looking for: {ROSTER_PATH.absolute()}")
    roster_names = set()
    
    # Check for the file
    if ROSTER_PATH.exists():
        roster_names = read_roster(str(ROSTER_PATH))
        print(f"   ✓ Loaded {len(roster_names)} athletes from roster")
    else:
        # Check for common variations
        found_variation = None
        variations = ['roster.csv', 'ROSTER.csv', 'Roster.CSV', 'roster.CSV']
        for var in variations:
            var_path = script_dir / var
            if var_path.exists():
                found_variation = var_path
                break
        
        if found_variation:
            print(f"   ⚠️  Found '{found_variation.name}' instead of 'Roster.csv'")
            print(f"   🔄 Using '{found_variation.name}'...")
            roster_names = read_roster(str(found_variation))
            print(f"   ✓ Loaded {len(roster_names)} athletes from roster")
        else:
            print(f"   ❌ Roster.csv not found at expected location")
            print(f"\n   Files in script directory:")
            try:
                csv_files = [item.name for item in sorted(script_dir.iterdir()) if item.is_file() and item.suffix.lower() == '.csv']
                if csv_files:
                    for f in csv_files:
                        print(f"      - {f}")
                else:
                    print(f"      No CSV files found")
            except Exception as e:
                print(f"      Could not list directory: {e}")
            print(f"\n   💡 Make sure Roster.csv is in: {script_dir.absolute()}")
            print(f"   💡 Check spelling/capitalization: 'Roster.csv' (capital R, lowercase .csv)")
    
    # Get group size preferences
    print("\n👥 Group Size Configuration")
    min_size = input("   Minimum athletes per group [default: 4]: ").strip()
    max_size = input("   Maximum athletes per group [default: 8]: ").strip()
    
    group_size_min = int(min_size) if min_size else 4
    group_size_max = int(max_size) if max_size else 8
    
    print(f"   ✓ Groups will have {group_size_min}-{group_size_max} athletes")
    
    # Prompt for VDOT choice
    print("\n🎯 Which race performance should determine VDOT for grouping?")
    print("  1. ALL    - Use highest VDOT across all events (default)")
    print("  2. 800    - Use 800m performance only")
    print("  3. 1600   - Use 1600m/mile performance only")
    print("  4. 3200   - Use 3200m/2-mile performance only")
    
    choice = input("\nEnter choice (1-4) [default: 1]: ").strip()
    
    vdot_choice_map = {
        '1': ('all', 'vdot_max'),
        '2': ('800', 'vdot_800'),
        '3': ('1600', 'vdot_1600'),
        '4': ('3200', 'vdot_3200'),
        '': ('all', 'vdot_max')
    }
    
    if choice not in vdot_choice_map:
        print("Invalid choice. Using default (ALL).")
        choice = '1'
    
    choice_name, vdot_field = vdot_choice_map[choice]
    
    print(f"\n✓ Using: {choice_name.upper()} performance for grouping")
    print("\n" + "=" * 70)
    
    # Process data
    print(f"\n📊 Reading athlete data...")
    athletes = read_athlete_data(str(CSV_PATH), vdot_table)
    print(f"   Found {len(athletes)} athletes with performance data")
    
    # Export VDOT verification CSV
    print(f"\n📋 Exporting VDOT calculations...")
    export_vdot_verification(athletes, str(VDOT_CSV_PATH))
    
    # Show top 10
    print(f"\n📈 Top 10 by {choice_name.upper()} VDOT:")
    sorted_athletes = sorted(athletes, key=lambda a: a.get(vdot_field) or 0, reverse=True)
    for i, athlete in enumerate(sorted_athletes[:10], 1):
        vdot = athlete.get(vdot_field)
        if vdot:
            # Show which time produced this VDOT
            time_info = ""
            if vdot_field == 'vdot_max':
                if athlete['vdot_800'] == vdot and athlete['800m']:
                    time_info = f"({athlete['800m']} 800m)"
                elif athlete['vdot_1600'] == vdot and athlete['1600m']:
                    time_info = f"({athlete['1600m']} 1600m)"
                elif athlete['vdot_3200'] == vdot and athlete['3200m']:
                    time_info = f"({athlete['3200m']} 3200m)"
            elif vdot_field == 'vdot_800' and athlete['800m']:
                time_info = f"({athlete['800m']})"
            elif vdot_field == 'vdot_1600' and athlete['1600m']:
                time_info = f"({athlete['1600m']})"
            elif vdot_field == 'vdot_3200' and athlete['3200m']:
                time_info = f"({athlete['3200m']})"
            
            print(f"   {i:2}. {athlete['name']:25} VDOT: {vdot:2} {time_info}")
    
    # Assign groups
    print(f"\n👥 Creating groups (size: {group_size_min}-{group_size_max})...")
    groups = assign_groups(athletes, vdot_field, group_size_min, group_size_max)
    
    # Check roster and create Unassigned group
    if roster_names:
        print(f"\n🔍 Checking roster for unassigned athletes...")
        
        # Collect all assigned athlete names
        assigned_names = set()
        for group_athletes in groups.values():
            for athlete in group_athletes:
                assigned_names.add(athlete['name'])
        
        # Find unassigned athletes (in roster but not in data file)
        unassigned_names = roster_names - assigned_names
        
        # Check for potential name mismatches (athletes in data but not exact match in roster)
        data_not_in_roster = assigned_names - roster_names
        
        if data_not_in_roster:
            print(f"\n   ⚠️  Warning: {len(data_not_in_roster)} athletes in data file don't exactly match roster:")
            for name in sorted(data_not_in_roster):
                similar = find_similar_names(name, roster_names)
                if similar:
                    print(f"      • '{name}' (data) — Did you mean '{similar[0]}' (roster)?")
                else:
                    print(f"      • '{name}' (not in roster)")
        
        if unassigned_names:
            print(f"\n   📋 Found {len(unassigned_names)} athletes in roster without performance data:")
            
            # Find the highest group number
            max_group = max(groups.keys()) if groups else 0
            unassigned_group_num = max_group + 1
            
            # Create Unassigned group
            groups[unassigned_group_num] = []
            for name in sorted(unassigned_names):
                groups[unassigned_group_num].append({
                    'name': name,
                    'unassigned': True
                })
                print(f"      - {name}")
        else:
            print(f"   ✓ All roster athletes have performance data and are assigned to groups")
    else:
        print(f"\n   ℹ️  No roster check performed (Roster.csv not found in script directory)")
    
    # Generate HTML
    print(f"\n📝 Generating HTML with VDOT toggle...")
    generate_html(groups, str(OUTPUT_PATH), vdot_field)
    
    # Summary
    print(f"\n" + "=" * 70)
    print("GROUP SUMMARY")
    print("=" * 70)
    for group_num in sorted(groups.keys()):
        count = len(groups[group_num])
        athletes_in_group = groups[group_num]
        vdots = [a.get(vdot_field) for a in athletes_in_group if not a.get('unassigned') and a.get(vdot_field)]
        
        # Check if this is the unassigned group
        is_unassigned = any(a.get('unassigned', False) for a in athletes_in_group)
        
        group_label = f"Group {group_num}"
        if is_unassigned:
            group_label = f"Group {group_num} (Unassigned)"
        
        if vdots:
            vdot_range = f"VDOT {max(vdots)}-{min(vdots)}"
        else:
            vdot_range = "No data available" if is_unassigned else "No VDOT data"
        print(f"  {group_label}: {count} athletes ({vdot_range})")
    
    print(f"\n✅ Complete! Files saved:")
    print(f"   HTML: {OUTPUT_PATH}")
    print(f"   VDOT Verification CSV: {VDOT_CSV_PATH}")
    print(f"\n💡 TIP: Open HTML and click 'Show VDOT Values' to verify")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
