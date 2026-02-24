#!/usr/bin/env python3
"""
STX Training Groups Generator - Using Actual VDOT Lookup Table
Based on Jack Daniels 3rd Edition (Coach's custom chart)
"""

import csv
import re
import os
from collections import defaultdict
from pathlib import Path
from html.parser import HTMLParser


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
# HTML Parser
# ============================================================================

class AthleteGroupParser(HTMLParser):
    """Parse existing HTML to extract athlete names and their groups."""
    
    def __init__(self):
        super().__init__()
        self.athletes = defaultdict(list)
        self.current_group = None
        self.in_group_header = False
        self.in_athlete_list = False
        self.in_list_item = False
        self.current_text = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'div' and attrs_dict.get('class') == 'group-header':
            self.in_group_header = True
            self.current_text = []
        elif tag == 'ul' and attrs_dict.get('class') == 'athlete-list':
            self.in_athlete_list = True
        elif tag == 'li' and self.in_athlete_list:
            self.in_list_item = True
            self.current_text = []
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_group_header:
            text = ''.join(self.current_text).strip()
            match = re.search(r'Group (\d+)', text)
            if match:
                self.current_group = int(match.group(1))
            self.in_group_header = False
        elif tag == 'li' and self.in_list_item:
            athlete_name = ''.join(self.current_text).strip()
            athlete_name = re.sub(r'\s*\(VDOT:.*?\)', '', athlete_name)
            if self.current_group is not None and athlete_name:
                self.athletes[self.current_group].append(athlete_name)
            self.in_list_item = False
        elif tag == 'ul' and self.in_athlete_list:
            self.in_athlete_list = False
    
    def handle_data(self, data):
        if self.in_group_header or self.in_list_item:
            self.current_text.append(data)


def parse_existing_html(html_path):
    """Parse existing HTML file to extract athletes and their groups."""
    if not Path(html_path).exists():
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    parser = AthleteGroupParser()
    parser.feed(html_content)
    return dict(parser.athletes)


# ============================================================================
# Data Processing
# ============================================================================

