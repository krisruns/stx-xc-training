#!/usr/bin/env python3
"""
Generate workout-specific pace pages from athlete_groups.html template.
MK3 - Enhanced workout parsing + PRINT FUNCTIONALITY
"""

import pandas as pd
import re
from pathlib import Path
from bs4 import BeautifulSoup
import sys
import copy
from workout_pace_generator import WorkoutPacePageGenerator


# ============================================================================
# PACE DATA LOADING
# ============================================================================

def load_training_paces(csv_path='training_paces.csv'):
    """
    Load the training paces CSV and create a lookup dictionary.
    
    Returns:
        dict: {VDOT: {'200m_mile': seconds, '400m_5k': seconds, ...}}
    """
    # Read CSV, skipping the first 3 header rows
    df = pd.read_csv(csv_path, skiprows=3)
    
    # Column mapping based on the CSV structure
    pace_columns = {
        # Tempo paces
        'tempo_400': 10,
        'tempo_1000': 11,
        'tempo_mile': 12,
        
        # Pre 30/40 paces
        'pre_200': 13,
        
        # ========================================
        # 3K Pace - ADD YOUR COLUMN NUMBERS HERE
        # ========================================
        # Step 1: Run python3 inspect_paces.py
        # Step 2: Find columns with "3K" in the header
        # Step 3: Replace XX with actual column numbers
        # Step 4: Comment out any distances you don't have
        
        
        # ========================================
        
        # CV Pace (10k pace)
        'cv_400': 17,
        'cv_800': 18,
        'cv_1000': 19,
        'cv_1200': 20,
        
        # 5K Pace (Interval pace)
        '5k_400': 21,
        '5k_1000': 22,
        '5k_1200': 23,
        '5k_mile': 24,
        
        # 3k Pace - REPLACE XX with actual column numbers
        '3k_400': 25,    # ← REPLACE XX with column number for 3K 400m
        '3k_600': 26,    # ← REPLACE XX with column number for 3K 600m
        '3k_800': 27,    # ← REPLACE XX with column number for 3K 800m
        '3k_1000': 28,   # ← REPLACE XX with column number for 3K 1000m

        # Mile Pace
        'mile_200': 29,
        'mile_300': 30,
        'mile_400': 31,
        'mile_600': 32,
        'mile_800': 33,
        
        # 800 Pace
        '800_200': 34,
        '800_300': 35,
        '800_400': 36,
        
        # 400 Pace
        '400_100': 37,
        '400_150': 38,
        '400_200': 39,
    }
    
    # ... rest of function stays the same ...

    
    # Create VDOT lookup dictionary
    vdot_paces = {}
    
    for idx, row in df.iterrows():
        vdot = int(row.iloc[0])  # First column is VDOT
        
        pace_dict = {}
        for pace_key, col_idx in pace_columns.items():
            try:
                value = row.iloc[col_idx]
                # Convert to seconds
                if pd.notna(value) and value != '-----':
                    if isinstance(value, str) and ':' in value:
                        parts = value.split(':')
                        seconds = int(parts[0]) * 60 + int(parts[1])
                    else:
                        seconds = int(value)
                    pace_dict[pace_key] = seconds
            except (IndexError, ValueError):
                pass
        
        vdot_paces[vdot] = pace_dict
    
    return vdot_paces

# ============================================================================
# WORKOUT PARSING - MK3 ENHANCED VERSION
# ============================================================================

def parse_workout_description(description):
    """
    Parse workout description to extract pace requirements.
    Enhanced to handle bracketed repetitions.
    
    Examples:
        "2x200@mile (200j)" -> [('200', 'mile')]
        "12x400@5k(200j)" -> [('400', '5k')]
        "2x200@mile (200j) + 12x400@5k(200j)+ 2x200@800 (60s)" 
            -> [('200', 'mile'), ('400', '5k'), ('200', '800')]
        "3x[600@3k (2:00) + 400@mile (2:00) + 200@800 (1:00)]"
            -> [('600', '3k'), ('400', 'mile'), ('200', '800')]
    
    Returns:
        list of tuples: [(distance, pace_type), ...]
    """
    if not description or pd.isna(description):
        return []
    
    pace_needs = []
    
    # First, check for bracketed repetitions: 3x[600@3k + 400@mile + 200@800]
    # Pattern: [number]x[...contents...]
    bracket_pattern = r'(\d+)x\[(.*?)\]'
    bracket_matches = re.findall(bracket_pattern, description.lower())
    
    # Process bracketed content
    for reps, bracketed_content in bracket_matches:
        # Parse all pace patterns inside the brackets
        inner_pattern = r'(\d+)(?:m)?@([\w\d]+)'
        inner_matches = re.findall(inner_pattern, bracketed_content)
        for distance, pace_type in inner_matches:
            pace_needs.append((distance, pace_type))
    
    # Then, look for non-bracketed patterns: [number]x[distance]@[pace_type]
    # But exclude anything that's inside brackets (already processed)
    # Remove bracketed sections first
    desc_without_brackets = re.sub(r'\d+x\[.*?\]', '', description.lower())
    
    # Pattern: [number]x[distance]@[pace_type]
    pattern = r'(\d+)x(\d+)(?:m)?@([\w\d]+)'
    matches = re.findall(pattern, desc_without_brackets)
    
    for match in matches:
        reps, distance, pace_type = match
        pace_needs.append((distance, pace_type))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paces = []
    for item in pace_needs:
        if item not in seen:
            seen.add(item)
            unique_paces.append(item)
    
    return unique_paces