def read_roster(roster_path):
    """Read the roster.csv file and return set of athlete names."""
    roster_names = set()
    
    with open(roster_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'Athlete' in row and row['Athlete'].strip():
                roster_names.add(row['Athlete'].strip())
    
    return roster_names


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


def merge_with_existing(new_groups, existing_groups, athletes_with_data):
    """Merge new groups with existing manually-added athletes."""
    names_with_data = {a['name'] for a in athletes_with_data}
    
    athletes_without_data = []
    preserved_athletes = defaultdict(list)
    
    for group_num, athletes in existing_groups.items():
        for athlete_name in athletes:
            if athlete_name not in names_with_data:
                athletes_without_data.append((athlete_name, group_num))
                preserved_athletes[group_num].append(athlete_name)
    
    merged_groups = dict(new_groups)
    
    for group_num, athletes in preserved_athletes.items():
        if group_num not in merged_groups:
            merged_groups[group_num] = []
        for athlete_name in athletes:
            merged_groups[group_num].append({'name': athlete_name, 'manual': True})
    
    return merged_groups, athletes_without_data


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
        
        # Check if this is the Unassigned group (last group with only manual entries)
        is_unassigned = (group_num == sorted_groups[-1][0] and 
                        all(a.get('manual', False) for a in athletes))
        
        group_label = f"Group {group_num}"
        if is_unassigned:
            group_label = f"Group {group_num} - Unassigned"
        
        html += f"""        <div class="group-card">
            <div class="group-header">{group_label}</div>
            <ul class="athlete-list">
"""
        
        for athlete in athletes_sorted:
            name = athlete['name']
            is_manual = athlete.get('manual', False)
            vdot = athlete.get(vdot_field, None)
            
            if is_manual:
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
    OLD_HTML_PATH = script_dir / 'athlete_groups.html'
    OUTPUT_PATH = script_dir / 'athlete_groups.html'
    VDOT_CSV_PATH = script_dir / 'vdot_verification.csv'
    
    print("\n" + "=" * 70)
    print("STX TRAINING GROUPS GENERATOR")
    print("Using Jack Daniels 3rd Edition VDOT Table")
    print("=" * 70)
    
    # Load VDOT lookup table
    print("\n📊 Loading VDOT lookup table from your chart...")
    vdot_table = load_vdot_table(str(VDOT_TABLE_PATH))
    print(f"   ✓ Loaded {len(vdot_table['vdot_values'])} VDOT values")
    
    # Load roster
    print("\n📋 Loading roster...")
    roster_names = set()
    if ROSTER_PATH.exists():
        roster_names = read_roster(str(ROSTER_PATH))
        print(f"   ✓ Loaded {len(roster_names)} athletes from roster")
    else:
        print(f"   ⚠️  Roster.csv not found, skipping roster check")
    
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
    print(f"   Found {len(athletes)} athletes")
    
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
    
    # Parse existing HTML
    print(f"\n🔍 Checking for manually-added athletes...")
    existing_groups = parse_existing_html(str(OLD_HTML_PATH))
    
    # Assign groups
    print(f"\n👥 Creating groups (size: {group_size_min}-{group_size_max})...")
    new_groups = assign_groups(athletes, vdot_field, group_size_min, group_size_max)
    
    # Merge with existing
    merged_groups, athletes_without_data = merge_with_existing(new_groups, existing_groups, athletes)
    
    if athletes_without_data:
        print(f"\n⚠️  Preserved {len(athletes_without_data)} manually-added athletes:")
        for name, group in sorted(athletes_without_data):
            print(f"   Group {group}: {name}")
    
    # Check roster and create Unassigned group
    if roster_names:
        print(f"\n🔍 Checking roster for unassigned athletes...")
        
        # Collect all assigned athlete names
        assigned_names = set()
        for group_num, group_athletes in merged_groups.items():
            for athlete in group_athletes:
                assigned_names.add(athlete['name'])
        
        # Find unassigned athletes
        unassigned_names = roster_names - assigned_names
        
        if unassigned_names:
            print(f"   ⚠️  Found {len(unassigned_names)} unassigned athletes from roster")
            
            # Find the highest group number
            max_group = max(merged_groups.keys()) if merged_groups else 0
            unassigned_group_num = max_group + 1
            
            # Create Unassigned group
            merged_groups[unassigned_group_num] = []
            for name in sorted(unassigned_names):
                merged_groups[unassigned_group_num].append({
                    'name': name,
                    'manual': True
                })
                print(f"      - {name}")
        else:
            print(f"   ✓ All roster athletes accounted for in groups")
    
    # Generate HTML
    print(f"\n📝 Generating HTML with VDOT toggle...")
    generate_html(merged_groups, str(OUTPUT_PATH), vdot_field)
    
    # Summary
    print(f"\n" + "=" * 70)
    print("GROUP SUMMARY")
    print("=" * 70)
    for group_num in sorted(merged_groups.keys()):
        count = len(merged_groups[group_num])
        athletes_in_group = merged_groups[group_num]
        vdots = [a.get(vdot_field) for a in athletes_in_group if not a.get('manual') and a.get(vdot_field)]
        
        # Special label for unassigned group
        group_label = f"Group {group_num}"
        if all(a.get('manual') for a in athletes_in_group):
            # Check if this is the last group and has only manual entries
            if group_num == max(merged_groups.keys()) and not vdots:
                group_label = f"Group {group_num} (Unassigned)"
        
        if vdots:
            vdot_range = f"VDOT {max(vdots)}-{min(vdots)}"
        else:
            vdot_range = "Manual entries only"
        print(f"  {group_label}: {count} athletes ({vdot_range})")
    
    print(f"\n✅ Complete! Files saved:")
    print(f"   HTML: {OUTPUT_PATH}")
    print(f"   VDOT Verification CSV: {VDOT_CSV_PATH}")
    print(f"\n💡 TIP: Open HTML and click 'Show VDOT Values' to verify")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