def extract_groups_from_html(html_content):
    """
    Extract group data from athlete_groups.html for use with the generator.
    
    Returns:
        List of group dictionaries compatible with WorkoutPacePageGenerator
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    groups = []
    
    # Find all group cards
    group_cards = soup.find_all('div', class_='group-card')
    
    for card in group_cards:
        # Get group name
        header = card.find('div', class_='group-header')
        if not header:
            continue
        
        group_name = header.get_text().strip()
        
        # Extract athletes with VDOTs
        athletes = []
        athlete_items = card.find_all('li')
        
        for item in athlete_items:
            name_span = item.find('span', class_='athlete-name')
            if not name_span:
                continue
            
            athlete_name = name_span.get_text().strip()
            
            # Get VDOT if available
            vdot_span = item.find('span', class_='vdot-value')
            vdot = None
            if vdot_span:
                vdot_text = vdot_span.get_text()
                vdot_match = re.search(r'VDOT[\s:]+(\d+)', vdot_text)
                if vdot_match:
                    vdot = int(vdot_match.group(1))
            
            athletes.append({
                'name': athlete_name,
                'vdot': vdot
            })
        
        # We'll add paces later based on VDOT ranges
        groups.append({
            'name': group_name,
            'athletes': athletes,
            'paces': {}  # Will be filled in
        })
    
    return groups


def get_pace_range_for_group(vdot_paces, athletes, distance, pace_type):
    """
    Get the pace range for a group based on their athletes' VDOTs.
    
    Args:
        vdot_paces: Dictionary from load_training_paces()
        athletes: List of athlete dicts with 'vdot' field
        distance: "200", "400", "800", etc.
        pace_type: "mile", "5k", "800", "400", "tempo", etc.
    
    Returns:
        (min_seconds, max_seconds) or None if not found
    """
    # Get VDOTs from athletes
    vdots = [a['vdot'] for a in athletes if a['vdot'] is not None]
    
    if not vdots:
        return None
    
    min_vdot = min(vdots)
    max_vdot = max(vdots)
    
    # Normalize pace type aliases
    pace_aliases = {
        'i': '5k',
        'interval': '5k',
        'rp': '5k',
        't': 'tempo',
        'threshold': 'tempo',
        'r': '400',
        'rep': '400',
        'm': 'mile',
        '3k': '3k',
        '10k': 'cv',
    }
    
    normalized_pace = pace_aliases.get(pace_type.lower(), pace_type.lower())
    lookup_key = f"{normalized_pace}_{distance}"
    
    try:
        available_vdots = sorted(vdot_paces.keys(), reverse=True)
        
        # Find closest VDOTs
        vdot_high = min([v for v in available_vdots if v >= max_vdot], default=max(available_vdots))
        vdot_low = max([v for v in available_vdots if v <= min_vdot], default=min(available_vdots))
        
        # Higher VDOT = faster = lower time
        pace_fast = vdot_paces[vdot_high].get(lookup_key)
        pace_slow = vdot_paces[vdot_low].get(lookup_key)
        
        if pace_fast and pace_slow:
            return (pace_fast, pace_slow)
        elif pace_fast:
            return (pace_fast, pace_fast)
        elif pace_slow:
            return (pace_slow, pace_slow)
        else:
            return None
            
    except (KeyError, ValueError):
        return None


def format_time(seconds):
    """Convert seconds to display format."""
    if seconds >= 60:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    else:
        return f"{seconds}s"


def add_paces_to_groups(groups, pace_needs, vdot_paces):
    """
    Add workout-specific paces to each group based on their VDOT ranges.
    
    Modifies groups in-place to add the 'paces' dictionary.
    """
    for group in groups:
        for distance, pace_type in pace_needs:
            pace_range = get_pace_range_for_group(
                vdot_paces, 
                group['athletes'], 
                distance, 
                pace_type
            )
            
            # Create pace label
            pace_label = f"{distance}m @ {pace_type.upper()}"
            
            if pace_range:
                min_time, max_time = pace_range
                if min_time == max_time:
                    group['paces'][pace_label] = format_time(min_time)
                else:
                    group['paces'][pace_label] = f"{format_time(min_time)}-{format_time(max_time)}"
            else:
                group['paces'][pace_label] = "N/A"


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_training_overview(overview_csv, paces_csv, athlete_groups_html, output_dir='output'):
    """
    Read Training Overview CSV and generate workout pace pages with PRINT FUNCTIONALITY.
    MK3 - Enhanced parsing + print buttons
    """
    # Initialize the generator with print functionality
    generator = WorkoutPacePageGenerator()
    
    # Load pace data
    print("Loading training paces...")
    vdot_paces = load_training_paces(paces_csv)
    print(f"✓ Loaded paces for {len(vdot_paces)} VDOT levels")
    
    # Load athlete groups HTML template
    print(f"\nReading athlete groups template: {athlete_groups_html}")
    with open(athlete_groups_html, 'r') as f:
        athlete_html = f.read()
    print("✓ Loaded athlete groups template")
    
    # Extract groups from HTML
    print("Extracting group structure...")
    base_groups = extract_groups_from_html(athlete_html)
    print(f"✓ Found {len(base_groups)} groups")
    
    # Load training overview
    print(f"\nReading training overview: {overview_csv}")
    df = pd.read_csv(overview_csv)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    generated_files = []
    
    # Process each row
    for idx, row in df.iterrows():
        week = row['Week']
        squad = row.iloc[0]  # V or JV
        
        # Process each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days:
            workout_desc = row[day]
            
            if pd.isna(workout_desc) or workout_desc.strip() == '':
                continue
            
            # Parse what paces are needed (MK3 enhanced parsing)
            pace_needs = parse_workout_description(workout_desc)
            
            if not pace_needs:
                continue
            
            # Make a copy of groups and add workout-specific paces
            groups = copy.deepcopy(base_groups)
            add_paces_to_groups(groups, pace_needs, vdot_paces)
            
            # Generate unique filename
            workout_name = f"{day.lower()[:3]}_week{week}"
            if squad and not pd.isna(squad):
                workout_name = f"{squad.lower()}_{workout_name}"
            
            # Generate HTML with PRINT FUNCTIONALITY using the new generator
            html = generator.generate_page(
                workout_description=workout_desc,
                groups=groups,
                squad_type=squad if not pd.isna(squad) else None,
                week_number=int(week) if not pd.isna(week) else None,
                day=day
            )
            
            # Save file
            output_file = output_path / f"workout-groups_{workout_name}.html"
            with open(output_file, 'w') as f:
                f.write(html)
            
            generated_files.append(output_file.name)
            
            pace_summary = ', '.join([f'{d}m@{p}' for d, p in pace_needs])
            print(f"  ✓ {output_file.name:40s} [{pace_summary}] + PRINT")
    
    print(f"\n✓ Generated {len(generated_files)} workout pace pages in {output_dir}/")
    print("  🖨️  Each page includes printable group record sheets!")
    return generated_files

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate workout-specific pace pages with PRINTABLE GROUP SHEETS (MK3 Enhanced)'
    )
    parser.add_argument(
        'overview_csv',
        nargs='?',
        default='Training Master - Training_Overview.csv',
        help='Path to training overview CSV (default: Training Master - Training_Overview.csv)'
    )
    parser.add_argument(
        '--paces',
        default='training_paces.csv',
        help='Path to training paces CSV'
    )
    parser.add_argument(
        '--template',
        default='athlete_groups.html',
        help='Path to athlete_groups.html template'
    )
    parser.add_argument(
        '--output',
        default='pace_pages',
        help='Output directory (default: pace_pages)'
    )
    
    args = parser.parse_args()
    
    try:
        generated = process_training_overview(
            args.overview_csv,
            args.paces,
            args.template,
            args.output
        )
        print("\n✅ Success! All workout pace pages generated with print functionality.")
        print("\n📋 MK3 Features:")
        print("   • Enhanced workout parsing (handles bracketed patterns)")
        print("   • Printable group record sheets")
        print("   • Professional print layout with proper page breaks")
        print("\n💡 To use:")
        print("   1. Open any workout pace page in a browser")
        print("   2. Click the 'Print Group Record Sheets' button")
        print("   3. Save as PDF or print for practice")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the following files exist:")
        print(f"  - {args.overview_csv}")
        print(f"  - {args.paces}")
        print(f"  - {args.template}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
